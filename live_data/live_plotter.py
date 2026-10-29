"""Standalone live display; this module does not start a market-data feed."""

from collections import deque
from datetime import datetime, timezone
from math import isfinite
from queue import Empty, Full, Queue
import threading
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg

if TYPE_CHECKING:
    from live_book import bookObvservation


class LivePlotter(QtWidgets.QMainWindow):
    """Display observations from ``liveBook.get_observation()``.

    Construct and call start/refresh/close on the main thread. ``submit`` is
    safe to call from a worker thread. No GUI or feed starts on import.
    History is limited by both elapsed observation time and point count.
    Under overload, the oldest pending observations are dropped for display.
    This queue must not be used as the input to a volatility calculator.

    Usage on the main thread::

        plotter = LivePlotter(title="BTC-USD")
        plotter.submit(book.get_observation(timestamp))
        plotter.start()

    A producer may continue calling submit while start runs the Qt event loop.
    """

    closed = QtCore.Signal()
    BID_COLOUR = "#34d399"
    ASK_COLOUR = "#fb7185"
    MID_COLOUR = "#60a5fa"

    def __init__(
        self,
        title: str = "Live order book",
        window_seconds: float = 300,
        refresh_ms: int = 100,
        max_points: int = 20_000,
        price_label: str = "Price",
    ):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("Create LivePlotter on the main thread")
        if not isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("window_seconds must be finite and positive")
        if refresh_ms < 1 or max_points < 2:
            raise ValueError("refresh_ms must be positive and max_points at least 2")

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        super().__init__()
        self._app = app
        self._closed = False
        self.window_seconds = window_seconds
        self._pending: Queue = Queue(maxsize=max_points)
        # Each item is (Unix timestamp, bid, ask, midprice).
        self._history = deque(maxlen=max_points)
        self.setWindowTitle(title)
        self.resize(1100, 650)

        container = QtWidgets.QWidget()
        container.setStyleSheet(
            "background: #101827; color: #e2e8f0; font-size: 13px;"
        )
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        self.setCentralWidget(container)

        toolbar = QtWidgets.QHBoxLayout()
        self.readout = QtWidgets.QLabel("Waiting for a book observation…")
        self.readout.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        toolbar.addWidget(self.readout, stretch=1)
        self.follow_latest = QtWidgets.QCheckBox("Follow latest")
        self.follow_latest.setChecked(True)
        toolbar.addWidget(self.follow_latest)
        layout.addLayout(toolbar)

        self.chart = pg.GraphicsLayoutWidget()
        self.chart.setBackground("#101827")
        layout.addWidget(self.chart)
        self.price_plot = self.chart.addPlot(
            axisItems={"bottom": pg.DateAxisItem(utcOffset=0)},
        )
        self.price_plot.setLabel("left", price_label)
        self.price_plot.setLabel("bottom", "Time (UTC)")
        self.price_plot.showGrid(x=True, y=True, alpha=0.15)
        self.price_plot.setMenuEnabled(False)
        self.price_plot.addLegend(offset=(12, 12))
        for name in ("left", "bottom"):
            axis = self.price_plot.getAxis(name)
            axis.setPen(pg.mkPen("#475569"))
            axis.setTextPen(pg.mkPen("#94a3b8"))
        self.price_plot.getAxis("left").enableAutoSIPrefix(False)

        self.bid_curve = self._curve("Best bid", self.BID_COLOUR)
        self.ask_curve = self._curve("Best ask", self.ASK_COLOUR)
        self.mid_curve = self._curve("Midprice", self.MID_COLOUR)
        self.mid_curve.setZValue(1)

        self.statusBar().showMessage(
            "Scroll to zoom · drag to pan · disable Follow latest to inspect history"
        )
        self.statusBar().setStyleSheet("background: #101827; color: #94a3b8;")
        self.price_plot.getViewBox().sigRangeChangedManually.connect(
            self._stop_following
        )
        self.follow_latest.toggled.connect(self._follow_changed)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(refresh_ms)
        self.timer.timeout.connect(self.refresh)

    def _curve(self, name, colour):
        return self.price_plot.plot(
            name=name,
            pen=pg.mkPen(colour, width=1),
            antialias=False,
            clipToView=True,
            autoDownsample=True,
            downsampleMethod="peak",
        )

    def submit(self, observation: "bookObvservation | None") -> None:
        """Enqueue one observation without blocking the producer; ignore None.

        Aware timestamps are required so the UTC axis is unambiguous. Decimal
        prices are converted here for display, leaving the source untouched.
        """
        if observation is None:
            return
        if observation.timestamp.utcoffset() is None:
            raise ValueError("Observation timestamps must include a timezone")
        point = (
            observation.timestamp.timestamp(),
            float(observation.best_bid),
            float(observation.best_ask),
            float(observation.mid_price),
        )
        if not all(isfinite(value) for value in point):
            raise ValueError("Observation timestamp and prices must be finite")
        while True:
            try:
                self._pending.put_nowait(point)
                return
            except Full:
                try:
                    self._pending.get_nowait()
                except Empty:
                    continue
                self._pending.task_done()

    def refresh(self) -> None:
        """Consume at most one queue capacity per refresh, then redraw once."""
        changed = False
        for _ in range(self._pending.maxsize):
            try:
                point = self._pending.get_nowait()
            except Empty:
                break
            try:
                # Late observations must not make the time axis run backwards.
                if self._history and point[0] < self._history[-1][0]:
                    continue
                self._history.append(point)
                changed = True
            finally:
                self._pending.task_done()

        if not changed:
            return
        cutoff = self._history[-1][0] - self.window_seconds
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

        data = np.asarray(self._history, dtype=float)
        for curve, column in (
            (self.bid_curve, 1), (self.ask_curve, 2), (self.mid_curve, 3),
        ):
            curve.setData(data[:, 0], data[:, column])

        timestamp, bid, ask, mid = self._history[-1]
        clock = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%H:%M:%S UTC")
        self.readout.setText(
            f"Mid {mid:,.4f}    Bid {bid:,.4f}    Ask {ask:,.4f}"
            f"    Spread {ask - bid:,.4f}    ·    {clock}"
        )
        self._update_view()

    def _update_view(self):
        if self.follow_latest.isChecked() and self._history:
            latest = self._history[-1][0]
            self.price_plot.setXRange(
                latest - self.window_seconds, latest, padding=0.02,
            )
            self.price_plot.enableAutoRange(axis="y", enable=True)

    def _stop_following(self, *_):
        self.follow_latest.setChecked(False)

    def _follow_changed(self, enabled):
        if enabled:
            self._update_view()
        else:
            self.price_plot.disableAutoRange()

    def start(self, *, block: bool = True) -> None:
        """Show the window; use block=False inside an existing Qt event loop."""
        if self._closed:
            raise RuntimeError("Create a new LivePlotter after closing this window")
        self.refresh()
        self.show()
        self.timer.start()
        if block:
            self._app.exec()

    def closeEvent(self, event):
        self.timer.stop()
        if not self._closed:
            self._closed = True
            # Remove plot widgets before Qt destroys their scene (PySide).
            self.price_plot.close()
            self.chart.close()
            self.closed.emit()
        super().closeEvent(event)
