"""Authenticated LoRa listener that logs gateway telemetry to SQLite.

The listener opens the gateway RYLR998, provisions its address and network,
reads every +RCV frame, authenticates the hex envelope with the shared field
key, and writes the decoded telemetry into the SQLite store. A frame that
fails authentication is recorded as an UNAUTHENTICATED event and its forged
body is never parsed. Run it next to the dashboard so the dashboard has live
rows to show.

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
import crypto
import rylr998
import store

DEFAULT_DB = "gateway.db"
DEFAULT_HUB = "0001"
DEFAULT_NETWORK = 18


def _parse_args(argv):
    """Parse listener command-line arguments.

    Parameters
    ----------
    argv : list of str or None
        Argument vector without the program name.

    Returns
    -------
    argparse.Namespace
        Parsed listener arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Serial port device")
    parser.add_argument("--baud", type=int, default=rylr998.DEFAULT_BAUD,
                        help="Radio baud rate")
    parser.add_argument("--hub", default=DEFAULT_HUB,
                        help="Gateway radio address")
    parser.add_argument("--network", type=int, default=DEFAULT_NETWORK,
                        help="Radio network identifier")
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="SQLite database path")
    return parser.parse_args(argv)


def _authenticate(payload_hex):
    """Decrypt and authenticate one hex envelope.

    Parameters
    ----------
    payload_hex : str
        Hex encoded sealed envelope.

    Returns
    -------
    str or None
        Decrypted JSON body, or None when authentication fails.
    """
    try:
        return crypto.open_field_frame(payload_hex).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _frame_record(body, address):
    """Build a store frame record from a decrypted telemetry body.

    Parameters
    ----------
    body : str
        Decrypted JSON telemetry body.
    address : int
        Sender radio address.

    Returns
    -------
    dict
        Frame record with node, seq, type, and payload.
    """
    data = json.loads(body)
    return {"node": data.get("n", address), "seq": data.get("s", 0),
            "type": codec.TYPE_TELEMETRY, "payload": body.encode("utf-8")}


def _reject(store_obj, record):
    """Record one unauthenticated frame as an event.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    record : dict
        Parsed +RCV record.

    Returns
    -------
    None
    """
    store_obj.insert_event(record["address"], "UNAUTHENTICATED", "rejected")
    print("UNAUTHENTICATED from {0}".format(record["address"]), flush=True)


def _handle(store_obj, record):
    """Authenticate and store one received radio record.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    record : dict
        Parsed +RCV record.

    Returns
    -------
    None
    """
    body = _authenticate(record["payload"])
    if body is None:
        _reject(store_obj, record)
        return
    frame = _frame_record(body, record["address"])
    store_obj.insert_frame(frame, record["rssi"], record["snr"])
    print("OK node={0} rssi={1} snr={2}".format(
        frame["node"], record["rssi"], record["snr"]), flush=True)


def _loop(store_obj, radio):
    """Receive and store frames until interrupted.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    radio : rylr998.RYLR998
        Open radio driver.

    Returns
    -------
    None
    """
    while True:
        record = radio.receive()
        if record is not None:
            _handle(store_obj, record)


def main(argv=None):
    """Run the authenticated listener loop.

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
    radio = rylr998.RYLR998(args.port, args.baud)
    store_obj = store.TelemetryStore(args.db)
    try:
        radio.set_address(int(args.hub))
        radio.set_network(args.network)
        _loop(store_obj, radio)
    except KeyboardInterrupt:
        pass
    finally:
        radio.close()
        store_obj.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
