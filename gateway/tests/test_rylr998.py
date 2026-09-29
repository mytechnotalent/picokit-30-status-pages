"""Tests for the RYLR998 +RCV line parser.

Parameters
----------
None

Returns
-------
None
"""

import rylr998


def test_parse_rcv_record():
    """Verify a well formed +RCV line parses into typed fields.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    record = rylr998.parse_rcv("+RCV=7,11,hello world,-71,9.5")
    assert record["address"] == 7
    assert record["length"] == 11
    assert record["payload"] == "hello world"
    assert record["rssi"] == -71
    assert record["snr"] == 9.5


def test_parse_rcv_payload_with_commas():
    """Verify commas inside the payload are preserved.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    record = rylr998.parse_rcv("+RCV=7,7,a,b,c,d,-60,7.0")
    assert record["payload"] == "a,b,c,d"
    assert record["rssi"] == -60


def test_parse_rcv_rejects_garbage():
    """Verify non +RCV and short lines are rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert rylr998.parse_rcv("+OK") is None
    assert rylr998.parse_rcv("+RCV=1,2") is None


def test_parse_rcv_rejects_bad_numbers():
    """Verify malformed numeric fields are rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert rylr998.parse_rcv("+RCV=x,5,data,-70,9.0") is None
