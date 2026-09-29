"""SQLite telemetry and event log for the gateway.

The store keeps two tables. The telemetry table holds every
authenticated frame with its decoded temperature and humidity fields. The
events table holds gateway level records such as rejected frames,
acknowledgements, and configuration changes. All timestamps are stored as
UTC ISO 8601 text.

Parameters
----------
None

Returns
-------
None
"""

import datetime
import json
import sqlite3

DEFAULT_PATH = "gateway.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utc TEXT NOT NULL,
    node INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    type INTEGER NOT NULL,
    temp_tenths INTEGER,
    hum_tenths INTEGER,
    rssi INTEGER,
    snr REAL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utc TEXT NOT NULL,
    node INTEGER,
    kind TEXT NOT NULL,
    detail TEXT NOT NULL
);
"""
INSERT_FRAME = """
INSERT INTO telemetry
    (utc, node, seq, type, temp_tenths, hum_tenths, rssi, snr, payload)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
INSERT_EVENT = """
INSERT INTO events (utc, node, kind, detail) VALUES (?, ?, ?, ?)
"""
SELECT_RECENT_FRAMES = """
SELECT * FROM telemetry ORDER BY id DESC LIMIT ?
"""
SELECT_LATEST_FRAMES = """
SELECT t.* FROM telemetry AS t
JOIN (SELECT node, MAX(id) AS newest FROM telemetry GROUP BY node) AS m
ON t.id = m.newest
ORDER BY t.node
"""
SELECT_RECENT_EVENTS = """
SELECT * FROM events ORDER BY id DESC LIMIT ?
"""
COUNT_FRAMES = "SELECT COUNT(*) FROM telemetry"


def utc_now():
    """Return the current UTC time as an ISO 8601 string.

    Parameters
    ----------
    None

    Returns
    -------
    str
        Current UTC timestamp.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def decode_payload(payload):
    """Decode a sealed payload into text and telemetry fields.

    Parameters
    ----------
    payload : bytes or str
        Recovered plaintext payload.

    Returns
    -------
    tuple
        Payload text, temperature in tenths, and humidity in tenths.
    """
    if isinstance(payload, bytes):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = str(payload)
    try:
        data = json.loads(text)
    except ValueError:
        data = {}
    return text, data.get("t"), data.get("h")


class TelemetryStore:
    """Persist authenticated telemetry and gateway events in SQLite.

    Parameters
    ----------
    path : str
        SQLite database file path.

    Returns
    -------
    None
    """

    def __init__(self, path=DEFAULT_PATH):
        """Open the database and create the schema when absent.

        Parameters
        ----------
        path : str
            SQLite database file path.

        Returns
        -------
        None
        """
        self.path = path
        self.connection = sqlite3.connect(path, timeout=5.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self):
        """Close the SQLite connection.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.connection.close()

    def insert_frame(self, record, rssi=None, snr=None):
        """Insert one authenticated frame and its decoded fields.

        Parameters
        ----------
        record : dict
            Decoded frame from the codec.
        rssi : int or None
            Radio signal strength in dBm.
        snr : float or None
            Radio signal to noise ratio in dB.

        Returns
        -------
        int
            Row identifier of the inserted frame.
        """
        text, temp, hum = decode_payload(record.get("payload", b""))
        values = (utc_now(), record.get("node"), record.get("seq"),
                  record.get("type"), temp, hum, rssi, snr, text)
        cursor = self.connection.execute(INSERT_FRAME, values)
        self.connection.commit()
        return cursor.lastrowid

    def insert_event(self, node, kind, detail):
        """Insert one gateway event record.

        Parameters
        ----------
        node : int or None
            Related node identifier.
        kind : str
            Event kind label.
        detail : str
            Human readable event detail.

        Returns
        -------
        int
            Row identifier of the inserted event.
        """
        values = (utc_now(), node, kind, detail)
        cursor = self.connection.execute(INSERT_EVENT, values)
        self.connection.commit()
        return cursor.lastrowid

    def recent_frames(self, limit=50):
        """Return the most recent telemetry frames.

        Parameters
        ----------
        limit : int
            Maximum number of rows to return.

        Returns
        -------
        list of dict
            Newest first telemetry rows.
        """
        cursor = self.connection.execute(SELECT_RECENT_FRAMES, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]

    def latest_frames(self):
        """Return the newest telemetry frame for every node.

        Parameters
        ----------
        None

        Returns
        -------
        list of dict
            One latest row per node, ordered by node identifier.
        """
        cursor = self.connection.execute(SELECT_LATEST_FRAMES)
        return [dict(row) for row in cursor.fetchall()]

    def recent_events(self, limit=50):
        """Return the most recent gateway events.

        Parameters
        ----------
        limit : int
            Maximum number of rows to return.

        Returns
        -------
        list of dict
            Newest first event rows.
        """
        cursor = self.connection.execute(SELECT_RECENT_EVENTS, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]

    def count_frames(self):
        """Return the total number of stored telemetry frames.

        Parameters
        ----------
        None

        Returns
        -------
        int
            Number of telemetry rows.
        """
        cursor = self.connection.execute(COUNT_FRAMES)
        return int(cursor.fetchone()[0])
