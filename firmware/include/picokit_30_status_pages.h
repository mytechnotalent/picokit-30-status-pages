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
// File:    picokit_30_status_pages.h
// Desc:    Declares the platform pin mapping, radio handle, and heartbeat
//          boundaries for the Picokit infrared keypad node.
// Created: 2026

#ifndef PICOKIT_30_STATUS_PAGES_H
#define PICOKIT_30_STATUS_PAGES_H

#include "hardware/uart.h"
#include "packet_artifact.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/**
 * @brief Onboard heartbeat LED GPIO pin number.
 *
 * The RP2350 Pico 2 onboard LED is connected to GPIO 25. It blinks once per
 * accepted keypad digit as a visible sign of life.
 */
#define PICOKIT_30_STATUS_PAGES_LED_PIN 25u

/**
 * @brief UART peripheral used by the RYLR998 transceiver.
 *
 * The RYLR998 connects to UART1 through the Pico 2 header. All AT command
 * traffic flows over this byte stream.
 */
#define PICOKIT_30_STATUS_PAGES_UART uart1

/**
 * @brief UART TX GPIO pin number to the RYLR998 RX input.
 */
#define PICOKIT_30_STATUS_PAGES_UART_TX 8u

/**
 * @brief UART RX GPIO pin number from the RYLR998 TX output.
 */
#define PICOKIT_30_STATUS_PAGES_UART_RX 9u

/**
 * @brief UART baud rate negotiated with the RYLR998.
 *
 * The RYLR998 ships with a 115200 baud default and must be matched on both
 * the edge device and the instructor gateway.
 */
#define PICOKIT_30_STATUS_PAGES_UART_BAUD 115200u

/**
 * @brief RYLR998 network identifier shared by all classroom radios.
 *
 * Every edge device and the instructor hub must program the same network
 * identifier or no frames are delivered over the air.
 */
#define PICOKIT_30_STATUS_PAGES_NETWORK_ID 18u

/**
 * @brief Fixed telemetry frame size in bytes.
 *
 * The JSON payload produced by the edge device is sealed into a hex envelope
 * before transmission over LoRa.
 */
#define PICOKIT_30_STATUS_PAGES_FRAME_SIZE PACKET_FRAME_SIZE

/**
 * @brief Minimum spacing between consecutive LoRa transmissions.
 *
 * Deliberately larger than the radio on-air time so the instructor hub sees
 * one authenticated heartbeat per edge device per slot.
 */
#define PICOKIT_30_STATUS_PAGES_TX_INTERVAL_MS PACKET_TX_INTERVAL_MS

/**
 * @brief Red keypad status LED GPIO pin number.
 */
#define PICOKIT_30_STATUS_PAGES_RED_LED_PIN 16u

/**
 * @brief Yellow keypad status LED GPIO pin number.
 */
#define PICOKIT_30_STATUS_PAGES_YELLOW_LED_PIN 18u

/**
 * @brief Green keypad status LED GPIO pin number.
 */
#define PICOKIT_30_STATUS_PAGES_GREEN_LED_PIN 17u

/**
 * @brief Infrared receiver GPIO pin number.
 *
 * The VS1838B demodulator output idles high and pulses low for each
 * mark, feeding the NEC decoder.
 */
#define PICOKIT_30_STATUS_PAGES_IR_PIN 5u

/**
 * @brief Operator push-button GPIO pin number.
 *
 * The tactile switch shorts this pin to ground when pressed and is read
 * as an input with the internal pull-up enabled.
 */
#define PICOKIT_30_STATUS_PAGES_BUTTON_PIN 15u

/**
 * @brief I2C peripheral used by the 1602 LCD backpack.
 *
 * The Pico 2 bus B (I2C1) drives the PCF8574 backpack on the display.
 */
#define PICOKIT_30_STATUS_PAGES_I2C i2c1

/**
 * @brief I2C SDA GPIO pin number.
 */
#define PICOKIT_30_STATUS_PAGES_I2C_SDA 2u

/**
 * @brief I2C SCL GPIO pin number.
 */
#define PICOKIT_30_STATUS_PAGES_I2C_SCL 3u

/**
 * @brief I2C bus clock rate in hertz.
 */
#define PICOKIT_30_STATUS_PAGES_I2C_BAUD 100000u

/**
 * @brief I2C address of the 1602 LCD PCF8574 backpack.
 *
 * Provisioned through the packet artifact as 0x27.
 */
#define PICOKIT_30_STATUS_PAGES_LCD_ADDR PACKET_LCD_I2C_ADDRESS

#endif // PICOKIT_30_STATUS_PAGES_H
