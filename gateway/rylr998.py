"""AT-command driver for the REYAX RYLR998 LoRa transceiver.

The driver speaks the plain CRLF-terminated AT protocol over a pyserial
connection. It programs the local address and network, transmits ASCII
payloads, and parses inbound +RCV lines into sender, length, payload,
RSSI, and SNR fields. The radio layer is deliberately payload agnostic so
the authenticated frame codec can sit directly on top of it.

Parameters
----------
None

Returns
-------
None
"""

try:
    import serial
except ImportError:
    serial = None

DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 1.0
RCV_PREFIX = "+RCV="
READ_ERRORS = "replace"


def _require_serial():
    """Return the imported pyserial module.

    Parameters
    ----------
    None

    Returns
    -------
    module
        The imported pyserial module.

    Raises
    ------
    RuntimeError
        When pyserial is not installed.
    """
    if serial is None:
        raise RuntimeError("pyserial is required for the RYLR998 driver")
    return serial


def _to_int(text):
    """Parse a decimal integer field.

    Parameters
    ----------
    text : str
        Candidate decimal text.

    Returns
    -------
    int or None
        Parsed integer, or None when the text is not a number.
    """
    try:
        return int(text)
    except ValueError:
        return None


def _split_rcv(text):
    """Split a +RCV tail using the declared payload length.

    Parameters
    ----------
    text : str
        +RCV fields after the prefix.

    Returns
    -------
    dict or None
        Typed record, or None when the line is malformed.
    """
    address, _, rest = text.partition(",")
    length_text, _, body = rest.partition(",")
    length = _to_int(length_text)
    if length is None or body[length:length + 1] != ",":
        return None
    tail = body[length + 1:].split(",", 1)
    if len(tail) != 2:
        return None
    return _rcv_record(address, length_text, body[:length], tail[0], tail[1])


def _rcv_record(address, length, payload, rssi, snr):
    """Convert raw +RCV fields into a typed record.

    Parameters
    ----------
    address : str
        Sender address field.
    length : str
        Declared payload length field.
    payload : str
        ASCII payload field.
    rssi : str
        Received signal strength field.
    snr : str
        Signal to noise ratio field.

    Returns
    -------
    dict or None
        Typed record, or None when a numeric field is malformed.
    """
    try:
        return {"address": int(address), "length": int(length),
                "payload": payload, "rssi": int(rssi), "snr": float(snr)}
    except ValueError:
        return None


def parse_rcv(line):
    """Parse one +RCV wire line into a typed record.

    Parameters
    ----------
    line : str
        Raw radio line beginning with the +RCV= prefix.

    Returns
    -------
    dict or None
        Record with address, length, payload, rssi, and snr, or None
        when the line is not a well formed +RCV line.
    """
    if not line.startswith(RCV_PREFIX):
        return None
    return _split_rcv(line[len(RCV_PREFIX):])


class RYLR998:
    """AT-command driver bound to one serial radio port.

    Parameters
    ----------
    port : str
        Serial port device path.
    baud : int
        Negotiated baud rate.
    timeout : float
        Read timeout in seconds.

    Returns
    -------
    None
    """

    def __init__(self, port, baud=DEFAULT_BAUD, timeout=DEFAULT_TIMEOUT):
        """Open the radio serial connection.

        Parameters
        ----------
        port : str
            Serial port device path.
        baud : int
            Negotiated baud rate.
        timeout : float
            Read timeout in seconds.

        Returns
        -------
        None
        """
        module = _require_serial()
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial = module.Serial(port, baud, timeout=timeout)

    def close(self):
        """Close the radio serial connection.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.serial.close()

    def write_command(self, command):
        """Write one CRLF-terminated AT command.

        Parameters
        ----------
        command : str
            AT command text without the terminator.

        Returns
        -------
        None
        """
        self.serial.write("{0}\r\n".format(command).encode("utf-8"))
        self.serial.flush()

    def set_address(self, address):
        """Program the local radio address.

        Parameters
        ----------
        address : int
            Local numeric radio address.

        Returns
        -------
        None
        """
        self.write_command("AT+ADDRESS={0}".format(int(address)))

    def set_network(self, network_id):
        """Program the shared radio network identifier.

        Parameters
        ----------
        network_id : int
            Shared numeric network identifier.

        Returns
        -------
        None
        """
        self.write_command("AT+NETWORKID={0}".format(int(network_id)))

    def send(self, address, payload):
        """Transmit one ASCII payload to a target address.

        Parameters
        ----------
        address : int or str
            Destination radio address.
        payload : str
            ASCII payload text.

        Returns
        -------
        None
        """
        self.write_command("AT+SEND={0},{1},{2}".format(
            address, len(payload), payload))

    def read_line(self):
        """Read and decode one CRLF-terminated radio line.

        Parameters
        ----------
        None

        Returns
        -------
        str or None
            Stripped line text, or None when the read timed out.
        """
        raw = self.serial.readline()
        if not raw:
            return None
        return raw.decode("utf-8", errors=READ_ERRORS).strip()

    def receive(self):
        """Read one line and parse a +RCV record when present.

        Parameters
        ----------
        None

        Returns
        -------
        dict or None
            Parsed +RCV record, or None when no frame is waiting.
        """
        line = self.read_line()
        if line is None:
            return None
        return parse_rcv(line)
