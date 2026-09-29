"""Rich terminal dashboard for the gateway.

The dashboard refreshes live node values, the most recent alarm and event
rows, and a small command console. Commands typed at the prompt are
dispatched by run_command, so the operator can acknowledge an alarm or
inspect the frame count without leaving the dashboard.

Parameters
----------
None

Returns
-------
None
"""

import argparse
import queue
import sys
import threading
import time

import store

DEFAULT_DB = "gateway.db"
DEFAULT_INTERVAL = 1.0
CONSOLE_LINES = 4
HELP_TEXT = "commands: help, ack <node>, count"


def _require_rich():
    """Import and return the rich building blocks for the dashboard.

    Parameters
    ----------
    None

    Returns
    -------
    tuple
        Console, Live, Table, Panel, and Layout classes.

    Raises
    ------
    RuntimeError
        When the rich package is not installed.
    """
    try:
        from rich.console import Console
        from rich.live import Live
        from rich.layout import Layout
        from rich.panel import Panel
        from rich.table import Table
    except ImportError as exc:
        raise RuntimeError("rich is required for the dashboard") from exc
    return Console, Live, Table, Panel, Layout


def _tenths(value):
    """Format a tenths value as one decimal place.

    Parameters
    ----------
    value : int or None
        Value in tenths, or None when absent.

    Returns
    -------
    str
        Formatted value, or a dash when absent.
    """
    if value is None:
        return "-"
    return "{0:.1f}".format(value / 10.0)


def _node_table(table_cls, frames):
    """Build the live node value table.

    Parameters
    ----------
    table_cls : type
        Rich Table class.
    frames : list of dict
        Latest frame per node.

    Returns
    -------
    object
        Rich table renderable.
    """
    table = table_cls(title="Live Nodes", expand=True)
    for column in ("Node", "Seq", "Temp C", "Hum %", "RSSI", "UTC"):
        table.add_column(column)
    for row in frames:
        table.add_row(str(row["node"]), str(row["seq"]),
                      _tenths(row["temp_tenths"]), _tenths(row["hum_tenths"]),
                      str(row["rssi"]), str(row["utc"])[:19])
    return table


def _event_table(table_cls, events):
    """Build the alarm and event log table.

    Parameters
    ----------
    table_cls : type
        Rich Table class.
    events : list of dict
        Recent gateway events.

    Returns
    -------
    object
        Rich table renderable.
    """
    table = table_cls(title="Events", expand=True)
    for column in ("UTC", "Node", "Kind", "Detail"):
        table.add_column(column)
    for row in events:
        table.add_row(str(row["utc"])[:19], str(row["node"]),
                      str(row["kind"]), str(row["detail"]))
    return table


def _build_layout(layout_cls, panel_cls, nodes, events, console_text):
    """Assemble the dashboard layout from its panels.

    Parameters
    ----------
    layout_cls : type
        Rich Layout class.
    panel_cls : type
        Rich Panel class.
    nodes : object
        Live node table renderable.
    events : object
        Event table renderable.
    console_text : str
        Command console transcript.

    Returns
    -------
    object
        Rich layout renderable.
    """
    layout = layout_cls()
    layout.split_column(
        layout_cls(name="nodes", size=12),
        layout_cls(name="events", size=10),
        layout_cls(name="console", size=6),
    )
    layout["nodes"].update(panel_cls(nodes, title="Live Nodes"))
    layout["events"].update(panel_cls(events, title="Alarms and Events"))
    layout["console"].update(panel_cls(console_text, title="Console"))
    return layout


def run_command(store_obj, text):
    """Dispatch one typed console command.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    text : str
        Raw command text.

    Returns
    -------
    str
        Command result message.
    """
    parts = text.strip().split()
    if not parts:
        return "empty command"
    verb = parts[0].lower()
    if verb in ("help", "?"):
        return HELP_TEXT
    if verb == "ack":
        node = int(parts[1]) if len(parts) > 1 else 0
        store_obj.insert_event(node, "ACK", "operator acknowledged")
        return "ack recorded for node {0}".format(node)
    if verb == "count":
        return "stored frames {0}".format(store_obj.count_frames())
    return "unknown command: {0}".format(verb)


def render(store_obj, messages, parts):
    """Render the complete dashboard state.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    messages : list of str
        Recent console transcript lines.
    parts : tuple
        Rich classes returned by _require_rich.

    Returns
    -------
    object
        Rich layout renderable.
    """
    table_cls = parts[2]
    panel_cls = parts[3]
    layout_cls = parts[4]
    nodes = _node_table(table_cls, store_obj.latest_frames())
    events = _event_table(table_cls, store_obj.recent_events())
    console_text = "\n".join(messages[-CONSOLE_LINES:]) or HELP_TEXT
    return _build_layout(layout_cls, panel_cls, nodes, events, console_text)


def _drain_commands(store_obj, inbox, messages):
    """Apply every queued console command without blocking.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    inbox : queue.Queue
        Queued command lines.
    messages : list of str
        Mutable console transcript.

    Returns
    -------
    None
    """
    while True:
        try:
            text = inbox.get_nowait()
        except queue.Empty:
            return
        messages.append(run_command(store_obj, text))


def _reader(inbox):
    """Read console lines from standard input into a queue.

    Parameters
    ----------
    inbox : queue.Queue
        Queue receiving command lines.

    Returns
    -------
    None
    """
    while True:
        line = sys.stdin.readline()
        if not line:
            return
        inbox.put(line)


def _run_live(store_obj, parts, console_obj, interval):
    """Run the live dashboard refresh loop.

    Parameters
    ----------
    store_obj : store.TelemetryStore
        Open telemetry store.
    parts : tuple
        Rich classes returned by _require_rich.
    console_obj : object
        Rich console instance.
    interval : float
        Refresh interval in seconds.

    Returns
    -------
    None
    """
    messages = []
    inbox = queue.Queue()
    worker = threading.Thread(target=_reader, args=(inbox,), daemon=True)
    worker.start()
    live_cls = parts[1]
    with live_cls(console=console_obj, screen=True) as live:
        while True:
            _drain_commands(store_obj, inbox, messages)
            live.update(render(store_obj, messages, parts))
            time.sleep(interval)


def _parse_args(argv):
    """Parse terminal dashboard command-line arguments.

    Parameters
    ----------
    argv : list of str or None
        Argument vector without the program name.

    Returns
    -------
    argparse.Namespace
        Parsed dashboard arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB,
                        help="SQLite database path")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                        help="Refresh interval in seconds")
    return parser.parse_args(argv)


def main(argv=None):
    """Run the terminal dashboard until interrupted.

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
    store_obj = store.TelemetryStore(args.db)
    parts = _require_rich()
    console_obj = parts[0]()
    try:
        _run_live(store_obj, parts, console_obj, args.interval)
    except KeyboardInterrupt:
        pass
    store_obj.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
