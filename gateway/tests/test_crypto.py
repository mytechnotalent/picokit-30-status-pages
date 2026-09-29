"""Known-answer and tamper tests for the gateway AES-CCM crypto module.

The vectors match the RP2350 firmware test suite, so a passing run proves
byte-for-byte interoperability with the embedded implementation.

Parameters
----------
None

Returns
-------
None
"""

import crypto
import pytest

FIELD_KEY = "7069636f6b69742d6c61622d6b657921"
FRAME_CT = "0e6ca7c6174478c02db75a9cee8baff77928905d"
FRAME_TAG = "7e28494f2f14250b7d557f81ca3d84bc"
NONCE = bytes(range(13))
PLAINTEXT = b'{"n":1,"s":12,"b":2}'


def test_field_key_matches_firmware():
    """Verify the field key matches the firmware vector.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    assert crypto.derive_field_key().hex() == FIELD_KEY


def test_ccm_matches_firmware():
    """Verify a sealed frame matches the firmware byte layout.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    ciphertext, tag = crypto.ccm_seal(
        crypto.derive_field_key(), NONCE, b"\x01", PLAINTEXT)
    assert ciphertext.hex() == FRAME_CT
    assert tag.hex() == FRAME_TAG


def test_public_aead_round_trip():
    """Verify the public AEAD wrappers seal and open a frame.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    key = crypto.derive_field_key()
    ciphertext, tag = crypto.ccm_seal(key, NONCE, b"\x01", PLAINTEXT)
    opened = crypto.ccm_open(key, NONCE, b"\x01", ciphertext, tag)
    assert opened == PLAINTEXT


def test_seal_open_round_trip():
    """Verify a sealed hex envelope opens back to the plaintext.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    envelope = crypto.seal_field_frame(PLAINTEXT)
    assert crypto.open_field_frame(envelope) == PLAINTEXT


def test_flipped_tag_rejected():
    """Verify a flipped authentication tag is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    raw = bytearray(bytes.fromhex(crypto.seal_field_frame(PLAINTEXT)))
    raw[-1] ^= 0x01
    with pytest.raises(ValueError):
        crypto.open_field_frame(bytes(raw).hex())


def test_flipped_ciphertext_rejected():
    """Verify flipped ciphertext is rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    raw = bytearray(bytes.fromhex(crypto.seal_field_frame(PLAINTEXT)))
    raw[crypto.NONCE_LEN] ^= 0x01
    with pytest.raises(ValueError):
        crypto.open_field_frame(bytes(raw).hex())


def test_malformed_frame_rejected():
    """Verify malformed hexadecimal frames are rejected.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    for candidate in ("", "00", "zz"):
        with pytest.raises(ValueError):
            crypto.open_field_frame(candidate)
