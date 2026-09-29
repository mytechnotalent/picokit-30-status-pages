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
// File:    field_secrets.h
// Desc:    LAB-ONLY shared AES-128 field key matching the Python instructor
//          gateway for the authenticated telemetry lab.
// Created: 2026

#ifndef FIELD_SECRETS_H
#define FIELD_SECRETS_H

#include <stdint.h>

/**
 * @brief LAB-ONLY shared AES-128 field key, the ASCII bytes
 * "picokit-lab-key!".
 *
 * WARNING: This value is committed for the classroom lab so the firmware
 * and the instructor gateway share one session key. Production firmware
 * MUST provision the key from one-time-programmable (OTP) memory at
 * manufacture and MUST NEVER embed a key in flash. Shipping this file
 * as-is is a lab convenience, not a secure deployment.
 */
#define FIELD_SECRET_KEY { 0x70, 0x69, 0x63, 0x6f, 0x6b, 0x69, 0x74, 0x2d, \
                           0x6c, 0x61, 0x62, 0x2d, 0x6b, 0x65, 0x79, 0x21 }

#endif // FIELD_SECRETS_H
