/**
 * FILE: test_peripheral_and_crypto.c
 *
 * DESCRIPTION:
 * Native unit tests for the RP2350 Picokit Blink chase LED annunciator and
 * the AES-128, AES-CCM, and hex envelope security modules.
 *
 * BRIEF:
 * Peripheral and security module native test translation unit.
 *
 * AUTHOR: Kevin Thomas
 * DATE: September 2026
 */

#include "mock/pico/stdlib.h"
#include "harness.h"
#include "mock/pico/time.h"
#include "mock/hardware/gpio.h"
#include "picokit_30_status_pages.h"
#include "status_led.h"
#include "aes.h"
#include "ccm.h"
#include "envelope.h"
#include <string.h>

#include "../src/status_led.c"
#include "../src/aes.c"
#include "../src/ccm.c"
#include "../src/envelope.c"

/**
 * @brief FIPS-197 AES-128 key bytes zero through fifteen.
 */
static const uint8_t s_aes_key[AES_KEY_LEN] = {
    0x00u, 0x01u, 0x02u, 0x03u, 0x04u, 0x05u, 0x06u, 0x07u,
    0x08u, 0x09u, 0x0Au, 0x0Bu, 0x0Cu, 0x0Du, 0x0Eu, 0x0Fu,
};

/**
 * @brief FIPS-197 AES-128 plaintext block.
 */
static const uint8_t s_aes_pt[AES_BLOCK_LEN] = {
    0x00u, 0x11u, 0x22u, 0x33u, 0x44u, 0x55u, 0x66u, 0x77u,
    0x88u, 0x99u, 0xAAu, 0xBBu, 0xCCu, 0xDDu, 0xEEu, 0xFFu,
};

/**
 * @brief FIPS-197 AES-128 ciphertext block.
 */
static const uint8_t s_aes_ct[AES_BLOCK_LEN] = {
    0x69u, 0xC4u, 0xE0u, 0xD8u, 0x6Au, 0x7Bu, 0x04u, 0x30u,
    0xD8u, 0xCDu, 0xB7u, 0x80u, 0x70u, 0xB4u, 0xC5u, 0x5Au,
};

/**
 * @brief AES-CCM nonce bytes zero through twelve.
 */
static const uint8_t s_ccm_nonce[CCM_NONCE_LEN] = {
    0x00u, 0x01u, 0x02u, 0x03u, 0x04u, 0x05u, 0x06u, 0x07u,
    0x08u, 0x09u, 0x0Au, 0x0Bu, 0x0Cu,
};

/**
 * @brief Single-byte associated data used by the CCM tests.
 */
static const uint8_t s_ccm_ad[1] = {0x01u};

/**
 * @brief Plaintext body used by the CCM tests.
 */
static const char s_ccm_pt[] = "{\"n\":1,\"s\":0,\"b\":2}";

/**
 * @brief Expected CCM ciphertext for the AES-CCM known-answer vector.
 */
static const uint8_t s_ccm_ct[19] = {
    0x6Du, 0x16u, 0xDAu, 0xAAu, 0x69u, 0x38u, 0xD6u, 0xA0u, 0x29u,
    0xB5u, 0x09u, 0x97u, 0xB1u, 0x16u, 0x7Cu, 0xFAu, 0xD9u, 0x32u,
    0x79u,
};

/**
 * @brief Expected CCM tag for the AES-CCM known-answer vector.
 */
static const uint8_t s_ccm_tag[CCM_TAG_LEN] = {
    0x49u, 0x12u, 0xD4u, 0x74u, 0x1Fu, 0xD1u, 0x55u, 0x2Fu,
    0x6Du, 0x5Eu, 0x7Du, 0x64u, 0x3Cu, 0xCAu, 0x86u, 0x0Au,
};

/**
 * @brief LAB-ONLY AES-128 field key used by the envelope tests.
 */
