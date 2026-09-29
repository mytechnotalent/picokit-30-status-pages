---
name: iot-readme-standard
description: Use ONLY when writing, editing, or reviewing the top-level README.md of a picokit project. Enforces the exact repository README pattern: banner image, blank line, <br>, the two FREE course links, <br>, the H1 title block, the framed legal disclaimer, and the exact bottom <br> / Next / <br> / License pattern with the MIT link. No exceptions and no variation between projects.
---

# IoT README standard (picokit)

The README.md of every project in the series is byte-for-byte the same shape.
Only the title, the subtitle, the series line, the body, and the Next target
change. The `<br>` placement, the course links, the disclaimer, and the license
block are fixed. There are no exceptions.

## Exact top block

```
![<repo>](https://raw.githubusercontent.com/mytechnotalent/<repo>/main/<repo>.png)

<br>

## FREE Reverse Engineering Self-Study Course [HERE](https://github.com/mytechnotalent/reverse-engineering)
## FREE Embedded Hacking Course [HERE](https://github.com/mytechnotalent/Embedded-Hacking)

<br>

# <TITLE>

### <SUBTITLE>
#### Lesson <N> of the Picokit Series

<br>

***
**LEGAL DISCLAIMER:**
...exact disclaimer text...
***

<br>
<br>
```

Rules:
- The image URL is the raw GitHub URL for `<repo>.png` at the repository root.
- `<br>` appears on its own line, never inline, never with surrounding spaces.
- The two course links are adjacent lines with no blank line between them.
- The disclaimer block is the exact text in `README.template.md` in this skill.

## Exact bottom block

The README ends with exactly this, and nothing after the MIT link:

```
<br>

# Next
[<NEXT TITLE>](<NEXT URL>)

<br>

# License
[MIT License](https://github.com/mytechnotalent/<repo>/blob/main/LICENSE)
```

## Body

Between the disclaimer and the bottom block, the body is free-form but every
section is separated by a `<br>` line, matching the 01_ project style.

## Verify

Run the bundled validator from the repository root. Exit 0 is clean; any output
is a failure and must be fixed before the change is complete.

```bash
python3 .opencode/skill/iot-readme-standard/validate_readme.py
```
