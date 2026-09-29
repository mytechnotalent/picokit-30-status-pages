"""Command-line control for the gateway.

The tool sends authenticated COMMAND, ACK, and CONFIG frames to a node
through the RYLR998 radio, and optionally records an event row in the
SQLite log. Every payload is sealed with the shared field key, so the node
only acts on frames that authenticate.

Parameters
----------
None

Returns
-------
None
"""

import argparse
import json
import sys

import codec
import rylr998
import store

DEFAULT_HUB = "0001"


def _add_common(sub):
    """Add the shared radio options to one subcommand parser.

    Parameters
    ----------
    sub : argparse.ArgumentParser
        Subcommand parser receiving the shared options.

    Returns
    -------
    argparse.ArgumentParser
        The same subcommand parser.
    """
    sub.add_argument("--port", required=True, help="Serial port device")
    sub.add_argument("--baud", type=int, default=rylr998.DEFAULT_BAUD,
                     help="Radio baud rate")
    sub.add_argument("--node", type=int, required=True,
                     help="Target node identifier")
    sub.add_argument("--hub", default=DEFAULT_HUB,
                     help="Gateway radio address")
    sub.add_argument("--db", default=None, help="Optional SQLite event log")
    return sub


def _add_send(sub):
    """Add the send subcommand payload option.

    Parameters
    ----------
    sub : argparse.ArgumentParser
        Send subcommand parser.

    Returns
    -------
    argparse.ArgumentParser
        The same parser.
    """
    sub.add_argument("--command", required=True, help="Command name")
    return sub


def _add_ack(sub):
    """Add the ack subcommand sequence option.

    Parameters
    ----------
    sub : argparse.ArgumentParser
        Ack subcommand parser.

    Returns
    -------
    argparse.ArgumentParser
        The same parser.
    """
    sub.add_argument("--seq", type=int, default=0, help="Sequence to ack")
    return sub


def _add_config(sub):
    """Add the config subcommand key=value option.

    Parameters
    ----------
    sub : argparse.ArgumentParser
        Config subcommand parser.

    Returns
    -------
    argparse.ArgumentParser
        The same parser.
    """
    sub.add_argument("--set", action="append", default=[], dest="pairs",
                     help="key=value configuration pair")
    return sub


def build_parser():
    """Build the gateway command-line parser.

    Parameters
    ----------
    None

    Returns
    -------
    argparse.ArgumentParser
        Parser with send, ack, and config subcommands.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    _add_send(_add_common(subs.add_parser("send")))
    _add_ack(_add_common(subs.add_parser("ack")))
    _add_config(_add_common(subs.add_parser("config")))
    return parser


def _json_bytes(data):
    """Encode a mapping as compact JSON bytes.

    Parameters
    ----------
    data : dict
        Payload mapping to encode.

    Returns
    -------
    bytes
        Compact UTF-8 JSON payload.
    """
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def _split_pair(text):
    """Split one key=value configuration pair.

    Parameters
    ----------
    text : str
        Configuration pair text.

    Returns
    -------
    tuple of str
        Key and value strings.
    """
    key, _, value = text.partition("=")
    return key, value


def command_payload(args):
    """Build the frame type and payload for a CLI action.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    tuple
        Frame type identifier and sealed-ready payload bytes.
    """
    if args.action == "ack":
        return codec.TYPE_ACK, _json_bytes({"ack": args.seq})
    if args.action == "config":
        data = dict(_split_pair(pair) for pair in args.pairs)
        return codec.TYPE_CONFIG, _json_bytes(data)
    return codec.TYPE_COMMAND, _json_bytes({"cmd": args.command})


def transmit(args, type_id, payload):
    """Seal a payload and transmit it over the radio.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    type_id : int
        Frame type identifier.
    payload : bytes
        Plaintext payload bytes.

    Returns
    -------
    None
    """
    frame = codec.seal_frame(type_id, args.node, 0, payload)
    radio = rylr998.RYLR998(args.port, args.baud)
    try:
        radio.send(args.hub, codec.encode_wire(frame))
    finally:
        radio.close()


def log_event(args):
    """Record the CLI action in the optional SQLite event log.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.

    Returns
    -------
    None
    """
    if args.db is None:
        return
    store_obj = store.TelemetryStore(args.db)
    try:
        store_obj.insert_event(args.node, args.action.upper(), "operator cli")
    finally:
        store_obj.close()


def main(argv=None):
    """Parse arguments and dispatch one gateway command.

    Parameters
    ----------
    argv : list of str or None
        Argument vector without the program name.

    Returns
    -------
    int
        Zero on success.
    """
    args = build_parser().parse_args(argv)
    type_id, payload = command_payload(args)
    transmit(args, type_id, payload)
    log_event(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