static const uint8_t s_env_key[ENVELOPE_KEY_LEN] = {
    0x70u, 0x69u, 0x63u, 0x6Fu, 0x6Bu, 0x69u, 0x74u, 0x2Du,
    0x6Cu, 0x61u, 0x62u, 0x2Du, 0x6Bu, 0x65u, 0x79u, 0x21u,
};

/**
 * @brief Fixed envelope nonce bytes zero through twelve.
 */
static const uint8_t s_env_nonce[ENVELOPE_NONCE_LEN] = {
    0x00u, 0x01u, 0x02u, 0x03u, 0x04u, 0x05u, 0x06u, 0x07u,
    0x08u, 0x09u, 0x0Au, 0x0Bu, 0x0Cu,
};

/**
 * @brief Plaintext body used by the envelope known-answer vector.
 */
static const char s_env_pt[] = "{\"n\":1,\"s\":12,\"b\":2}";

/**
 * @brief Expected lowercase hex envelope for the known-answer vector.
 */
static const char s_env_hex[] =
    "000102030405060708090a0b0c0e6ca7c6174478c02db75a9cee8baff779"
    "28905d7e28494f2f14250b7d557f81ca3d84bc";

/**
 * @brief Reset the peripheral and crypto host mocks.
 *
 * @param void No parameters.
 * @return void
 */
static void reset_pc(void) {
    mock_timer_reset();
    mock_gpio_reset();
    mock_rand_reset();
}

/**
 * @brief Assert exactly one annunciator lamp is lit.
 *
 * @param red Expected red lamp level.
 * @param yellow Expected yellow lamp level.
 * @param green Expected green lamp level.
 * @return void
 */
static void assert_lamps(int red, int yellow, int green) {
    TEST_ASSERT_EQUAL_INT(red, mock_gpio_get(PICOKIT_30_STATUS_PAGES_RED_LED_PIN));
    TEST_ASSERT_EQUAL_INT(yellow,
                          mock_gpio_get(PICOKIT_30_STATUS_PAGES_YELLOW_LED_PIN));
    TEST_ASSERT_EQUAL_INT(green,
                          mock_gpio_get(PICOKIT_30_STATUS_PAGES_GREEN_LED_PIN));
}

/**
 * @brief Uppercase the hexadecimal letters of a string in place.
 *
 * @param s Pointer to the NUL-terminated string to uppercase.
 * @return void
 */
static void upper_hex(char *s) {
    for (size_t i = 0u; s[i] != '\0'; ++i) {
        if (s[i] >= 'a' && s[i] <= 'f') { s[i] = (char)(s[i] - 32); }
    }
}

/**
 * @brief Seal the shared CCM test plaintext into ciphertext and tag.
 *
 * @param ct Pointer to the ciphertext output buffer.
 * @param tag Pointer to the tag output buffer.
 * @return size_t Plaintext length that was sealed.
 */
static size_t seal_ccm(uint8_t *ct, uint8_t *tag) {
    size_t len = sizeof(s_ccm_pt) - 1u;
    ccm_seal(s_aes_key, s_ccm_nonce, s_ccm_ad, 1u, (const uint8_t *)s_ccm_pt,
             len, ct, tag);
    return len;
}

/**
 * @brief Seal the shared envelope test plaintext into a hex string.
 *
 * @param hex Pointer to the hex output buffer.
 * @param hex_len Capacity of the hex output buffer in bytes.
 * @return void
 */
static void seal_env(char *hex, size_t hex_len) {
    envelope_seal_hex(s_env_key, s_env_nonce, s_ccm_ad, 1u,
                      (const uint8_t *)s_env_pt, sizeof(s_env_pt) - 1u, hex,
                      hex_len);
}

/**
 * @brief Verify chase LED initialization configures the pins.
 *
 * @param void No parameters.
 * @return void
 */
