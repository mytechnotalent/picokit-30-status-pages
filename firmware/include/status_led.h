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
// File:    status_led.h
// Desc:    Declares the red, yellow, and green LED chase annunciator.
// Created: 2026

#ifndef STATUS_LED_H
#define STATUS_LED_H

#include <stdbool.h>
#include <stdint.h>

/**
 * @brief Chase step that lights the red LED.
 */
#define STATUS_LED_STEP_RED 0u

/**
 * @brief Chase step that lights the yellow LED.
 */
#define STATUS_LED_STEP_YELLOW 1u

/**
 * @brief Chase step that lights the green LED.
 */
#define STATUS_LED_STEP_GREEN 2u

/**
 * @brief Number of steps in one full chase cycle.
 */
#define STATUS_LED_STEP_COUNT 3u

/**
 * @brief Initialize the tri-color chase LED GPIO pins.
 *
 * Configures the red, yellow, and green annunciator pins as outputs and
 * leaves every LED dark.
 *
 * @param void No parameters.
 * @return bool true when initialization completed.
 */
bool status_led_init(void);

/**
 * @brief Light exactly one chase lamp for the current step.
 *
 * @param step Chase step index, reduced modulo STATUS_LED_STEP_COUNT.
 * @return void
 */
void status_led_show_step(uint8_t step);

#endif // STATUS_LED_H
