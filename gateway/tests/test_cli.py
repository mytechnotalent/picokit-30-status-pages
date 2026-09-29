"""Tests for the gateway command-line helpers.

Parameters
----------
None

Returns
-------
None
"""

import cli
import codec


def test_command_payload_send():
    """Verify the send action builds a COMMAND frame.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser = cli.build_parser()
    args = parser.parse_args(
        ["send", "--port", "x", "--node", "5", "--command", "seal"])
    type_id, payload = cli.command_payload(args)
    assert type_id == codec.TYPE_COMMAND
    assert b"seal" in payload


def test_command_payload_ack():
    """Verify the ack action builds an ACK frame.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser = cli.build_parser()
    args = parser.parse_args(
        ["ack", "--port", "x", "--node", "5", "--seq", "12"])
    type_id, payload = cli.command_payload(args)
    assert type_id == codec.TYPE_ACK
    assert b"12" in payload


def test_command_payload_config():
    """Verify the config action builds a CONFIG frame.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    parser = cli.build_parser()
    args = parser.parse_args(
        ["config", "--port", "x", "--node", "5", "--set", "mode=auto"])
    type_id, payload = cli.command_payload(args)
    assert type_id == codec.TYPE_CONFIG
    assert b"auto" in payload


def test_split_pair():
    """Verify a key=value pair splits on the first equals sign.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert cli._split_pair("mode=auto") == ("mode", "auto")