static void test_status_led_init(void) {
    reset_pc();
    TEST_ASSERT_TRUE(status_led_init());
    TEST_ASSERT_TRUE(s_mock_gpio_dirs[PICOKIT_30_STATUS_PAGES_RED_LED_PIN]);
    TEST_ASSERT_TRUE(s_mock_gpio_dirs[PICOKIT_30_STATUS_PAGES_YELLOW_LED_PIN]);
    TEST_ASSERT_TRUE(s_mock_gpio_dirs[PICOKIT_30_STATUS_PAGES_GREEN_LED_PIN]);
}

/**
 * @brief Verify the red chase step lights only the red lamp.
 *
 * @param void No parameters.
 * @return void
 */
static void test_status_led_red(void) {
    reset_pc();
    status_led_init();
    status_led_show_step(STATUS_LED_STEP_RED);
    assert_lamps(1, 0, 0);
}

/**
 * @brief Verify the yellow chase step lights only the yellow lamp.
 *
 * @param void No parameters.
 * @return void
 */
static void test_status_led_yellow(void) {
    reset_pc();
    status_led_init();
    status_led_show_step(STATUS_LED_STEP_YELLOW);
    assert_lamps(0, 1, 0);
}

/**
 * @brief Verify the green chase step lights only the green lamp.
 *
 * @param void No parameters.
 * @return void
 */
static void test_status_led_green(void) {
    reset_pc();
    status_led_init();
    status_led_show_step(STATUS_LED_STEP_GREEN);
    assert_lamps(0, 0, 1);
}

/**
 * @brief Verify a step beyond the cycle wraps back to red.
 *
 * @param void No parameters.
 * @return void
 */
static void test_status_led_wrap(void) {
    reset_pc();
    status_led_init();
    status_led_show_step(STATUS_LED_STEP_COUNT);
    assert_lamps(1, 0, 0);
}

/**
 * @brief Verify the FIPS-197 AES-128 known-answer vector.
 *
 * @param void No parameters.
 * @return void
 */
static void test_aes128_known_vector(void) {
    aes_ctx_t ctx;
    uint8_t out[AES_BLOCK_LEN];
    aes128_init(&ctx, s_aes_key);
    aes128_encrypt_block(&ctx, s_aes_pt, out);
    TEST_ASSERT_EQUAL_MEMORY(s_aes_ct, out, AES_BLOCK_LEN);
}

/**
 * @brief Verify the AES-CCM known-answer ciphertext and tag.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_known_vector(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    ccm_seal(s_aes_key, s_ccm_nonce, s_ccm_ad, 1u, (const uint8_t *)s_ccm_pt,
             sizeof(s_ccm_pt) - 1u, ct, tag);
    TEST_ASSERT_EQUAL_MEMORY(s_ccm_ct, ct, sizeof(ct));
    TEST_ASSERT_EQUAL_MEMORY(s_ccm_tag, tag, CCM_TAG_LEN);
}

/**
 * @brief Verify a sealed CCM frame opens back to its plaintext.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_roundtrip(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    uint8_t out[sizeof(s_ccm_pt) - 1u];
    size_t len = seal_ccm(ct, tag);
    TEST_ASSERT_TRUE(ccm_open(s_aes_key, s_ccm_nonce, s_ccm_ad, 1u, ct, len, tag, out));
    TEST_ASSERT_EQUAL_MEMORY(s_ccm_pt, out, len);
}

/**
 * @brief Verify a tampered CCM tag is rejected.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_tamper_tag(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    uint8_t out[sizeof(s_ccm_pt) - 1u];
    size_t len = seal_ccm(ct, tag);
    tag[0] ^= 0x01u;
    TEST_ASSERT_FALSE(ccm_open(s_aes_key, s_ccm_nonce, s_ccm_ad, 1u, ct, len, tag, out));
}

/**
 * @brief Verify tampered CCM ciphertext is rejected.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_tamper_ct(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    uint8_t out[sizeof(s_ccm_pt) - 1u];
    size_t len = seal_ccm(ct, tag);
    ct[0] ^= 0x01u;
    TEST_ASSERT_FALSE(ccm_open(s_aes_key, s_ccm_nonce, s_ccm_ad, 1u, ct, len, tag, out));
}

/**
 * @brief Verify a changed CCM associated data is rejected.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_tamper_ad(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    uint8_t out[sizeof(s_ccm_pt) - 1u];
    const uint8_t bad[1] = {0x02u};
    size_t len = seal_ccm(ct, tag);
    TEST_ASSERT_FALSE(ccm_open(s_aes_key, s_ccm_nonce, bad, 1u, ct, len, tag, out));
}

/**
 * @brief Verify CCM seals and opens a frame with no associated data.
 *
 * @param void No parameters.
 * @return void
 */
