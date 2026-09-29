"""AES-CCM authenticated field crypto for the gateway.

The field key is a shared 16-byte AES-128 key. Every frame is sealed with
AES-CCM, which authenticates the associated data and the payload in one
pass and needs only the AES block cipher.

Parameters
----------
None

Returns
-------
None
"""

import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

FIELD_KEY = b"picokit-lab-key!"
NONCE_LEN = 13
TAG_LEN = 16
ASSOCIATED = b"\x01"


def derive_field_key():
    """Return the shared 16-byte AES-128 field key.

    Parameters
    ----------
    None

    Returns
    -------
    bytes
        The sixteen-byte AES-128 field key.
    """
    return FIELD_KEY


def ccm_seal(key, nonce, aad, plaintext):
    """Seal a plaintext with AES-CCM.

    Parameters
    ----------
    key : bytes
        Sixteen-byte AES-128 key.
    nonce : bytes
        Thirteen-byte nonce.
    aad : bytes
        Associated data authenticated but not encrypted.
    plaintext : bytes
        Payload to seal.

    Returns
    -------
    tuple of bytes
        Ciphertext and sixteen-byte tag.
    """
    sealed = AESCCM(key, tag_length=TAG_LEN).encrypt(nonce, plaintext, aad)
    return sealed[:-TAG_LEN], sealed[-TAG_LEN:]


def ccm_open(key, nonce, aad, ciphertext, tag):
    """Open and authenticate an AES-CCM ciphertext.

    Parameters
    ----------
    key : bytes
        Sixteen-byte AES-128 key.
    nonce : bytes
        Thirteen-byte nonce.
    aad : bytes
        Associated data authenticated but not encrypted.
    ciphertext : bytes
        Sealed ciphertext.
    tag : bytes
        Sixteen-byte authentication tag.

    Returns
    -------
    bytes
        Recovered plaintext bytes.

    Raises
    ------
    ValueError
        When authentication fails.
    """
    try:
        return AESCCM(key, tag_length=TAG_LEN).decrypt(
            nonce, ciphertext + tag, aad)
    except InvalidTag as exc:
        raise ValueError("authentication failed") from exc


def seal_field_frame(plaintext):
    """Seal a telemetry frame into a lowercase hex envelope.

    Parameters
    ----------
    plaintext : bytes
        Compact JSON telemetry body to seal.

    Returns
    -------
    str
        Lowercase hex of nonce, ciphertext, and tag.
    """
    nonce = secrets.token_bytes(NONCE_LEN)
    key = derive_field_key()
    ciphertext, tag = ccm_seal(key, nonce, ASSOCIATED, plaintext)
    return (nonce + ciphertext + tag).hex()


def open_field_frame(hex_payload):
    """Authenticate and open a lowercase hex telemetry envelope.

    Parameters
    ----------
    hex_payload : str
        Lowercase hex nonce, ciphertext, and tag.

    Returns
    -------
    bytes
        Recovered plaintext bytes.

    Raises
    ------
    ValueError
        When the envelope is malformed or fails authentication.
    """
    try:
        raw = bytes.fromhex(hex_payload)
    except ValueError as exc:
        raise ValueError("payload is not valid hex") from exc
    if len(raw) < NONCE_LEN + TAG_LEN:
        raise ValueError("payload is too short")
    nonce = raw[:NONCE_LEN]
    ciphertext = raw[NONCE_LEN:-TAG_LEN]
    tag = raw[-TAG_LEN:]
    return ccm_open(derive_field_key(), nonce, ASSOCIATED, ciphertext, tag)
