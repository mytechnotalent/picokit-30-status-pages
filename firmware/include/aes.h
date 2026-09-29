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
// File:    aes.h
// Desc:    Declares the AES-128 block cipher used by the CCM codec.
// Created: 2026

#ifndef AES_H
#define AES_H

#include <stdint.h>

/** @brief AES block size in bytes. */
#define AES_BLOCK_LEN 16u

/** @brief AES-128 key size in bytes. */
#define AES_KEY_LEN 16u

/**
 * @brief Expanded AES-128 key schedule.
 */
typedef struct {
    uint8_t round_key[176];
} aes_ctx_t;

/**
 * @brief Expand a 16-byte AES-128 key into the round-key schedule.
 *
 * @param ctx Pointer to the key schedule output context.
 * @param key Pointer to the 16-byte AES-128 key.
 * @return void
 */
void aes128_init(aes_ctx_t *ctx, const uint8_t key[AES_KEY_LEN]);

/**
 * @brief Encrypt one 16-byte block with AES-128.
 *
 * @param ctx Pointer to an expanded key schedule.
 * @param in Pointer to the 16-byte plaintext block.
 * @param out Pointer to the 16-byte ciphertext output block.
 * @return void
 */
void aes128_encrypt_block(const aes_ctx_t *ctx, const uint8_t in[AES_BLOCK_LEN],
                          uint8_t out[AES_BLOCK_LEN]);

#endif // AES_H