static void test_ccm_no_ad(void) {
    uint8_t ct[sizeof(s_ccm_pt) - 1u];
    uint8_t tag[CCM_TAG_LEN];
    uint8_t out[sizeof(s_ccm_pt) - 1u];
    size_t len = sizeof(s_ccm_pt) - 1u;
    ccm_seal(s_aes_key, s_ccm_nonce, NULL, 0u, (const uint8_t *)s_ccm_pt,
             len, ct, tag);
    TEST_ASSERT_TRUE(ccm_open(s_aes_key, s_ccm_nonce, NULL, 0u, ct, len, tag, out));
    TEST_ASSERT_EQUAL_MEMORY(s_ccm_pt, out, len);
}

/**
 * @brief Verify the mock random source yields a deterministic nonce.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_nonce(void) {
    uint8_t nonce[ENVELOPE_NONCE_LEN];
    const uint8_t expect[ENVELOPE_NONCE_LEN] = {
        0u, 0u, 0u, 0u, 1u, 0u, 0u, 0u, 2u, 0u, 0u, 0u, 3u,
    };
    reset_pc();
    envelope_fill_nonce(nonce);
    TEST_ASSERT_EQUAL_MEMORY(expect, nonce, ENVELOPE_NONCE_LEN);
}

/**
 * @brief Verify the envelope known-answer hex string.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_known_vector(void) {
    char hex[ENVELOPE_MAX_HEX_LEN];
    seal_env(hex, sizeof(hex));
    TEST_ASSERT_EQUAL_STRING(s_env_hex, hex);
}

/**
 * @brief Verify a sealed envelope opens back to its plaintext.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_roundtrip(void) {
    char hex[ENVELOPE_MAX_HEX_LEN];
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    seal_env(hex, sizeof(hex));
    TEST_ASSERT_TRUE(envelope_open_hex(s_env_key, s_ccm_ad, 1u, hex, out, sizeof(out), &out_len));
    TEST_ASSERT_EQUAL_MEMORY(s_env_pt, out, out_len);
}

/**
 * @brief Verify the envelope seal rejects oversized and short buffers.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_seal_rejects(void) {
    char hex[ENVELOPE_MAX_HEX_LEN];
    uint8_t big[ENVELOPE_MAX_PLAINTEXT + 1u] = {0u};
    TEST_ASSERT_FALSE(envelope_seal_hex(s_env_key, s_env_nonce, NULL, 0u, big,
                                        sizeof(big), hex, sizeof(hex)));
    TEST_ASSERT_FALSE(envelope_seal_hex(s_env_key, s_env_nonce, NULL, 0u,
                                        (const uint8_t *)s_env_pt,
                                        sizeof(s_env_pt) - 1u, hex, 4u));
}

/**
 * @brief Verify the envelope open rejects malformed and short input.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_open_rejects(void) {
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, NULL, 0u, "zz", out,
                                        sizeof(out), &out_len));
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, NULL, 0u, "00", out,
                                        sizeof(out), &out_len));
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, NULL, 0u, s_env_hex, out,
                                        1u, &out_len));
}

/**
 * @brief Verify the envelope open rejects a long invalid hex string.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_bad_hex(void) {
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    char bad[63];
    memset(bad, 'z', 62u);
    bad[62] = '\0';
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, NULL, 0u, bad, out,
                                        sizeof(out), &out_len));
}

/**
 * @brief Verify the envelope open rejects an oversized hex string.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_too_long(void) {
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    char big[161];
    memset(big, '0', 160u);
    big[160] = '\0';
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, NULL, 0u, big, out,
                                        sizeof(out), &out_len));
}

/**
 * @brief Verify the envelope open rejects a too-small plaintext buffer.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_small_out(void) {
    uint8_t out[1];
    size_t out_len = 0u;
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, s_ccm_ad, 1u, s_env_hex, out,
                                        sizeof(out), &out_len));
}

/**
 * @brief Verify a tampered envelope fails authentication.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_tamper(void) {
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    char tampered[ENVELOPE_MAX_HEX_LEN];
    strcpy(tampered, s_env_hex);
    tampered[strlen(tampered) - 1u] = '0';
    TEST_ASSERT_FALSE(envelope_open_hex(s_env_key, s_ccm_ad, 1u, tampered, out, sizeof(out), &out_len));
}

/**
 * @brief Verify the envelope open accepts an uppercase hex string.
 *
 * @param void No parameters.
 * @return void
 */
