from datetime import datetime, timedelta, timezone
from decimal import Decimal
import threading
from types import SimpleNamespace

import pytest

from live_plotter import LivePlotter


def observation(seconds, mid="100.25"):
    price = Decimal(mid)
    return SimpleNamespace(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)
        + timedelta(seconds=seconds),
        best_bid=price - Decimal("0.25"),
        best_ask=price + Decimal("0.25"),
        mid_price=price,
    )


@pytest.fixture
def plotter():
    window = LivePlotter(window_seconds=10, max_points=4)
    yield window
    window.close()


def test_worker_can_submit_and_curves_use_observation_prices(plotter):
    sample = observation(0)
    worker = threading.Thread(target=plotter.submit, args=(sample,))
    worker.start()
    worker.join()
    plotter.refresh()

    assert list(plotter.bid_curve.getData()[1]) == [100.0]
    assert list(plotter.ask_curve.getData()[1]) == [100.5]
    assert list(plotter.mid_curve.getData()[1]) == [100.25]
    colours = {curve.opts["pen"].color().name() for curve in (
        plotter.bid_curve, plotter.ask_curve, plotter.mid_curve,
    )}
    assert len(colours) == 3
    assert sample.mid_price == Decimal("100.25")
    assert plotter._pending.unfinished_tasks == 0


def test_overload_keeps_latest_points_and_balances_queue(plotter):
    for second in range(10):
        plotter.submit(observation(second))
    plotter.refresh()
    assert len(plotter._history) == 4
    assert plotter._history[0][0] == observation(6).timestamp.timestamp()
    assert plotter._pending.unfinished_tasks == 0


def test_history_expires_and_late_points_are_ignored(plotter):
    for second in (0, 8, 15, 7):
        plotter.submit(observation(second))
    plotter.refresh()
    assert [point[0] for point in plotter._history] == [
        observation(second).timestamp.timestamp() for second in (8, 15)
    ]


def test_disabled_follow_preserves_manual_view(plotter):
    plotter.submit(observation(0))
    plotter.refresh()
    plotter.follow_latest.setChecked(False)
    plotter.price_plot.setXRange(100, 200, padding=0)
    plotter.submit(observation(20))
    plotter.refresh()
    assert plotter.price_plot.viewRange()[0] == [100, 200]


def test_none_invalid_observations_and_window_lifecycle(plotter):
    plotter.submit(None)
    naive = observation(0)
    naive.timestamp = naive.timestamp.replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone"):
        plotter.submit(naive)
    with pytest.raises(ValueError, match="finite"):
        plotter.submit(observation(0, "NaN"))
    assert plotter._pending.empty()

    closed = []
    plotter.closed.connect(lambda: closed.append(True))
    plotter.start(block=False)
    assert plotter.timer.isActive()
    plotter.close()
    assert not plotter.timer.isActive()
    assert closed == [True]
