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
// File:    monitor.h
// Desc:    Declares the LCD status page state machine paged by the button
//          or the infrared remote and paired with an authenticated
//          heartbeat.
// Created: 2026

#ifndef MONITOR_H
#define MONITOR_H

#include <stdbool.h>
#include <stdint.h>

/**
 * @brief Spacing between two button and infrared polls in milliseconds.
 */
#define MONITOR_POLL_INTERVAL_MS 100u

/**
 * @brief Onboard heartbeat LED on and off time in microseconds.
 */
#define MONITOR_HEARTBEAT_BLINK_US 50000u

/**
 * @brief Number of live status pages.
 */
#define MONITOR_PAGE_COUNT 3u

/**
 * @brief NEC command code that advances to the next status page.
 */
#define MONITOR_KEY_NEXT 0x45u

/**
 * @brief NEC command code that returns to the previous status page.
 */
#define MONITOR_KEY_PREV 0x46u

/**
 * @brief Initialize the LCD status page monitor state machine.
 *
 * Configures the onboard heartbeat LED, the menu button, the VS1838B
 * infrared receiver, the 1602 LCD, and the RYLR998 UART, derives the
 * field key, and resets the page, poll, and transmit timing.
 *
 * @param void No parameters.
 * @return bool true when all submodules initialized.
 */
bool monitor_init(void);

/**
 * @brief Clear the monitor-ready flag.
 *
 * Test and recovery hook that returns the state machine to the
 * uninitialized policy state.
 *
 * @param void No parameters.
 * @return void
 */
void monitor_deinit(void);

/**
 * @brief Execute one monitor state-machine tick.
 *
 * Pages the status screens on a button press or an infrared next or
 * previous key, renders the current page to the 1602 LCD, transmits the
 * authenticated heartbeat on the telemetry interval, and pumps inbound
 * +RCV lines.
 *
 * @param void No parameters.
 * @return bool true when the tick completed without a policy error.
 */
bool monitor_step(void);

#endif // MONITOR_H
