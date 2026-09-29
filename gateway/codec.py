"""Binary authenticated frame codec for the node.

A wire frame is laid out as SYNC, VER, TYPE, NODE_ID, SEQ, NONCE, CT,
and TAG. The nine byte header is authenticated as associated data and the
payload is sealed with the shared AES-128 field key using AES-CCM. Frames
travel over the radio as lowercase hex text so the ASCII AT payload path
is preserved.

Parameters
----------
None

Returns
-------
None
"""

import secrets
import struct

import crypto

SYNC = 0xA55A
VERSION = 1
TYPE_TELEMETRY = 1
TYPE_COMMAND = 2
TYPE_ACK = 3
TYPE_ALARM = 4
TYPE_CONFIG = 5
TYPE_HELLO = 6
_TYPE_PAIRS = (
    (TYPE_TELEMETRY, "TELEMETRY"),
    (TYPE_COMMAND, "COMMAND"),
    (TYPE_ACK, "ACK"),
    (TYPE_ALARM, "ALARM"),
    (TYPE_CONFIG, "CONFIG"),
    (TYPE_HELLO, "HELLO"),
)
TYPE_NAMES = dict(_TYPE_PAIRS)
HEADER = struct.Struct("<HBBBI")
HEADER_LEN = HEADER.size
NONCE_LEN = 13
TAG_LEN = 16
MIN_FRAME_LEN = HEADER_LEN + NONCE_LEN + TAG_LEN


def type_name(type_id):
    """Return the symbolic name of a frame type identifier.

    Parameters
    ----------
    type_id : int
        Numeric frame type identifier.

    Returns
    -------
    str
        Symbolic type name, or UNKNOWN when unrecognized.
    """
    return TYPE_NAMES.get(type_id, "UNKNOWN")


def build_header(type_id, node_id, seq):
    """Build the authenticated frame header bytes.

    Parameters
    ----------
    type_id : int
        Numeric frame type identifier.
    node_id : int
        Originating node identifier.
    seq : int
        Monotonic frame sequence number.

    Returns
    -------
    bytes
        Nine byte packed frame header.
    """
    return HEADER.pack(SYNC, VERSION, type_id, node_id, seq)


def parse_header(header):
    """Parse and validate a frame header.

    Parameters
    ----------
    header : bytes
        Nine byte packed frame header.

    Returns
    -------
    dict
        Parsed type, node, and sequence fields.

    Raises
    ------
    ValueError
        When the sync word or version is not supported.
    """
    sync, version, type_id, node_id, seq = HEADER.unpack(header)
    if sync != SYNC:
        raise ValueError("bad frame sync word")
    if version != VERSION:
        raise ValueError("unsupported frame version")
    return {"type": type_id, "node": node_id, "seq": seq}


def seal_frame(type_id, node_id, seq, payload):
    """Seal a payload into an authenticated binary wire frame.

    Parameters
    ----------
    type_id : int
        Numeric frame type identifier.
    node_id : int
        Originating node identifier.
    seq : int
        Monotonic frame sequence number.
    payload : bytes
        Plaintext payload to seal.

    Returns
    -------
    bytes
        Header, nonce, ciphertext, and tag concatenated.
    """
    header = build_header(type_id, node_id, seq)
    nonce = secrets.token_bytes(NONCE_LEN)
    ciphertext, tag = crypto.ccm_seal(
        crypto.derive_field_key(), nonce, header, payload)
    return header + nonce + ciphertext + tag


def split_frame(frame):
    """Split a wire frame into its header, nonce, ciphertext, and tag.

    Parameters
    ----------
    frame : bytes
        Complete binary wire frame.

    Returns
    -------
    tuple of bytes
        Header, nonce, ciphertext, and tag fields.

    Raises
    ------
    ValueError
        When the frame is shorter than the fixed overhead.
    """
    if len(frame) < MIN_FRAME_LEN:
        raise ValueError("frame is too short")
    header = frame[:HEADER_LEN]
    nonce = frame[HEADER_LEN:HEADER_LEN + NONCE_LEN]
    ciphertext = frame[HEADER_LEN + NONCE_LEN:len(frame) - TAG_LEN]
    return header, nonce, ciphertext, frame[len(frame) - TAG_LEN:]


def open_frame(frame):
    """Authenticate and decode a binary wire frame.

    Parameters
    ----------
    frame : bytes
        Complete binary wire frame.

    Returns
    -------
    dict
        Parsed type, name, node, seq, and plaintext payload fields.

    Raises
    ------
    ValueError
        When the frame is malformed or fails authentication.
    """
    header, nonce, ciphertext, tag = split_frame(frame)
    fields = parse_header(header)
    fields["payload"] = crypto.ccm_open(
        crypto.derive_field_key(), nonce, header, ciphertext, tag)
    fields["name"] = type_name(fields["type"])
    return fields


def encode_wire(frame):
    """Encode a binary frame as lowercase hex for radio transport.

    Parameters
    ----------
    frame : bytes
        Complete binary wire frame.

    Returns
    -------
    str
        Lowercase hexadecimal wire payload.
    """
    return frame.hex()


def decode_wire(text):
    """Decode a lowercase hex radio payload into frame bytes.

    Parameters
    ----------
    text : str
        Lowercase hexadecimal wire payload.

    Returns
    -------
    bytes
        Decoded binary frame.

    Raises
    ------
    ValueError
        When the text is not valid hexadecimal.
    """
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError("wire payload is not valid hex") from exc
