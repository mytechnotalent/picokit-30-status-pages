![picokit-30-status-pages](https://raw.githubusercontent.com/mytechnotalent/picokit-30-status-pages/main/picokit-30-status-pages.png)

<br>

## FREE Reverse Engineering Self-Study Course [HERE](https://github.com/mytechnotalent/reverse-engineering)
## FREE Embedded Hacking Course [HERE](https://github.com/mytechnotalent/Embedded-Hacking)

<br>

# PICOKIT-30 STATUS PAGES

### Button and Remote Status Pages on the 1602 I2C LCD and Authenticated Heartbeat
#### Lesson 30 of the Picokit Series

<br>

***
**LEGAL DISCLAIMER:**
The information, tools, and code provided in this repository and course are strictly for educational, research, and defensive purposes only.

You are explicitly prohibited from using any materials contained herein to access, test, modify, or exploit any device, network, or system that you do not own 100% or for which you do not have explicit, documented, and legally binding authorization to interact with.

By using this repository and course, you acknowledge and agree that:

1. Any illegal, unauthorized, or malicious use of this information is solely your responsibility.
2. The author(s) and contributor(s) of this repository and course shall not be held liable for any damages, legal repercussions, criminal charges, or unauthorized actions resulting from the use, misuse, or abuse of the contents herein.
3. You will comply with all applicable local, state, national, and international laws regarding cybersecurity and computer fraud.

**IF YOU DO NOT AGREE WITH THESE TERMS, DO NOT USE THIS REPOSITORY AND COURSE.**
***

<br>
<br>

## Overview

The thirtieth Picokit lesson. The node pages through several live status screens
on the 1602 I2C LCD using either the GP15 push button or the NEC infrared
remote. The button advances to the next page, and the remote can step forward
or back. Every five seconds the node transmits an authenticated heartbeat over
LoRa to a Python gateway that logs and displays the current page. It combines
the local button and the wireless remote into one paged status panel.

<br>

## What it teaches

- Servicing two independent page inputs in one poll loop.
- Debouncing the button and decoding the NEC remote side by side.
- Wrapping a bounded page index from either input.
- Reporting the active page in the authenticated heartbeat body.

<br>

## Hardware

| Peripheral | Pico 2 pin | Role |
| --- | --- | --- |
| Button | GP15 | local page input, active low |
| VS1838B IR | GP5 | remote page input |
| 1602 I2C LCD | GP2 SDA / GP3 SCL | live status pages |
| Red / Yellow / Green | GP16 / GP18 / GP17 | page indicator |
| Onboard LED | GP25 | heartbeat, one blink per transmit |
| RYLR998 | GP8 TX / GP9 RX | LoRa heartbeat |
| Debug Probe | SWCLK/SWDIO/GND, GP0/GP1 | SWD and the console |

<br>

## How it works

The node runs `monitor_step` in a loop. Every 100 ms it consumes one button
press and polls the VS1838B receiver. A button press advances the page, the
remote `0x45` advances it, and the remote `0x46` returns it, wrapping across
STATUS, SENSOR, and RADIO. It renders `PAGE n/3` and the page name to the 1602
LCD, and every 5 seconds it seals `{"n":30,"s":<seq>,"g":<page>}` with the
field key and sends it over LoRa. The gateway authenticates each frame and only
then parses it.

<br>

## Build and flash

```bash
cd firmware
cmake -S . -B build -G Ninja -DPICO_BOARD=pico2 -DPICO_PLATFORM=rp2350-arm-s
cmake --build build
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg \
  -c "program build/picokit_30_status_pages.elf verify reset exit"
```

<br>

## Watch the node

Open the console at 115200 and reset:

```text
BOOT
I2C scan:
  found 0x27
=== PICOKIT-30 STATUS PAGES // BUTTON + REMOTE + AUTHENTICATED HEARTBEAT ===
PAGE 2 SENSOR
PAGE 3 RADIO
PAGE 1 STATUS
RX from 0x0001, N bytes
```

<br>

## The gateway

```bash
cd gateway
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 listen.py --port /dev/cu.usbserial-A50285BI --hub 0001 --network 18 --db gateway.db
```

It prints `OK node=30 rssi=...` per authenticated heartbeat. The terminal
dashboard `python3 tui.py --db gateway.db` and the web dashboard
`python3 web/app.py --db gateway.db` show the same rows.

<br>

## Verify

```bash
python3 .opencode/skill/embedded-c-standard/audit_c_standard.py
python3 .opencode/skill/embedded-python-standard/audit_python_standard.py
python3 .opencode/skill/iot-readme-standard/validate_readme.py
python3 .opencode/skill/iot-banner-standard/validate_banner.py
python3 scripts/run_tests.py
python3 scripts/check_coverage.py
```

<br>

# Next
[picokit-31-thermostat](https://github.com/mytechnotalent/picokit-31-thermostat)

<br>

# License
[MIT License](https://github.com/mytechnotalent/picokit-30-status-pages/blob/main/LICENSE)
