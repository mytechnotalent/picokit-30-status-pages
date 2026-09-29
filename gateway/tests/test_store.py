"""Tests for the SQLite telemetry and event store.

Parameters
----------
None

Returns
-------
None
"""

import store

FRAME = {"node": 7, "seq": 3, "type": 1,
         "payload": b'{"n":7,"s":3,"t":235,"h":610}'}


def test_insert_and_query_frames(tmp_path):
    """Verify a frame round trips through SQLite with decoded fields.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "test.db"))
    store_obj.insert_frame(FRAME, rssi=-71, snr=9.5)
    rows = store_obj.recent_frames()
    store_obj.close()
    assert len(rows) == 1
    assert rows[0]["temp_tenths"] == 235
    assert rows[0]["hum_tenths"] == 610
    assert rows[0]["rssi"] == -71


def test_latest_frames_per_node(tmp_path):
    """Verify one newest frame is returned for each node.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "latest.db"))
    store_obj.insert_frame(FRAME, rssi=-70, snr=8.0)
    second = dict(FRAME, node=8, seq=1)
    store_obj.insert_frame(second, rssi=-60, snr=7.0)
    rows = store_obj.latest_frames()
    store_obj.close()
    assert [row["node"] for row in rows] == [7, 8]


def test_event_log(tmp_path):
    """Verify events are inserted and returned newest first.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "events.db"))
    store_obj.insert_event(7, "ALARM", "temperature breach")
    rows = store_obj.recent_events()
    store_obj.close()
    assert rows[0]["kind"] == "ALARM"
    assert rows[0]["node"] == 7


def test_count_frames(tmp_path):
    """Verify the stored frame count matches the inserts.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    None
    """
    store_obj = store.TelemetryStore(str(tmp_path / "count.db"))
    store_obj.insert_frame(FRAME)
    store_obj.insert_frame(dict(FRAME, seq=4))
    total = store_obj.count_frames()
    store_obj.close()
    assert total == 2


def test_decode_payload_handles_plain_text():
    """Verify a non-JSON payload decodes without telemetry fields.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    text, temp, hum = store.decode_payload(b"plain text")
    assert text == "plain text"
    assert temp is None
    assert hum is None
