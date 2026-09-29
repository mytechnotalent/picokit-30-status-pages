"""Tests for the authenticated gateway listener.

Parameters
----------
None

Returns
-------
None
"""

import crypto
import listen
import store


def test_handle_stores_authenticated_frame(tmp_path):
    """Verify an authenticated frame is decoded and stored.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "gw.db"))
    envelope = crypto.seal_field_frame(b'{"n":7,"s":12,"t":235,"h":610}')
    record = {"address": 1, "payload": envelope, "rssi": -71, "snr": 9.5}
    listen._handle(store_obj, record)
    frames = store_obj.latest_frames()
    store_obj.close()
    assert frames[0]["node"] == 7
    assert frames[0]["temp_tenths"] == 235


def test_handle_rejects_forged_frame(tmp_path):
    """Verify a forged frame is logged as an event, not telemetry.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "gw.db"))
    record = {"address": 200, "payload": "deadbeef", "rssi": -90, "snr": 1.0}
    listen._handle(store_obj, record)
    events = store_obj.recent_events()
    count = store_obj.count_frames()
    store_obj.close()
    assert count == 0
    assert events[0]["kind"] == "UNAUTHENTICATED"
