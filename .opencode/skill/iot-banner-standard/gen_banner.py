#!/usr/bin/env python3
"""Render a symmetric hacker-style repository banner from a banner.json spec.

Produces a 2400x2400 dark terminal-style PNG with an accent-tinted radial
background, a glowing centered title, a circular icon medallion, a terminal
block, data chips, category pills, and a dotted footer. Every project supplies
its own banner.json so the artwork is unique while the theme stays the same.

The composition is strictly symmetric about the vertical center line and every
element occupies its own fixed horizontal band, so nothing can overlap. Icon
radii are derived from a per-icon reach factor and clamped to the medallion, so
no glyph, ray, or arc can cross a frame. Every centered line of text is
auto-fitted: the letter tracking is reduced to zero first and then the font
size is reduced until the rendered width fits inside a safe inset, so no glyph
can ever cross the image bounds. Five distinct layouts and twenty vector icons
are available so the series has real variety. Run from the repository root;
exit zero on success.
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image
from PIL import ImageChops
from PIL import ImageDraw
from PIL import ImageFilter
from PIL import ImageFont

SIZE = 2400
MARGIN = 80
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FONT_BOLD = 1
FONT_REGULAR = 0

LAYOUTS = ("panel", "split", "terminal", "stat", "grid")
ICONS = (
    "thermo", "leaf", "drop", "led", "lcd", "servo", "button", "remote",
    "antenna", "lock", "shield", "bug", "chip", "key", "clock", "gauge",
    "wifi", "hash", "wave", "bell",
)

_ICON_REACH = {
    "thermo": 1.0, "leaf": 0.85, "drop": 1.0, "led": 1.16, "lcd": 1.0,
    "servo": 1.0, "button": 1.0, "remote": 1.1, "antenna": 1.8, "lock": 1.0,
    "shield": 1.0, "bug": 1.05, "chip": 1.0, "key": 1.0, "clock": 1.0,
    "gauge": 1.0, "wifi": 1.55, "hash": 1.0, "wave": 1.0, "bell": 1.0,
}

_PANEL_FILL = (0x0B, 0x10, 0x14)
_TERM_FILL = (0x08, 0x0B, 0x0E)
_CHIP_FILL = (0x0C, 0x10, 0x14)

_RECORDS = []


def _record(text, left, right, top, bottom, size, centered):
    """
    Remember one drawn text extent for overflow validation.

    Parameters
    ----------
    text : str
        The drawn text.
    left : float
        The left ink edge.
    right : float
        The right ink edge.
    top : float
        The top ink edge.
    bottom : float
        The bottom ink edge.
    size : int
        The font pixel size.
    centered : bool
        True when the line is centered on the canvas.

    Returns
    -------
    None
    """
    _RECORDS.append({"text": text, "left": left, "right": right,
                     "top": top, "bottom": bottom, "size": size,
                     "centered": centered})


@lru_cache(maxsize=None)
def _font(size, bold):
    """
    Load a Menlo face at the requested pixel size.

    Parameters
    ----------
    size : int
        The pixel size.
    bold : bool
        True for the bold face.

    Returns
    -------
    PIL.ImageFont.FreeTypeFont
        The loaded font.
    """
    index = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(FONT_PATH, size, index=index)


def _rgb(value):
    """
    Convert a hex color string to an RGB tuple.

    Parameters
    ----------
    value : str
        A hex color such as '#39FF88'.

    Returns
    -------
    tuple[int, int, int]
        The RGB components.
    """
    text = value.lstrip("#")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def _mix(first, second, ratio):
    """
    Blend two RGB colors.

    Parameters
    ----------
    first : tuple[int, int, int]
        The base color.
    second : tuple[int, int, int]
        The color to blend toward.
    ratio : float
        The blend fraction from 0.0 (all first) to 1.0 (all second).

    Returns
    -------
    tuple[int, int, int]
        The blended color.
    """
    return tuple(int(first[i] + (second[i] - first[i]) * ratio)
                 for i in range(3))


def _spaced_width(draw, text, font, tracking):
    """
    Measure the width of letter-spaced text.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    text : str
        The text to measure.
    font : PIL.ImageFont.FreeTypeFont
        The glyph font.
    tracking : int
        Extra pixels between glyphs.

    Returns
    -------
    float
        The total rendered width.
    """
    widths = [draw.textlength(ch, font=font) for ch in text]
    return sum(widths) + tracking * max(0, len(text) - 1)


def _spaced_text(draw, x, y, text, font, fill, tracking):
    """
    Draw letter-spaced text and return the end x position.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    x : float
        The starting x position.
    y : float
        The top position.
    text : str
        The text to draw.
    font : PIL.ImageFont.FreeTypeFont
        The glyph font.
    fill : tuple
        The glyph color.
    tracking : int
        Extra pixels between glyphs.

    Returns
    -------
    float
        The x position after the last glyph.
    """
    cursor = x
    for ch in text:
        draw.text((cursor, y), ch, font=font, fill=fill)
        cursor += draw.textlength(ch, font=font) + tracking
    return cursor


def _fit(draw, text, max_size, max_track, max_w, bold):
    """
    Find the largest tracking and font size that keeps text inside max_w.

    Tracking is reduced to zero before the font size is reduced, matching the
    banner standard's auto-fit rule.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    text : str
        The text to fit.
    max_size : int
        The largest allowed pixel size.
    max_track : int
        The largest allowed tracking.
    max_w : float
        The maximum allowed rendered width.
    bold : bool
        True to use the bold face.

    Returns
    -------
    tuple
        The (font, tracking, width) that fits.
    """
    size, track = max_size, max_track
    while True:
        font = _font(size, bold)
        width = _spaced_width(draw, text, font, track)
        if width <= max_w or size <= 12:
            return font, track, width
        if track > 0:
            track -= 1
        else:
            size -= 1


def _center_fit(draw, cx, y, text, max_size, max_track, fill, bold,
                max_w=None):
    """
    Draw auto-fitted letter-spaced text centered on a horizontal axis.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    cx : float
        The center x position.
    y : float
        The top position.
    text : str
        The text to draw.
    max_size : int
        The largest allowed pixel size.
    max_track : int
        The largest allowed tracking.
    fill : tuple
        The glyph color.
    bold : bool
        True to use the bold face.
    max_w : float, optional
        The maximum rendered width.

    Returns
    -------
    None
    """
    if max_w is None:
        max_w = SIZE - 2 * MARGIN
    font, track, width = _fit(draw, text, max_size, max_track, max_w, bold)
    left = cx - width / 2
    _spaced_text(draw, left, y, text, font, fill, track)
    _record(text, left, left + width, y, y + font.size, font.size, True)


def _left_fit(draw, x, y, text, max_size, fill, max_w, bold):
    """
    Draw single-tracking text shrunk to fit a maximum width.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    x : float
        The left position.
    y : float
        The top position.
    text : str
        The text to draw.
    max_size : int
        The largest allowed pixel size.
    fill : tuple
        The glyph color.
    max_w : float
        The maximum rendered width.
    bold : bool
        True to use the bold face.

    Returns
    -------
    None
    """
    size = max_size
    while size > 12:
        font = _font(size, bold)
        if _spaced_width(draw, text, font, 0) <= max_w:
            break
        size -= 1
    font = _font(size, bold)
    width = _spaced_width(draw, text, font, 0)
    draw.text((x, y), text, font=font, fill=fill)
    _record(text, x, x + width, y, y + font.size, size, False)


def _gradient_text(img, cx, y, text, max_size, max_track, color_top,
                   color_bottom, bold, max_w=None):
    """
    Draw auto-fitted centered text filled with a vertical gradient.

    Parameters
    ----------
    img : PIL.Image.Image
        The destination image.
    cx : float
        The center x position.
    y : float
        The top position.
    text : str
        The text to draw.
    max_size : int
        The largest allowed pixel size.
    max_track : int
        The largest allowed tracking.
    color_top : tuple[int, int, int]
        The gradient color at the top of the glyphs.
    color_bottom : tuple[int, int, int]
        The gradient color at the bottom of the glyphs.
    bold : bool
        True to use the bold face.
    max_w : float, optional
        The maximum rendered width.

    Returns
    -------
    None
    """
    if max_w is None:
        max_w = SIZE - 2 * MARGIN
    draw = ImageDraw.Draw(img)
    font, track, width = _fit(draw, text, max_size, max_track, max_w, bold)
    left = cx - width / 2
    mask = Image.new("L", (SIZE, SIZE), 0)
    _spaced_text(ImageDraw.Draw(mask), left, y, text, font, 255, track)
    height = max(1, font.size)
    strip = Image.new("RGB", (1, height))
    for row in range(height):
        ratio = row / max(1, height - 1)
        strip.putpixel((0, row), _mix(color_top, color_bottom, ratio))
    grad = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    grad.paste(strip.resize((SIZE, height)), (0, int(y)))
    img.paste(grad, (0, 0), mask)
    _record(text, left, left + width, y, y + font.size, font.size, True)


def _radial_mask(radius):
    """
    Build a soft radial falloff mask.

    Parameters
    ----------
    radius : float
        The falloff radius in destination pixels.

    Returns
    -------
    PIL.Image.Image
        The single-channel radial mask.
    """
    small = Image.new("L", (128, 128), 0)
    pixels = small.load()
    for y in range(128):
        for x in range(128):
            dx = (x - 63.5) / 63.5 * radius
            dy = (y - 63.5) / 63.5 * radius
            dist = math.hypot(dx, dy) / radius
            pixels[x, y] = int(max(0.0, 1.0 - dist) ** 1.6 * 255)
    return small.resize((SIZE, SIZE), Image.BICUBIC)


def _vignette_mask():
    """
    Build a radial vignette mask.

    Parameters
    ----------
    None

    Returns
    -------
    PIL.Image.Image
        The single-channel vignette mask.
    """
    small = Image.new("L", (64, 64), 0)
    pixels = small.load()
    for y in range(64):
        for x in range(64):
            dist = (((x - 31.5) ** 2 + (y - 31.5) ** 2) ** 0.5) / 42.0
            pixels[x, y] = int(max(0.0, min(1.0, 1.0 - dist)) * 255)
    return small.resize((SIZE, SIZE), Image.BICUBIC)


def _background(spec):
    """
    Build the vignetted, accent-tinted dark background.

    Parameters
    ----------
    spec : dict
        The banner specification.

    Returns
    -------
    PIL.Image.Image
        The RGB background image.
    """
    base = Image.new("RGB", (SIZE, SIZE), _rgb(spec["bg"]))
    dark = Image.new("RGB", (SIZE, SIZE), _rgb(spec.get("bg_edge", "#000000")))
    img = Image.composite(base, dark, _vignette_mask())
    tint = _mix(_rgb(spec.get("bg_edge", "#000000")), _rgb(spec["accent"]),
                0.18)
    glow = Image.composite(Image.new("RGB", (SIZE, SIZE), tint),
                           Image.new("RGB", (SIZE, SIZE), (0, 0, 0)),
                           _radial_mask(1500))
    return ImageChops.screen(img, glow)


def _screen_glow(base, layer, radius):
    """
    Add a blurred glow layer onto the base with a screen blend.

    Parameters
    ----------
    base : PIL.Image.Image
        The RGB base image.
    layer : PIL.Image.Image
        The RGB glow layer on black.
    radius : float
        The blur radius.

    Returns
    -------
    PIL.Image.Image
        The composited RGB image.
    """
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    return ImageChops.screen(base, blurred)


def _glow_layer():
    """
    Create a black RGB layer used for glow rendering.

    Parameters
    ----------
    None

    Returns
    -------
    PIL.Image.Image
        A black RGB image.
    """
    return Image.new("RGB", (SIZE, SIZE), (0, 0, 0))


def _rounded(draw, box, radius, fill, outline, width):
    """
    Draw a rounded rectangle panel.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    box : tuple
        The (x0, y0, x1, y1) bounds.
    radius : int
        The corner radius.
    fill : tuple
        The interior color.
    outline : tuple
        The border color.
    width : int
        The border width.

    Returns
    -------
    None
    """
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                           width=width)


def _ic_thermo(d, cx, cy, r, a, dim):
    """Draw a thermometer icon."""
    w = max(8, r // 10)
    d.rounded_rectangle((cx - r // 4, cy - r, cx + r // 4, cy + r // 4),
                        radius=r // 4, outline=a, width=w)
    d.ellipse((cx - r // 2, cy + r // 6, cx + r // 2, cy + r), outline=a,
              width=w)
    d.ellipse((cx - r // 5, cy + r // 4, cx + r // 5, cy + r * 4 // 5),
              fill=dim)
    for step in range(3):
        yy = cy - r * 3 // 4 + step * r // 3
        d.line((cx + r // 8, yy, cx + r // 2, yy), fill=a, width=w)


def _ic_leaf(d, cx, cy, r, a, dim):
    """Draw a pointed leaf icon with a midrib and veins."""
    hw, hh = r * 3 // 4, r // 2
    top = [(cx - hw + 2 * hw * (i / 40), cy - hh * math.sin(math.pi * i / 40))
           for i in range(41)]
    bot = [(cx + hw - 2 * hw * (i / 40), cy + hh * math.sin(math.pi * i / 40))
           for i in range(41)]
    w = max(8, r // 12)
    d.line(top + bot + [top[0]], fill=a, width=w, joint="curve")
    d.line((cx - hw, cy, cx + hw, cy), fill=a, width=max(6, w - 2))
    for step in (0.3, 0.5, 0.7):
        base = cx - hw + 2 * hw * step
        d.line((base, cy, base - r // 4, cy - r // 4), fill=a,
               width=max(5, w - 4))
        d.line((base, cy, base - r // 4, cy + r // 4), fill=a,
               width=max(5, w - 4))


def _ic_drop(d, cx, cy, r, a, dim):
    """Draw a teardrop icon."""
    w = max(8, r // 10)
    d.ellipse((cx - r * 3 // 4, cy - r // 6, cx + r * 3 // 4, cy + r * 5 // 6),
              outline=a, width=w)
    d.polygon((cx, cy - r, cx - r * 3 // 4, cy + r // 4,
               cx + r * 3 // 4, cy + r // 4), outline=a, width=w)
    d.ellipse((cx - r // 4, cy + r // 3, cx + r // 4, cy + r * 3 // 5),
              fill=dim)


def _ic_led(d, cx, cy, r, a, dim):
    """Draw an LED icon with emitted rays."""
    w = max(8, r // 10)
    d.ellipse((cx - r * 3 // 5, cy - r * 3 // 5, cx + r * 3 // 5,
               cy + r * 3 // 5), outline=a, width=w)
    d.ellipse((cx - r // 4, cy - r // 4, cx + r // 4, cy + r // 4), fill=dim)
    for step in range(8):
        ang = math.radians(step * 45)
        x0 = cx + math.cos(ang) * r * 4 // 5
        y0 = cy + math.sin(ang) * r * 4 // 5
        x1 = cx + math.cos(ang) * r * 23 // 20
        y1 = cy + math.sin(ang) * r * 23 // 20
        d.line((x0, y0, x1, y1), fill=a, width=max(5, w - 3))


def _ic_lcd(d, cx, cy, r, a, dim):
    """Draw a character LCD icon."""
    w = max(8, r // 12)
    d.rounded_rectangle((cx - r, cy - r * 3 // 5, cx + r, cy + r * 3 // 5),
                        radius=r // 6, outline=a, width=w)
    d.rectangle((cx - r * 4 // 5, cy - r // 3, cx + r * 4 // 5, cy - r // 20),
                fill=dim)
    d.rectangle((cx - r * 4 // 5, cy + r // 12, cx + r // 3, cy + r // 3),
                fill=dim)
    for step in range(4):
        x = cx - r * 3 // 5 + step * r * 2 // 5
        d.line((x, cy + r * 3 // 5, x, cy + r * 17 // 20), fill=a, width=w)


def _ic_servo(d, cx, cy, r, a, dim):
    """Draw a servo motor icon with a horn."""
    w = max(8, r // 10)
    d.rounded_rectangle((cx - r * 3 // 4, cy - r // 2, cx + r * 3 // 4,
                         cy + r * 3 // 4), radius=r // 6, outline=a, width=w)
    d.ellipse((cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3),
              outline=a, width=w)
    d.line((cx, cy, cx, cy - r), fill=a, width=w)
    d.line((cx, cy - r, cx + r * 3 // 4, cy - r), fill=a, width=w)
    d.ellipse((cx - r // 8, cy - r // 8, cx + r // 8, cy + r // 8), fill=dim)


def _ic_button(d, cx, cy, r, a, dim):
    """Draw a tactile push button icon."""
    w = max(8, r // 10)
    d.rounded_rectangle((cx - r, cy - r, cx + r, cy + r), radius=r // 3,
                        outline=a, width=w)
    d.ellipse((cx - r * 3 // 5, cy - r * 3 // 5, cx + r * 3 // 5,
               cy + r * 3 // 5), outline=a, width=w)
    d.ellipse((cx - r // 4, cy - r // 4, cx + r // 4, cy + r // 4), fill=dim)


def _ic_remote(d, cx, cy, r, a, dim):
    """Draw a compact remote control icon with IR beams."""
    w = max(8, r // 10)
    d.rounded_rectangle((cx - r // 2, cy - r // 6, cx + r // 2, cy + r),
                        radius=r // 5, outline=a, width=w)
    for row in range(2):
        for col in range(2):
            x = cx - r // 4 + col * r // 2
            y = cy + r // 6 + row * r // 3
            d.ellipse((x - r // 10, y - r // 10, x + r // 10, y + r // 10),
                      fill=dim)
    for step in range(3):
        rr = r * (1 + step) // 3
        d.arc((cx - rr, cy - r // 6 - rr, cx + rr, cy - r // 6 + rr), 210, 330,
              fill=a, width=max(5, w - 3))


def _ic_antenna(d, cx, cy, r, a, dim):
    """Draw an antenna mast with a radiated signal."""
    w = max(8, r // 10)
    d.line((cx, cy - r // 3, cx, cy + r), fill=a, width=w)
    d.line((cx - r * 3 // 4, cy + r, cx + r * 3 // 4, cy + r), fill=a, width=w)
    d.line((cx, cy - r // 3, cx - r // 3, cy + r // 6), fill=a, width=w)
    d.line((cx, cy - r // 3, cx + r // 3, cy + r // 6), fill=a, width=w)
    for step in range(3):
        rr = r * (1 + step) // 3
        d.arc((cx - rr, cy - r // 3 - rr, cx + rr, cy - r // 3 + rr), 210, 330,
              fill=dim, width=max(5, w - 3))


def _ic_lock(d, cx, cy, r, a, dim):
    """Draw a padlock icon."""
    w = max(8, r // 10)
    d.rounded_rectangle((cx - r * 3 // 4, cy - r // 6, cx + r * 3 // 4,
                         cy + r), radius=r // 6, outline=a, width=w)
    d.arc((cx - r // 2, cy - r, cx + r // 2, cy + r // 3), 180, 360, fill=a,
          width=w)
    d.ellipse((cx - r // 6, cy + r // 6, cx + r // 6, cy + r // 2), fill=dim)


def _ic_shield(d, cx, cy, r, a, dim):
    """Draw a security shield icon with a check mark."""
    w = max(8, r // 10)
    pts = [(cx, cy - r), (cx + r * 3 // 4, cy - r * 3 // 5),
           (cx + r * 3 // 4, cy + r // 4), (cx, cy + r),
           (cx - r * 3 // 4, cy + r // 4), (cx - r * 3 // 4, cy - r * 3 // 5)]
    d.polygon(pts, outline=a, width=w)
    d.line((cx - r // 3, cy, cx - r // 10, cy + r // 3), fill=dim,
           width=max(8, w))
    d.line((cx - r // 10, cy + r // 3, cx + r // 3, cy - r // 3), fill=dim,
           width=max(8, w))


def _ic_bug(d, cx, cy, r, a, dim):
    """Draw a software bug icon."""
    w = max(8, r // 12)
    d.ellipse((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), outline=a,
              width=w)
    d.ellipse((cx - r // 4, cy - r * 3 // 4, cx + r // 4, cy - r // 3),
              outline=a, width=w)
    d.line((cx - r // 4, cy - r * 3 // 4, cx - r // 2, cy - r), fill=a,
           width=w)
    d.line((cx + r // 4, cy - r * 3 // 4, cx + r // 2, cy - r), fill=a,
           width=w)
    for step in range(3):
        yy = cy - r // 3 + step * r // 3
        d.line((cx - r // 2, yy, cx - r, yy - r // 5), fill=a, width=w)
        d.line((cx + r // 2, yy, cx + r, yy - r // 5), fill=a, width=w)
    d.line((cx, cy - r // 2, cx, cy + r // 2), fill=dim, width=max(5, w - 3))


def _ic_chip(d, cx, cy, r, a, dim):
    """Draw an integrated circuit chip icon."""
    w = max(8, r // 12)
    d.rounded_rectangle((cx - r * 3 // 4, cy - r * 3 // 4, cx + r * 3 // 4,
                         cy + r * 3 // 4), radius=r // 8, outline=a, width=w)
    d.rectangle((cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3),
                outline=dim, width=max(5, w - 4))
    for step in range(4):
        off = -r * 3 // 5 + step * r * 2 // 5
        d.line((cx + off, cy - r * 3 // 4, cx + off, cy - r), fill=a, width=w)
        d.line((cx + off, cy + r * 3 // 4, cx + off, cy + r), fill=a, width=w)
        d.line((cx - r * 3 // 4, cy + off, cx - r, cy + off), fill=a, width=w)
        d.line((cx + r * 3 // 4, cy + off, cx + r, cy + off), fill=a, width=w)


def _ic_key(d, cx, cy, r, a, dim):
    """Draw a cryptographic key icon."""
    w = max(8, r // 10)
    d.ellipse((cx - r, cy - r // 2, cx - r // 2, cy + r // 2), outline=a,
              width=w)
    d.line((cx - r * 3 // 4, cy, cx + r, cy), fill=a, width=w)
    d.line((cx + r // 4, cy, cx + r // 4, cy + r // 3), fill=a, width=w)
    d.line((cx + r * 3 // 5, cy, cx + r * 3 // 5, cy + r // 2), fill=a,
           width=w)
    d.ellipse((cx - r * 7 // 8, cy - r // 8, cx - r * 5 // 8, cy + r // 8),
              fill=dim)


def _ic_clock(d, cx, cy, r, a, dim):
    """Draw a clock icon."""
    w = max(8, r // 12)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=a, width=w)
    d.line((cx, cy, cx, cy - r * 3 // 5), fill=a, width=w)
    d.line((cx, cy, cx + r // 2, cy + r // 5), fill=dim, width=w)
    for step in range(12):
        ang = math.radians(step * 30)
        d.line((cx + math.cos(ang) * r * 4 // 5, cy + math.sin(ang) * r * 4 // 5,
                cx + math.cos(ang) * r * 9 // 10,
                cy + math.sin(ang) * r * 9 // 10), fill=a, width=max(4, w - 5))


def _ic_gauge(d, cx, cy, r, a, dim):
    """Draw a gauge icon with a needle."""
    w = max(8, r // 10)
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=a, width=w)
    d.line((cx - r, cy, cx + r, cy), fill=a, width=w)
    d.line((cx, cy, cx + r // 2, cy - r // 2), fill=dim, width=w)
    d.ellipse((cx - r // 6, cy - r // 6, cx + r // 6, cy + r // 6), fill=a)
    for step in range(5):
        ang = math.radians(180 + step * 45)
        d.line((cx + math.cos(ang) * r * 3 // 4, cy + math.sin(ang) * r * 3 // 4,
                cx + math.cos(ang) * r * 9 // 10,
                cy + math.sin(ang) * r * 9 // 10), fill=a, width=max(4, w - 5))


def _ic_wifi(d, cx, cy, r, a, dim):
    """Draw a Wi-Fi signal icon."""
    w = max(8, r // 8)
    for step in range(3):
        rr = r * (2 + step * 2) // 5
        d.arc((cx - rr, cy - rr + r // 3, cx + rr, cy + rr + r // 3), 200, 340,
              fill=a, width=w)
    d.ellipse((cx - r // 6, cy + r // 2, cx + r // 6, cy + r * 5 // 6),
              fill=dim)


def _ic_hash(d, cx, cy, r, a, dim):
    """Draw a hash or number sign icon."""
    w = max(8, r // 10)
    d.line((cx - r // 3, cy - r, cx - r // 3, cy + r), fill=a, width=w)
    d.line((cx + r // 3, cy - r, cx + r // 3, cy + r), fill=a, width=w)
    d.line((cx - r, cy - r // 3, cx + r, cy - r // 3), fill=dim, width=w)
    d.line((cx - r, cy + r // 3, cx + r, cy + r // 3), fill=dim, width=w)


def _ic_wave(d, cx, cy, r, a, dim):
    """Draw a sine waveform icon."""
    w = max(8, r // 10)
    pts = [(cx - r + 2 * r * (i / 48),
            cy - math.sin(2 * math.pi * i / 48) * r * 2 // 3)
           for i in range(49)]
    d.line(pts, fill=a, width=w, joint="curve")
    d.line((cx - r, cy, cx + r, cy), fill=dim, width=max(4, w - 5))


def _ic_bell(d, cx, cy, r, a, dim):
    """Draw an alarm bell icon."""
    w = max(8, r // 10)
    pts = [(cx - r * 3 // 4, cy + r // 2), (cx - r * 1 // 2, cy - r // 3),
           (cx - r // 2, cy - r * 3 // 5), (cx + r // 2, cy - r * 3 // 5),
           (cx + r // 2, cy - r // 3), (cx + r * 3 // 4, cy + r // 2)]
    d.line(pts, fill=a, width=w, joint="curve")
    d.line((cx - r * 3 // 4, cy + r // 2, cx + r * 3 // 4, cy + r // 2),
           fill=a, width=w)
    d.ellipse((cx - r // 5, cy + r // 2, cx + r // 5, cy + r * 4 // 5),
              fill=dim)
    d.ellipse((cx - r // 6, cy - r, cx + r // 6, cy - r * 7 // 10), fill=a)


_ICON_FUNCS = {
    "thermo": _ic_thermo, "leaf": _ic_leaf, "drop": _ic_drop, "led": _ic_led,
    "lcd": _ic_lcd, "servo": _ic_servo, "button": _ic_button,
    "remote": _ic_remote, "antenna": _ic_antenna, "lock": _ic_lock,
    "shield": _ic_shield, "bug": _ic_bug, "chip": _ic_chip, "key": _ic_key,
    "clock": _ic_clock, "gauge": _ic_gauge, "wifi": _ic_wifi,
    "hash": _ic_hash, "wave": _ic_wave, "bell": _ic_bell,
}


def _icon(draw, cx, cy, kind, r, accent, dim):
    """
    Draw the requested vector icon.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    cx : int
        The icon center x.
    cy : int
        The icon center y.
    kind : str
        The icon kind from the ICONS set.
    r : int
        The icon half size.
    accent : tuple
        The accent color.
    dim : tuple
        The dim accent color.

    Returns
    -------
    None
    """
    _ICON_FUNCS.get(kind, _ic_thermo)(draw, cx, cy, r, accent, dim)


def _medallion(img, cx, cy, radius, kind, accent, dim, bg):
    """
    Draw the symmetric circular icon medallion.

    The icon radius is derived from the icon's reach factor so its widest ray
    or arc always stays inside the medallion ring.

    Parameters
    ----------
    img : PIL.Image.Image
        The destination image.
    cx : int
        The medallion center x.
    cy : int
        The medallion center y.
    radius : int
        The outer ring radius.
    kind : str
        The icon kind from the ICONS set.
    accent : tuple[int, int, int]
        The accent color.
    dim : tuple[int, int, int]
        The dim color.
    bg : tuple[int, int, int]
        The background color.

    Returns
    -------
    None
    """
    ring = _glow_layer()
    ImageDraw.Draw(ring).ellipse((cx - radius, cy - radius, cx + radius,
                                  cy + radius), outline=accent, width=14)
    img.paste(ImageChops.screen(img, ring.filter(ImageFilter.GaussianBlur(20))))
    draw = ImageDraw.Draw(img)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 fill=_mix(bg, accent, 0.14), outline=accent, width=5)
    inner = radius - 26
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner),
                 outline=_mix(dim, accent, 0.3), width=2)
    for step in range(12):
        ang = math.radians(step * 30)
        x = cx + math.cos(ang) * (radius - 13)
        y = cy + math.sin(ang) * (radius - 13)
        dot = 7 if step % 3 == 0 else 4
        draw.ellipse((x - dot, y - dot, x + dot, y + dot),
                     fill=accent if step % 3 == 0 else dim)
    reach = _ICON_REACH.get(kind, 1.0)
    icon_r = int((radius - 52) / reach)
    _icon(draw, cx, cy, kind, icon_r, accent, _mix(bg, accent, 0.55))


def _chip(draw, x, y, w, h, label, value, accent, white):
    """
    Draw one auto-fitted data chip with an accent bar.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    x : int
        The chip left edge.
    y : int
        The chip top edge.
    w : int
        The chip width.
    h : int
        The chip height.
    label : str
        The chip label.
    value : str
        The chip value.
    accent : tuple
        The accent color.
    white : tuple
        The value text color.

    Returns
    -------
    None
    """
    _rounded(draw, (x, y, x + w, y + h), 18, _CHIP_FILL, accent, 3)
    draw.rounded_rectangle((x + 14, y + 18, x + 20, y + h - 18), radius=3,
                           fill=accent)
    _left_fit(draw, x + 40, y + 16, label, 34, accent, w - 64, True)
    _left_fit(draw, x + 40, y + h - 54, value, 34, white, w - 64, False)


def _chips_row(draw, chips, x0, x1, y, h, accent, white):
    """
    Draw a single row of data chips.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    chips : list
        The chip dictionaries.
    x0 : int
        The row left edge.
    x1 : int
        The row right edge.
    y : int
        The chip top edge.
    h : int
        The chip height.
    accent : tuple
        The accent color.
    white : tuple
        The value text color.

    Returns
    -------
    None
    """
    gap = 30
    width = (x1 - x0 - gap * (len(chips) - 1)) // len(chips)
    for index, chip in enumerate(chips):
        x = x0 + index * (width + gap)
        _chip(draw, x, y, width, h, chip["label"], chip["value"], accent,
              white)


def _chips_grid(draw, chips, x0, x1, y0, cols, h, accent, white):
    """
    Draw a matrix of data chips.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    chips : list
        The chip dictionaries.
    x0 : int
        The grid left edge.
    x1 : int
        The grid right edge.
    y0 : int
        The first row top edge.
    cols : int
        The number of columns.
    h : int
        The chip height.
    accent : tuple
        The accent color.
    white : tuple
        The value text color.

    Returns
    -------
    None
    """
    gap = 30
    width = (x1 - x0 - gap * (cols - 1)) // cols
    for index, chip in enumerate(chips):
        row, col = divmod(index, cols)
        x = x0 + col * (width + gap)
        y = y0 + row * (h + gap)
        _chip(draw, x, y, width, h, chip["label"], chip["value"], accent,
              white)


def _terminal(draw, box, lines, accent, dim, cyan, max_size=40):
    """
    Draw the terminal transcript block, shrinking to fit its width.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    box : tuple
        The (x0, y0, x1, y1) bounds.
    lines : list
        The transcript lines.
    accent : tuple
        The accent color.
    dim : tuple
        The dim text color.
    cyan : tuple
        The secondary color.
    max_size : int
        The largest allowed transcript font size.

    Returns
    -------
    None
    """
    _rounded(draw, box, 24, _TERM_FILL, _mix(dim, accent, 0.35), 3)
    max_w = box[2] - box[0] - 80
    size = max_size
    font = _font(size, False)
    longest = max((_spaced_width(draw, line, font, 0) for line in lines),
                  default=0)
    while size > 18 and longest > max_w:
        size -= 1
        font = _font(size, False)
        longest = max((_spaced_width(draw, line, font, 0) for line in lines),
                      default=0)
    line_h = int(size * 1.7)
    top = box[1] + max(24, (box[3] - box[1] - line_h * len(lines)) // 2)
    for line in lines:
        color = dim
        if line.startswith("[*]"):
            color = cyan
        elif line.startswith("[+]"):
            color = accent
        draw.text((box[0] + 40, top), line, font=font, fill=color)
        width = _spaced_width(draw, line, font, 0)
        _record(line, box[0] + 40, box[0] + 40 + width, top, top + font.size,
                size, False)
        top += line_h


def _cards(draw, y, h, cards, accent, dim, white):
    """
    Draw the row of auto-fitted status cards with an accent cap.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    y : int
        The card top edge.
    h : int
        The card height.
    cards : list
        Card dictionaries with tag, label, and value.
    accent : tuple
        The accent color.
    dim : tuple
        The dim text color.
    white : tuple
        The bright text color.

    Returns
    -------
    None
    """
    gap, x0, x1 = 40, 120, 2280
    width = (x1 - x0 - gap * (len(cards) - 1)) // len(cards)
    for index, card in enumerate(cards):
        x = x0 + index * (width + gap)
        _rounded(draw, (x, y, x + width, y + h), 20, _CHIP_FILL, dim, 3)
        draw.rounded_rectangle((x + 20, y + 14, x + width - 20, y + 20),
                               radius=3, fill=accent)
        _left_fit(draw, x + 30, y + 30, card["tag"], 38, accent, width - 60,
                  True)
        _left_fit(draw, x + 30, y + h // 2 - 6, card["label"], 34, white,
                  width - 60, False)
        _left_fit(draw, x + 30, y + h - 54, card["value"], 34, dim,
                  width - 60, True)


def _pills(draw, cx, y, h, items, accent, white):
    """
    Draw a symmetric centered row of outlined category pills.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    cx : int
        The center x position.
    y : int
        The pill top edge.
    h : int
        The pill height.
    items : list
        The category strings.
    accent : tuple
        The accent color.
    white : tuple
        The label color.

    Returns
    -------
    None
    """
    gap, pad = 28, 40
    font = _font(40, True)
    widths = [_spaced_width(draw, item, font, 6) for item in items]
    total = sum(w + 2 * pad for w in widths) + gap * (len(items) - 1)
    x = cx - total / 2
    for item, width in zip(items, widths):
        pill = width + 2 * pad
        _rounded(draw, (x, y, x + pill, y + h), h // 2, _CHIP_FILL, accent, 3)
        text_y = y + (h - font.size) // 2 - 6
        _spaced_text(draw, x + pad, text_y, item, font, white, 6)
        _record(item, x + pad, x + pad + width, text_y, text_y + font.size,
                font.size, False)
        x += pill + gap


def _dots(draw, y, count, color):
    """
    Draw a row of separator dots.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    y : int
        The dot center row.
    count : int
        The number of dots.
    color : tuple
        The dot color.

    Returns
    -------
    None
    """
    margin = 160
    step = (SIZE - 2 * margin) / (count - 1)
    for index in range(count):
        x = margin + index * step
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)


def _header(img, spec, accent, white, sub_y):
    """
    Draw the eyebrow, gradient title, and subtitle lines with auto-fit.

    Parameters
    ----------
    img : PIL.Image.Image
        The destination image.
    spec : dict
        The banner specification.
    accent : tuple
        The accent color.
    white : tuple
        The title color.
    sub_y : int
        The subtitle top position.

    Returns
    -------
    None
    """
    draw = ImageDraw.Draw(img)
    _center_fit(draw, SIZE // 2, 80, spec["eyebrow"], 46, 20, accent, True)
    _gradient_text(img, SIZE // 2, 160, spec["title"], 150, 10, accent, white,
                   True)
    _center_fit(draw, SIZE // 2, sub_y, spec["subtitle"], 50, 20, accent, True)


def _footer(draw, spec, accent, white, dim, y0, y1, dots=None):
    """
    Draw the dotted footer lines with auto-fit.

    Parameters
    ----------
    draw : PIL.ImageDraw.ImageDraw
        The drawing surface.
    spec : dict
        The banner specification.
    accent : tuple
        The accent color.
    white : tuple
        The bright text color.
    dim : tuple
        The dot color.
    y0 : int
        The first footer line top.
    y1 : int
        The second footer line top.
    dots : int, optional
        The y of the trailing dot row.

    Returns
    -------
    None
    """
    if dots is not None:
        _dots(draw, dots, 40, dim)
    _center_fit(draw, SIZE // 2, y0, spec["footer"][0], 44, 16, accent, True)
    _center_fit(draw, SIZE // 2, y1, spec["footer"][1], 40, 14, white, True)


def _layout_panel(img, spec, accent, dim, white, cyan):
    """Draw the centered medallion layout with chips and a terminal."""
    _header(img, spec, accent, white, 350)
    _medallion(img, SIZE // 2, 700, 195, spec["icon"], accent, dim,
               _rgb(spec["bg"]))
    draw = ImageDraw.Draw(img)
    _center_fit(draw, SIZE // 2, 985, spec["panel_status"], 48, 14, accent,
                True)
    _chips_row(draw, spec["chips"], 170, 2230, 1050, 150, accent, white)
    _terminal(draw, (120, 1300, 2280, 1700), spec["terminal"], accent, dim, cyan)
    _pills(draw, SIZE // 2, 1750, 72, spec["categories"], accent, white)
    _cards(draw, 1860, 170, spec["cards"], accent, dim, white)
    _footer(draw, spec, accent, white, dim, 2100, 2185, dots=2070)


def _layout_split(img, spec, accent, dim, white, cyan):
    """Draw a left medallion panel beside a right detail block."""
    _header(img, spec, accent, white, 350)
    draw = ImageDraw.Draw(img)
    left = (120, 520, 1080, 1640)
    right = (1120, 520, 2280, 1640)
    _rounded(draw, left, 40, _PANEL_FILL, accent, 4)
    _rounded(draw, right, 40, _PANEL_FILL, accent, 4)
    _medallion(img, 600, 850, 190, spec["icon"], accent, dim, _rgb(spec["bg"]))
    _center_fit(draw, 600, 1160, spec["panel_status"], 44, 10, accent, True,
                max_w=800)
    _terminal(draw, (1160, 560, 2240, 1080), spec["terminal"], accent, dim, cyan)
    _chips_grid(draw, spec["chips"], 1160, 2240, 1120, 2, 150, accent, white)
    _pills(draw, SIZE // 2, 1700, 72, spec["categories"], accent, white)
    _cards(draw, 1800, 170, spec["cards"], accent, dim, white)
    _footer(draw, spec, accent, white, dim, 2040, 2125, dots=2010)


def _layout_terminal(img, spec, accent, dim, white, cyan):
    """Draw a layout dominated by a large terminal transcript."""
    _header(img, spec, accent, white, 340)
    _medallion(img, SIZE // 2, 530, 105, spec["icon"], accent, dim,
               _rgb(spec["bg"]))
    draw = ImageDraw.Draw(img)
    _terminal(draw, (120, 660, 2280, 1580), spec["terminal"], accent, dim, cyan,
              max_size=52)
    _pills(draw, SIZE // 2, 1620, 70, spec["categories"], accent, white)
    _chips_row(draw, spec["chips"], 170, 2230, 1720, 140, accent, white)
    _cards(draw, 1890, 150, spec["cards"], accent, dim, white)
    _footer(draw, spec, accent, white, dim, 2110, 2195, dots=2080)


def _layout_stat(img, spec, accent, dim, white, cyan):
    """Draw a layout with one huge centered reading."""
    _header(img, spec, accent, white, 360)
    draw = ImageDraw.Draw(img)
    stat = spec.get("stat") or spec["chips"][0]["value"]
    _center_fit(draw, SIZE // 2, 470, stat, 300, 6, accent, True)
    _center_fit(draw, SIZE // 2, 830, spec["panel_status"], 56, 16, white, True)
    _medallion(img, SIZE // 2, 1140, 200, spec["icon"], accent, dim,
               _rgb(spec["bg"]))
    _pills(draw, SIZE // 2, 1420, 72, spec["categories"], accent, white)
    _chips_row(draw, spec["chips"], 170, 2230, 1520, 140, accent, white)
    _cards(draw, 1700, 170, spec["cards"], accent, dim, white)
    _footer(draw, spec, accent, white, dim, 1970, 2055, dots=1940)


def _layout_grid(img, spec, accent, dim, white, cyan):
    """Draw a layout with a matrix of chips."""
    _header(img, spec, accent, white, 340)
    _medallion(img, SIZE // 2, 520, 100, spec["icon"], accent, dim,
               _rgb(spec["bg"]))
    draw = ImageDraw.Draw(img)
    _center_fit(draw, SIZE // 2, 650, spec["panel_status"], 50, 14, accent,
                True)
    _chips_grid(draw, spec["chips"], 170, 2230, 740, 2, 170, accent, white)
    _terminal(draw, (170, 1160, 2230, 1580), spec["terminal"], accent, dim, cyan)
    _pills(draw, SIZE // 2, 1620, 70, spec["categories"], accent, white)
    _cards(draw, 1700, 160, spec["cards"], accent, dim, white)
    _footer(draw, spec, accent, white, dim, 1930, 2015, dots=1900)


_LAYOUT_FUNCS = {
    "panel": _layout_panel, "split": _layout_split,
    "terminal": _layout_terminal, "stat": _layout_stat, "grid": _layout_grid,
}


def _compose(img, spec):
    """
    Draw every banner layer onto the given image.

    Parameters
    ----------
    img : PIL.Image.Image
        The destination RGB image.
    spec : dict
        The banner specification.

    Returns
    -------
    PIL.Image.Image
        The same image, mutated in place.
    """
    accent = _rgb(spec["accent"])
    dim = _rgb(spec.get("dim", "#6B7280"))
    white = _rgb(spec.get("white", "#F2F5FF"))
    cyan = _rgb(spec.get("cyan", "#7FD8E0"))
    layout = spec.get("layout", "panel")
    _LAYOUT_FUNCS.get(layout, _layout_panel)(img, spec, accent, dim, white,
                                             cyan)
    return img


def _render(spec):
    """
    Render the full banner image.

    Parameters
    ----------
    spec : dict
        The banner specification.

    Returns
    -------
    PIL.Image.Image
        The rendered RGB banner.
    """
    accent = _rgb(spec["accent"])
    white = _rgb(spec.get("white", "#F2F5FF"))
    img = _background(spec)
    glow = _glow_layer()
    _header(glow, spec, accent, white, 350)
    img = _screen_glow(img, glow, 26)
    _compose(img, spec)
    return img


def measure_spec(spec):
    """
    Measure every drawn text extent for a spec without saving an image.

    Parameters
    ----------
    spec : dict
        The banner specification.

    Returns
    -------
    dict
        The minimum left edge, maximum right edge, and per-line records.
    """
    _RECORDS.clear()
    _compose(Image.new("RGB", (SIZE, SIZE)), spec)
    records = list(_RECORDS)
    if not records:
        return {"min_left": SIZE, "max_right": 0, "records": [],
                "overflow": []}
    min_left = min(item["left"] for item in records)
    max_right = max(item["right"] for item in records)
    overflow = [item for item in records
                if item["left"] < MARGIN - 1 or item["right"] > SIZE - MARGIN + 1]
    return {"min_left": min_left, "max_right": max_right, "records": records,
            "overflow": overflow}


def main():
    """
    Load the spec, render the banner, and write the PNG artifact.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Zero on success.
    """
    root = Path.cwd()
    spec = json.loads((root / "banner.json").read_text(encoding="utf-8"))
    out = root / f"{spec['repo']}.png"
    _render(spec).save(out)
    metrics = measure_spec(spec)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print(f"text extent left={metrics['min_left']:.0f} "
          f"right={metrics['max_right']:.0f} (limit {MARGIN}..{SIZE - MARGIN})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
