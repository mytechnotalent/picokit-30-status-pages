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
// File:    status_led.c
// Desc:    Implements the red, yellow, and green LED chase annunciator for
//          the three step Picokit Blink pattern.
// Created: 2026

#include "pico/stdlib.h"
#include "picokit_30_status_pages.h"
#include "status_led.h"
#include "hardware/gpio.h"
#include <stdbool.h>
#include <stdint.h>

/**
 * @brief Configure one chase GPIO as a dark output.
 *
 * @param pin GPIO pin number to configure.
 * @return void
 */
static void status_led_config_pin(uint pin) {
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_OUT);
    gpio_put(pin, 0);
}

bool status_led_init(void) {
    status_led_config_pin(PICOKIT_30_STATUS_PAGES_RED_LED_PIN);
    status_led_config_pin(PICOKIT_30_STATUS_PAGES_YELLOW_LED_PIN);
    status_led_config_pin(PICOKIT_30_STATUS_PAGES_GREEN_LED_PIN);
    return true;
}

void status_led_show_step(uint8_t step) {
    uint8_t index = (uint8_t)(step % STATUS_LED_STEP_COUNT);
    gpio_put(PICOKIT_30_STATUS_PAGES_RED_LED_PIN, index == STATUS_LED_STEP_RED);
    gpio_put(PICOKIT_30_STATUS_PAGES_YELLOW_LED_PIN, index == STATUS_LED_STEP_YELLOW);
    gpio_put(PICOKIT_30_STATUS_PAGES_GREEN_LED_PIN, index == STATUS_LED_STEP_GREEN);
}
