"""Simulated node that emits authenticated telemetry.

The simulator drives the gateway radio with the same fixed-field JSON
telemetry that the RP2350 firmware produces, sealing every frame with the
shared AES-128 field key so the gateway accepts it. It also drains the
downlink, authenticates any COMMAND, ACK, or CONFIG frame, and reports the
decoded action, which lets the whole two-way path be tested from a laptop.

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
import time

import codec
import crypto
import rylr998

DEFAULT_HUB = "0001"
DEFAULT_NODE = 1
DEFAULT_INTERVAL = 5.0
DEFAULT_TEMP = 50
DEFAULT_HUM = 610
SIM_TIMEOUT = 0.1


def _add_node_args(parser):
    """Add the simulator radio and telemetry options.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Parser receiving the simulator options.

    Returns
    -------
    argparse.ArgumentParser
        The same parser.
    """
    parser.add_argument("--port", required=True, help="Serial port device")
    parser.add_argument("--baud", type=int, default=rylr998.DEFAULT_BAUD,
                        help="Radio baud rate")
    parser.add_argument("--node", type=int, default=DEFAULT_NODE,
                        help="Node identifier")
    parser.add_argument("--hub", default=DEFAULT_HUB,
                        help="Gateway radio address")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                        help="Transmit interval in seconds")
    parser.add_argument("--temp", type=int, default=DEFAULT_TEMP,
                        help="Temperature in tenths Celsius")
    parser.add_argument("--hum", type=int, default=DEFAULT_HUM,
                        help="Humidity in tenths percent")
    return parser


def _parse_args(argv):
    """Parse simulator command-line arguments.

    Parameters
    ----------
    argv : list of str or None
        Argument vector without the program name.

    Returns
    -------
    argparse.Namespace
        Parsed simulator arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    _add_node_args(parser)
    return parser.parse_args(argv)


def telemetry_payload(node, seq, temp, hum):
    """Build the compact JSON telemetry body.

    Parameters
    ----------
    node : int
        Node identifier.
    seq : int
        Transmit sequence number.
    temp : int
        Temperature in tenths Celsius.
    hum : int
        Humidity in tenths percent.

    Returns
    -------
    bytes
        Compact JSON telemetry payload.
    """
    data = {"n": node, "s": seq, "t": temp, "h": hum}
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def apply_command(record):
    """Apply one decoded downlink frame.

    Parameters
    ----------
    record : dict
        Decoded frame from the codec.

    Returns
    -------
    str
        Human readable result of the applied command.
    """
    try:
        data = json.loads(record.get("payload", b"").decode("utf-8"))
    except (ValueError, AttributeError, UnicodeDecodeError):
        return "malformed command"
    action = data.get("cmd", record.get("name", "command"))
    return "applied {0}".format(action)


def _tick(radio, args, seq):
    """Transmit one authenticated telemetry frame.

    Parameters
    ----------
    radio : rylr998.RYLR998
        Open radio driver.
    args : argparse.Namespace
        Parsed simulator arguments.
    seq : int
        Current sequence number.

    Returns
    -------
    None
    """
    body = telemetry_payload(args.node, seq, args.temp, args.hum)
    envelope = crypto.seal_field_frame(body)
    radio.send(args.hub, envelope)
    print("[node {0}] seq {1}".format(args.node, seq), flush=True)


def _decode_downlink(text):
    """Decode a downlink payload from either supported frame format.

    Parameters
    ----------
    text : str
        Lowercase hex payload reported by the radio.

    Returns
    -------
    dict
        Decoded frame record.
    """
    try:
        return codec.open_frame(codec.decode_wire(text))
    except ValueError:
        return {"payload": crypto.open_field_frame(text), "name": "FIELD"}


def _consume(radio):
    """Read, authenticate, and apply one downlink frame when present.

    Parameters
    ----------
    radio : rylr998.RYLR998
        Open radio driver.

    Returns
    -------
    None
    """
    record = radio.receive()
    if record is None:
        return
    message = apply_command(_decode_downlink(record["payload"]))
    print("[node] {0}".format(message), flush=True)


def run(radio, args):
    """Run the simulator transmit and receive loop.

    Parameters
    ----------
    radio : rylr998.RYLR998
        Open radio driver.
    args : argparse.Namespace
        Parsed simulator arguments.

    Returns
    -------
    None
    """
    seq = 0
    while True:
        _tick(radio, args, seq)
        seq += 1
        time.sleep(args.interval)
        _consume(radio)


def main(argv=None):
    """Run the node simulator until interrupted.

    Parameters
    ----------
    argv : list of str or None
        Argument vector without the program name.

    Returns
    -------
    int
        Zero on clean shutdown.
    """
    args = _parse_args(argv)
    radio = rylr998.RYLR998(args.port, args.baud, timeout=SIM_TIMEOUT)
    try:
        run(radio, args)
    except KeyboardInterrupt:
        pass
    finally:
        radio.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
