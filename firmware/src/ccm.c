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
// File:    ccm.c
// Desc:    Implements AES-CCM authenticated encryption over the AES-128 core.
// Created: 2026

#include "ccm.h"

#include <string.h>

/**
 * @brief Build the B0 control byte for the CCM flags field.
 *
 * @param has_ad True when associated data is present.
 * @return uint8_t B0 control byte.
 */
static uint8_t ccm_b0_flags(bool has_ad) {
    return (uint8_t)((has_ad ? 0x40u : 0x00u) | 0x38u | 0x01u);
}

/**
 * @brief Build the B0 block that seeds the CCM CBC-MAC.
 *
 * @param b0 Pointer to the sixteen-byte B0 output block.
 * @param nonce Pointer to the 13-byte nonce.
 * @param has_ad True when associated data is present.
 * @param msg_len Plaintext length in bytes.
 * @return void
 */
static void ccm_build_b0(uint8_t b0[16], const uint8_t nonce[13], bool has_ad,
                         size_t msg_len) {
    memset(b0, 0, 16u);
    b0[0] = ccm_b0_flags(has_ad);
    memcpy(b0 + 1, nonce, 13u);
    b0[14] = (uint8_t)(msg_len >> 8);
    b0[15] = (uint8_t)(msg_len & 0xffu);
}

/**
 * @brief Encrypt one CCM counter block into a keystream block.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param nonce Pointer to the 13-byte nonce.
 * @param counter Counter value for the block.
 * @param out Pointer to the sixteen-byte keystream output block.
 * @return void
 */
static void ccm_ctr_block(const aes_ctx_t *ctx, const uint8_t nonce[13],
                          uint16_t counter, uint8_t out[16]) {
    uint8_t a[16];
    a[0] = 0x01u;
    memcpy(a + 1, nonce, 13u);
    a[14] = (uint8_t)(counter >> 8);
    a[15] = (uint8_t)(counter & 0xffu);
    aes128_encrypt_block(ctx, a, out);
}

/**
 * @brief XOR a buffer with the CCM keystream starting at counter one.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param nonce Pointer to the 13-byte nonce.
 * @param in Pointer to the input bytes.
 * @param len Number of input bytes.
 * @param out Pointer to the output bytes.
 * @return void
 */
static void ccm_ctr_xor(const aes_ctx_t *ctx, const uint8_t nonce[13],
                        const uint8_t *in, size_t len, uint8_t *out) {
    uint16_t ctr = 1u;
    for (size_t off = 0u; off < len; off += 16u) {
        uint8_t ks[16];
        size_t n = (len - off < 16u) ? (len - off) : 16u;
        ccm_ctr_block(ctx, nonce, ctr, ks);
        for (size_t i = 0u; i < n; ++i) {
            out[off + i] = (uint8_t)(in[off + i] ^ ks[i]);
        }
        ctr++;
    }
}

/**
 * @brief XOR one sixteen-byte block into the running CBC-MAC value.
 *
 * @param dst Pointer to the running MAC block.
 * @param src Pointer to the block to fold in.
 * @return void
 */
static void ccm_xor_block(uint8_t *dst, const uint8_t *src) {
    for (int i = 0; i < 16; ++i) {
        dst[i] ^= src[i];
    }
}

/**
 * @brief Fold a zero-padded byte buffer into the running CBC-MAC.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param mac Pointer to the running MAC block.
 * @param data Pointer to the data bytes.
 * @param len Number of data bytes.
 * @return void
 */
static void ccm_mac_update(const aes_ctx_t *ctx, uint8_t mac[16],
                           const uint8_t *data, size_t len) {
    for (size_t off = 0u; off < len; off += 16u) {
        uint8_t blk[16];
        size_t n = (len - off < 16u) ? (len - off) : 16u;
        memset(blk, 0, 16u);
        memcpy(blk, data + off, n);
        ccm_xor_block(mac, blk);
        aes128_encrypt_block(ctx, mac, mac);
    }
}

/**
 * @brief Fold the length-prefixed associated data into the CBC-MAC.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param mac Pointer to the running MAC block.
 * @param ad Pointer to the associated data.
 * @param ad_len Number of associated-data bytes.
 * @return void
 */
