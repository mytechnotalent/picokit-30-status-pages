// MIT License
//
// Copyright (c) 2026 Kevin Thomas
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//
// Author:  Kevin Thomas
// Email:   kevin@mytechnotalent.com
// GitHub:  https://github.com/mytechnotalent/picokit-30-status-pages
// File:    ccm.h
// Desc:    Declares the AES-CCM authenticated encryption codec.
// Created: 2026

#ifndef CCM_H
#define CCM_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "aes.h"

/** @brief AES-CCM key size in bytes. */
#define CCM_KEY_LEN 16u

/** @brief AES-CCM nonce size in bytes. */
#define CCM_NONCE_LEN 13u

/** @brief AES-CCM authentication tag size in bytes. */
#define CCM_TAG_LEN 16u

/** @brief Maximum associated-data length accepted by the codec. */
#define CCM_MAX_AD 16u

/**
 * @brief Seal a plaintext with AES-CCM authenticated encryption.
 *
 * @param key Pointer to the 16-byte AES-128 key.
 * @param nonce Pointer to the 13-byte nonce.
 * @param ad Pointer to the associated data.
 * @param ad_len Number of associated-data bytes.
 * @param pt Pointer to the plaintext bytes.
 * @param pt_len Number of plaintext bytes.
 * @param ct Pointer to the ciphertext output buffer.
 * @param tag Pointer to the 16-byte tag output buffer.
 * @return bool true when the plaintext was sealed.
 */
bool ccm_seal(const uint8_t key[CCM_KEY_LEN], const uint8_t nonce[CCM_NONCE_LEN],
              const uint8_t *ad, size_t ad_len, const uint8_t *pt, size_t pt_len,
              uint8_t *ct, uint8_t tag[CCM_TAG_LEN]);

/**
 * @brief Open and authenticate an AES-CCM ciphertext.
 *
 * @param key Pointer to the 16-byte AES-128 key.
 * @param nonce Pointer to the 13-byte nonce.
 * @param ad Pointer to the associated data.
 * @param ad_len Number of associated-data bytes.
 * @param ct Pointer to the ciphertext bytes.
 * @param ct_len Number of ciphertext bytes.
 * @param tag Pointer to the 16-byte authentication tag.
 * @param pt Pointer to the plaintext output buffer.
 * @return bool true when the tag verified and plaintext was produced.
 */
bool ccm_open(const uint8_t key[CCM_KEY_LEN], const uint8_t nonce[CCM_NONCE_LEN],
              const uint8_t *ad, size_t ad_len, const uint8_t *ct, size_t ct_len,
              const uint8_t tag[CCM_TAG_LEN], uint8_t *pt);

#endif // CCM_H
