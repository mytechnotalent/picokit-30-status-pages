"""Round-trip and tamper tests for the binary frame codec.

Parameters
----------
None

Returns
-------
None
"""

import codec
import pytest


def test_header_round_trip():
    """Verify a header packs and parses back to its fields.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    header = codec.build_header(codec.TYPE_ALARM, 5, 9)
    fields = codec.parse_header(header)
    assert fields == {"type": codec.TYPE_ALARM, "node": 5, "seq": 9}


def test_frame_round_trip():
    """Verify a sealed telemetry frame opens back to its payload.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    body = b'{"n":5,"s":9,"t":210,"h":500}'
    frame = codec.seal_frame(codec.TYPE_TELEMETRY, 5, 9, body)
    record = codec.open_frame(frame)
    assert record["payload"] == body
    assert record["name"] == "TELEMETRY"
    assert record["node"] == 5
    assert record["seq"] == 9


def test_wire_round_trip():
    """Verify hex wire encoding round trips a frame.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    frame = codec.seal_frame(codec.TYPE_HELLO, 1, 0, b"hi")
    assert codec.decode_wire(codec.encode_wire(frame)) == frame


def test_bad_sync_rejected():
    """Verify a wrong sync word is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    header = codec.build_header(codec.TYPE_ACK, 1, 0)
    broken = b"\x00\x00" + header[2:]
    with pytest.raises(ValueError):
        codec.parse_header(broken)


def test_tampered_frame_rejected():
    """Verify a flipped tag byte is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    frame = bytearray(codec.seal_frame(codec.TYPE_COMMAND, 1, 0, b"go"))
    frame[-1] ^= 0x01
    with pytest.raises(ValueError):
        codec.open_frame(bytes(frame))


def test_short_frame_rejected():
    """Verify a truncated frame is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(ValueError):
        codec.open_frame(b"\x00" * 10)


def test_type_name_lookup():
    """Verify frame type names resolve and default safely.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert codec.type_name(codec.TYPE_CONFIG) == "CONFIG"
    assert codec.type_name(99) == "UNKNOWN"


def test_decode_wire_rejects_garbage():
    """Verify non-hex wire text is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    with pytest.raises(ValueError):
        codec.decode_wire("not-hex")