static void ccm_mac_aad(const aes_ctx_t *ctx, uint8_t mac[16],
                        const uint8_t *ad, size_t ad_len) {
    uint8_t buf[CCM_MAX_AD + 2u];
    if (ad_len == 0u) {
        return;
    }
    buf[0] = (uint8_t)(ad_len >> 8);
    buf[1] = (uint8_t)(ad_len & 0xffu);
    memcpy(buf + 2, ad, ad_len);
    ccm_mac_update(ctx, mac, buf, ad_len + 2u);
}

/**
 * @brief Compute the raw CCM CBC-MAC over AAD and plaintext.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param nonce Pointer to the 13-byte nonce.
 * @param ad Pointer to the associated data.
 * @param ad_len Number of associated-data bytes.
 * @param pt Pointer to the plaintext bytes.
 * @param pt_len Number of plaintext bytes.
 * @param mac Pointer to the sixteen-byte MAC output block.
 * @return void
 */
static void ccm_mac(const aes_ctx_t *ctx, const uint8_t nonce[13],
                    const uint8_t *ad, size_t ad_len, const uint8_t *pt,
                    size_t pt_len, uint8_t mac[16]) {
    uint8_t b0[16];
    ccm_build_b0(b0, nonce, ad_len > 0u, pt_len);
    aes128_encrypt_block(ctx, b0, mac);
    ccm_mac_aad(ctx, mac, ad, ad_len);
    ccm_mac_update(ctx, mac, pt, pt_len);
}

/**
 * @brief Produce the CCM tag by masking the MAC with counter block zero.
 *
 * @param ctx Pointer to an expanded AES-128 key schedule.
 * @param nonce Pointer to the 13-byte nonce.
 * @param mac Pointer to the sixteen-byte CBC-MAC block.
 * @param tag Pointer to the sixteen-byte tag output block.
 * @return void
 */
static void ccm_finish_tag(const aes_ctx_t *ctx, const uint8_t nonce[13],
                           const uint8_t mac[16], uint8_t tag[16]) {
    uint8_t s0[16];
    ccm_ctr_block(ctx, nonce, 0u, s0);
    for (int i = 0; i < 16; ++i) {
        tag[i] = (uint8_t)(mac[i] ^ s0[i]);
    }
}

/**
 * @brief Compare two tags in constant time.
 *
 * @param a Pointer to the first tag.
 * @param b Pointer to the second tag.
 * @return bool true when the tags are equal.
 */
static bool ccm_tag_equal(const uint8_t a[16], const uint8_t b[16]) {
    uint8_t diff = 0u;
    for (int i = 0; i < 16; ++i) {
        diff |= (uint8_t)(a[i] ^ b[i]);
    }
    return diff == 0u;
}

bool ccm_seal(const uint8_t key[CCM_KEY_LEN], const uint8_t nonce[CCM_NONCE_LEN],
              const uint8_t *ad, size_t ad_len, const uint8_t *pt, size_t pt_len,
              uint8_t *ct, uint8_t tag[CCM_TAG_LEN]) {
    aes_ctx_t ctx;
    uint8_t mac[16];
    aes128_init(&ctx, key);
    ccm_mac(&ctx, nonce, ad, ad_len, pt, pt_len, mac);
    ccm_ctr_xor(&ctx, nonce, pt, pt_len, ct);
    ccm_finish_tag(&ctx, nonce, mac, tag);
    return true;
}

bool ccm_open(const uint8_t key[CCM_KEY_LEN], const uint8_t nonce[CCM_NONCE_LEN],
              const uint8_t *ad, size_t ad_len, const uint8_t *ct, size_t ct_len,
              const uint8_t tag[CCM_TAG_LEN], uint8_t *pt) {
    aes_ctx_t ctx;
    uint8_t mac[16];
    uint8_t expect[16];
    aes128_init(&ctx, key);
    ccm_ctr_xor(&ctx, nonce, ct, ct_len, pt);
    ccm_mac(&ctx, nonce, ad, ad_len, pt, ct_len, mac);
    ccm_finish_tag(&ctx, nonce, mac, expect);
    return ccm_tag_equal(expect, tag);
}