static void test_envelope_uppercase(void) {
    uint8_t out[ENVELOPE_MAX_PLAINTEXT];
    size_t out_len = 0u;
    char upper[ENVELOPE_MAX_HEX_LEN];
    strcpy(upper, s_env_hex);
    upper_hex(upper);
    TEST_ASSERT_TRUE(envelope_open_hex(s_env_key, s_ccm_ad, 1u, upper, out,
                                       sizeof(out), &out_len));
}

/**
 * @brief Run the chase LED annunciator tests.
 *
 * @param void No parameters.
 * @return void
 */
static void run_led_tests(void) {
    RUN_TEST(test_status_led_init);
    RUN_TEST(test_status_led_red);
    RUN_TEST(test_status_led_yellow);
    RUN_TEST(test_status_led_green);
    RUN_TEST(test_status_led_wrap);
}

/**
 * @brief Run the AES-128 block cipher tests.
 *
 * @param void No parameters.
 * @return void
 */
static void run_aes_tests(void) {
    RUN_TEST(test_aes128_known_vector);
}

/**
 * @brief Run the AES-CCM authenticated encryption tests.
 *
 * @param void No parameters.
 * @return void
 */
static void run_ccm_tests(void) {
    RUN_TEST(test_ccm_known_vector);
    RUN_TEST(test_ccm_roundtrip);
    RUN_TEST(test_ccm_tamper_tag);
    RUN_TEST(test_ccm_tamper_ct);
    RUN_TEST(test_ccm_tamper_ad);
    RUN_TEST(test_ccm_no_ad);
}

/**
 * @brief Run the hex envelope rejection tests.
 *
 * @param void No parameters.
 * @return void
 */
static void run_envelope_reject_tests(void) {
    RUN_TEST(test_envelope_bad_hex);
    RUN_TEST(test_envelope_too_long);
    RUN_TEST(test_envelope_small_out);
    RUN_TEST(test_envelope_tamper);
    RUN_TEST(test_envelope_uppercase);
}

/**
 * @brief Run the hex envelope codec tests.
 *
 * @param void No parameters.
 * @return void
 */
static void run_envelope_tests(void) {
    RUN_TEST(test_envelope_nonce);
    RUN_TEST(test_envelope_known_vector);
    RUN_TEST(test_envelope_roundtrip);
    RUN_TEST(test_envelope_seal_rejects);
    RUN_TEST(test_envelope_open_rejects);
    run_envelope_reject_tests();
}

void run_peripheral_and_crypto_tests(void) {
    run_led_tests();
    run_aes_tests();
    run_ccm_tests();
    run_envelope_tests();
}
