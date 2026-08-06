"""Streamlit Web Application for Perfume Scanner."""

from __future__ import annotations

import re
import time
from pathlib import Path

import streamlit as st

# Import backend scraper and comparator
from perfume_scanner.comparator import process_and_compare_deals
from perfume_scanner.scraper import RETAILERS, scrape_all_retailers
from perfume_scanner.search_widget import render_search_autocomplete

ASSETS_DIR = Path(__file__).parent / "assets"

# Page Configuration
st.set_page_config(
    page_title="Indian Perfume Scanner | Compare Fragrance Deals",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def sanitize_html(html_str: str) -> str:
    """Strips per-line indentation from HTML/SVG to prevent Streamlit Markdown 4-space code block bugs."""
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    return "".join(lines)


@st.cache_data(show_spinner=False)
def load_audio_base64(relative_path: str) -> str:
    """Reads a bundled audio file from `assets/` and returns a base64 data URI.

    Cached so the (small) file is only read and encoded once per session
    instead of on every Streamlit rerun. Returns an empty string if the
    asset is missing so a renamed/removed sound effect never crashes the
    app -- it just silently skips playback.
    """
    import base64

    asset_path = ASSETS_DIR / relative_path
    try:
        audio_bytes = asset_path.read_bytes()
    except OSError:
        return ""

    mime_type = "audio/mpeg" if asset_path.suffix.lower() == ".mp3" else "audio/wav"
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def generate_spray_wav_base64(duration_seconds=1.2, sample_rate=22050) -> str:
    """Generates a 16-bit high-passed white noise wave file in bytes and encodes it as Base64."""
    import base64
    import math
    import random
    import struct

    num_samples = int(sample_rate * duration_seconds)
    samples = []

    # Simple high-pass white noise difference filter: y[n] = x[n] - x[n-1]
    prev_x = 0.0
    for i in range(num_samples):
        t = i / sample_rate
        envelope = t / 0.08 if t < 0.08 else math.exp(-3.5 * (t - 0.08))

        x = random.uniform(-1.0, 1.0)
        y = x - prev_x
        prev_x = x

        # Scale volume and clamp PCM limit
        val = max(-1.0, min(1.0, y * envelope * 0.12))
        samples.append(int(val * 32767))

    subchunk2_size = num_samples * 2
    chunk_size = 36 + subchunk2_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        subchunk2_size,
    )

    wav_bytes = header + struct.pack(f"<{len(samples)}h", *samples)
    return "data:audio/wav;base64," + base64.b64encode(wav_bytes).decode("utf-8")


# Multi-Theme Customizer System
THEMES = {
    "Beach Vibes 🌊": {
        "name": "Beach Vibes 🌊",
        "bg_base": "#021424",
        "bg_radial": "radial-gradient(circle at top, #093358 0%, #021424 85%)",
        "header_bg": "rgba(8, 37, 66, 0.65)",
        "accent": "#00e5ff",
        "secondary": "#ffb703",
        "sub_text": "#8ea8c3",
        "card_bg": "rgba(8, 37, 66, 0.65)",
        "card_border": "rgba(0, 229, 255, 0.4)",
        "card_shadow": "rgba(0, 229, 255, 0.25)",
        "button_bg": "linear-gradient(90deg, #00e5ff 0%, #00b4d8 100%)",
        "button_text": "#021424",
        "wave_1": "%2300e5ff",
        "wave_2": "%23ffb703",
        "title_gradient": "linear-gradient(120deg, #ffffff 0%, #00e5ff 20%, #ffffff 40%, #ffb703 60%, #00e5ff 80%, #ffffff 100%)",
        "glow": "rgba(0, 229, 255, 0.6)",
        "glow_alt": "rgba(255, 183, 3, 0.5)",
        "liquid_stop1": "rgba(0, 229, 255, 0.55)",
        "liquid_stop2": "rgba(0, 180, 216, 0.65)",
        "liquid_stop3": "rgba(255, 183, 3, 0.5)",
        "tagline": "🌊 Surf live fragrance deals and real images across 11 leading Indian retailers 🏖️",
        "spray_color": "rgba(0, 229, 255, 0.95)",
    },
    "Crimson Passion 🔴": {
        "name": "Crimson Passion 🔴",
        "bg_base": "#0c0205",
        "bg_radial": "radial-gradient(circle at top, #3a000a 0%, #0c0205 85%)",
        "header_bg": "rgba(42, 10, 18, 0.7)",
        "accent": "#ff0033",
        "secondary": "#ffb703",
        "sub_text": "#cfa8b0",
        "card_bg": "rgba(42, 10, 18, 0.7)",
        "card_border": "rgba(255, 0, 51, 0.4)",
        "card_shadow": "rgba(255, 0, 51, 0.25)",
        "button_bg": "linear-gradient(90deg, #ff0033 0%, #c80028 100%)",
        "button_text": "#ffffff",
        "wave_1": "%23ff0033",
        "wave_2": "%23ffb703",
        "title_gradient": "linear-gradient(120deg, #ffffff 0%, #ff0033 20%, #ffffff 40%, #ffb703 60%, #ff0033 80%, #ffffff 100%)",
        "glow": "rgba(255, 0, 51, 0.6)",
        "glow_alt": "rgba(255, 183, 3, 0.5)",
        "liquid_stop1": "rgba(255, 0, 51, 0.65)",
        "liquid_stop2": "rgba(200, 0, 40, 0.75)",
        "liquid_stop3": "rgba(255, 183, 3, 0.5)",
        "tagline": "🔥 Ignite live fragrance deals & crimson prices across 11 leading Indian retailers 🌹",
        "spray_color": "rgba(255, 0, 51, 0.95)",
    },
    "Floral Bloom 🌸": {
        "name": "Floral Bloom 🌸",
        "bg_base": "#150210",
        "bg_radial": "radial-gradient(circle at top, #3c092a 0%, #150210 85%)",
        "header_bg": "rgba(55, 15, 42, 0.7)",
        "accent": "#ff4d8d",
        "secondary": "#9d4edd",
        "sub_text": "#dfb0cb",
        "card_bg": "rgba(55, 15, 42, 0.7)",
        "card_border": "rgba(255, 77, 141, 0.4)",
        "card_shadow": "rgba(255, 77, 141, 0.25)",
        "button_bg": "linear-gradient(90deg, #ff4d8d 0%, #b5179e 100%)",
        "button_text": "#ffffff",
        "wave_1": "%23ff4d8d",
        "wave_2": "%239d4edd",
        "title_gradient": "linear-gradient(120deg, #ffffff 0%, #ff4d8d 20%, #ffffff 40%, #9d4edd 60%, #ff4d8d 80%, #ffffff 100%)",
        "glow": "rgba(255, 77, 141, 0.6)",
        "glow_alt": "rgba(157, 78, 221, 0.5)",
        "liquid_stop1": "rgba(255, 77, 141, 0.6)",
        "liquid_stop2": "rgba(181, 23, 158, 0.7)",
        "liquid_stop3": "rgba(157, 78, 221, 0.5)",
        "tagline": "🌸 Blossom into live fragrance deals & bouquet previews across 11 retailers 🌿",
        "spray_color": "rgba(255, 77, 141, 0.95)",
    },
    "Woody Oud 🪵": {
        "name": "Woody Oud 🪵",
        "bg_base": "#0d0702",
        "bg_radial": "radial-gradient(circle at top, #2d1806 0%, #0d0702 85%)",
        "header_bg": "rgba(45, 24, 10, 0.75)",
        "accent": "#e5a93c",
        "secondary": "#c86414",
        "sub_text": "#d4b896",
        "card_bg": "rgba(45, 24, 10, 0.75)",
        "card_border": "rgba(229, 169, 60, 0.4)",
        "card_shadow": "rgba(229, 169, 60, 0.25)",
        "button_bg": "linear-gradient(90deg, #e5a93c 0%, #b85d1e 100%)",
        "button_text": "#0d0702",
        "wave_1": "%23e5a93c",
        "wave_2": "%23c86414",
        "title_gradient": "linear-gradient(120deg, #ffffff 0%, #e5a93c 20%, #ffffff 40%, #c86414 60%, #e5a93c 80%, #ffffff 100%)",
        "glow": "rgba(229, 169, 60, 0.6)",
        "glow_alt": "rgba(200, 100, 20, 0.5)",
        "liquid_stop1": "rgba(229, 169, 60, 0.65)",
        "liquid_stop2": "rgba(184, 93, 30, 0.75)",
        "liquid_stop3": "rgba(200, 100, 20, 0.5)",
        "tagline": "🪵 Uncover deep wood & royal oud fragrance deals across 11 retailers 👑",
        "spray_color": "rgba(229, 169, 60, 0.95)",
    },
}

def clean_html(html_str: str) -> str:
    """Strip leading whitespace from each line to prevent Python Markdown from parsing HTML/SVG as code blocks."""
    return re.sub(r'^\s+', '', html_str, flags=re.MULTILINE)

# Theme-Specific Bottle SVG Generator
def get_theme_bottle_svg(theme_key: str, theme: dict, is_floating: bool = True, size: str | None = None) -> str:
    if not size:
        size = "135px" if is_floating else "100px"
    glow = theme.get("glow", "rgba(0, 229, 255, 0.6)")
    svg_style = f"width: {size} !important; height: {size} !important; filter: drop-shadow(0 10px 25px {glow}); display: block; margin: 0 auto;"
    css_class = "floating-bottle" if is_floating else "spray-bottle"
    
    if "Crimson" in theme_key or "Cyber" in theme_key:
        # Luxury Faceted Ruby Crimson Flacon with Seductive Cyber Glow
        raw_svg = f"""
        <svg viewBox="0 0 100 100" style="{svg_style}" class="{css_class}">
            <!-- High-Energy Cyber Crimson Laser Spray Emitter -->
            <g class="cyber-spray-emitter">
                <circle class="spray-cloud sc1" cx="65" cy="11" r="2.5" fill="#ff0055" />
                <circle class="spray-cloud sc2" cx="72" cy="7" r="3.2" fill="#ffcc00" />
                <circle class="spray-cloud sc3" cx="80" cy="3" r="4.0" fill="#ff0033" />
                <line x1="61" y1="12" x2="88" y2="2" stroke="#ff0055" stroke-width="1" stroke-dasharray="2,2" opacity="0.85" />
            </g>

            <!-- Octagonal Metallic Ruby Crown Cap -->
            <g class="bottle-cap">
                <path d="M 42,5 L 58,5 L 64,11 L 58,17 L 42,17 L 36,11 Z" fill="url(#ruby-crown)" stroke="url(#ruby-gold-border)" stroke-width="1.2" />
                <rect x="44" y="8" width="12" height="6" rx="1" fill="#150006" opacity="0.7" />
                <circle cx="50" cy="11" r="2" fill="#ff0055" />
                <circle cx="61" cy="11" r="1.5" fill="#ffcc00" />
            </g>

            <!-- Chiseled Gold Neck Ring & Metallic Collar -->
            <path d="M 43,17 L 57,17 L 59,23 L 41,23 Z" fill="url(#ruby-gold-border)" />
            <rect x="42" y="23" width="16" height="5" fill="#20000a" stroke="#ff0055" stroke-width="0.8" />

            <!-- Faceted Crystalline Ruby Glass Body (Chamfered Shoulders & Tapered Waist) -->
            <path d="M 36,28 L 64,28 L 72,36 L 68,76 L 62,86 L 38,86 L 32,76 L 28,36 Z" 
                  fill="url(#ruby-glass-bg)" stroke="url(#ruby-neon-stroke)" stroke-width="2" />

            <!-- Facet Reflection Overlay Lines -->
            <path d="M 36,28 L 50,42 L 64,28 M 32,36 L 50,42 M 68,36 L 50,42 M 50,42 L 50,86" 
                  stroke="rgba(255, 0, 85, 0.4)" stroke-width="0.8" fill="none" />

            <!-- Deep Seductive Crimson Liquid Elixir -->
            <path d="M 34,42 L 66,42 L 64,74 L 59,82 L 41,82 L 36,74 Z" 
                  fill="url(#seductive-elixir)" opacity="0.92" />

            <!-- Glowing Cyber Reticle & Pulsing Core Gem -->
            <g class="cyber-reticle">
                <circle cx="50" cy="53" r="10" stroke="#ff0055" stroke-width="1" fill="none" stroke-dasharray="4,2" />
                <circle cx="50" cy="53" r="5" stroke="#ffcc00" stroke-width="0.8" fill="none" />
                <polygon points="50,48 54,53 50,58 46,53" fill="#ff0055" stroke="#ffffff" stroke-width="0.8" />
            </g>

            <!-- Heavy Obsidian Plaque with Gold & Crimson Typography -->
            <rect x="36" y="66" width="28" height="16" rx="2" fill="rgba(15, 0, 5, 0.92)" stroke="url(#ruby-gold-border)" stroke-width="1" />
            <text x="50" y="73" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.6" font-weight="900" fill="#ff0055" text-anchor="middle" letter-spacing="0.5">CRIMSON</text>
            <text x="50" y="78" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.0" font-weight="800" fill="#ffcc00" text-anchor="middle" letter-spacing="1">INTENSE ⚡</text>

            <defs>
                <linearGradient id="ruby-crown" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#3b0010" />
                    <stop offset="50%" stop-color="#ff0055" />
                    <stop offset="100%" stop-color="#1a0007" />
                </linearGradient>
                <linearGradient id="ruby-gold-border" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ffcc00" />
                    <stop offset="50%" stop-color="#ff0055" />
                    <stop offset="100%" stop-color="#ff9900" />
                </linearGradient>
                <linearGradient id="ruby-glass-bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="rgba(255, 0, 85, 0.25)" />
                    <stop offset="50%" stop-color="rgba(30, 0, 10, 0.85)" />
                    <stop offset="100%" stop-color="rgba(10, 0, 3, 0.95)" />
                </linearGradient>
                <linearGradient id="ruby-neon-stroke" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ff0055" />
                    <stop offset="50%" stop-color="#ffcc00" />
                    <stop offset="100%" stop-color="#ff0033" />
                </linearGradient>
                <linearGradient id="seductive-elixir" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(255, 0, 85, 0.9)" />
                    <stop offset="60%" stop-color="rgba(160, 0, 40, 0.95)" />
                    <stop offset="100%" stop-color="rgba(255, 204, 0, 0.85)" />
                </linearGradient>
            </defs>
        </svg>
        """

    elif "Floral" in theme_key:
        # Floral Bloom Rose Gold Flacon
        raw_svg = f"""
        <svg viewBox="0 0 100 100" style="{svg_style}" class="{css_class}">
            <!-- Floral Blossom Spray Nozzle Particles (Emitted directly from Nozzle tip at 61, 11) -->
            <g class="floral-spray-emitter">
                <text class="emitted-petal ep1" x="61" y="11" font-size="16">🌸</text>
                <text class="emitted-petal ep2" x="61" y="11" font-size="16">🌹</text>
                <text class="emitted-petal ep3" x="61" y="11" font-size="16">🌸</text>
                <text class="emitted-petal ep4" x="61" y="11" font-size="16">🌺</text>
                <text class="emitted-petal ep5" x="61" y="11" font-size="16">🌷</text>
                <text class="emitted-petal ep6" x="61" y="11" font-size="16">🌸</text>
                <text class="emitted-petal ep7" x="61" y="11" font-size="16">🌺</text>
                <text class="emitted-petal ep8" x="61" y="11" font-size="16">🌹</text>
                <text class="emitted-petal ep9" x="61" y="11" font-size="16">🌿</text>
                <text class="emitted-petal ep10" x="61" y="11" font-size="16">🌷</text>
            </g>

            <!-- Rose Gold Floral Cap -->
            <g class="bottle-cap">
                <path d="M 40,18 C 40,8 45,3 50,3 C 55,3 60,8 60,18 Z" fill="url(#floral-gold)" stroke="#ff4d8d" stroke-width="0.8" />
                <rect x="38.5" y="16.5" width="23" height="3.5" rx="1" fill="#9d4edd" />
                <circle cx="61" cy="11" r="1.5" fill="#ff4d8d" />
            </g>

            <!-- Metallic Rose Collar -->
            <rect x="44" y="20" width="12" height="7" rx="1" fill="url(#floral-gold)" stroke="#ff4d8d" stroke-width="0.5" />

            <!-- Curved Amethyst & Rose Glass Flacon -->
            <path d="M 34,30 C 34,26 40,26 44,26 L 56,26 C 60,26 66,26 66,30 C 72,45 70,75 64,84 C 58,88 42,88 36,84 C 30,75 28,45 34,30 Z" 
                  fill="url(#floral-glass)" stroke="url(#floral-stroke)" stroke-width="2" />

            <!-- Rose Pink Liquid Elixir -->
            <path d="M 35,42 C 35,42 65,42 65,42 C 68,60 67,76 62,82 C 57,85 43,85 38,82 C 33,76 32,60 35,42 Z" 
                  fill="url(#floral-liquid)" opacity="0.85" />

            <!-- Flower Label Plaque -->
            <rect x="37" y="50" width="26" height="20" rx="4" fill="rgba(21, 2, 16, 0.85)" stroke="#ff4d8d" stroke-width="1" />
            <text x="50" y="58" font-family="'Plus Jakarta Sans', sans-serif" font-size="3" font-weight="800" fill="#ff4d8d" text-anchor="middle">FLORAL</text>
            <text x="50" y="64" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.2" font-weight="700" fill="#9d4edd" text-anchor="middle">🌸 BLOOM</text>

            <defs>
                <linearGradient id="floral-gold" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ffd1dc" />
                    <stop offset="50%" stop-color="#ff4d8d" />
                    <stop offset="100%" stop-color="#9d4edd" />
                </linearGradient>
                <linearGradient id="floral-stroke" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ff4d8d" />
                    <stop offset="100%" stop-color="#9d4edd" />
                </linearGradient>
                <linearGradient id="floral-glass" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="rgba(255, 77, 141, 0.2)" />
                    <stop offset="100%" stop-color="rgba(55, 15, 42, 0.7)" />
                </linearGradient>
                <linearGradient id="floral-liquid" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(255, 77, 141, 0.75)" />
                    <stop offset="100%" stop-color="rgba(157, 78, 221, 0.65)" />
                </linearGradient>
            </defs>
        </svg>
        """

    elif "Woody" in theme_key or "Oud" in theme_key:
        # Carved Wood Log Perfume Bottle Animation with Step-by-Step Carving Reveal!
        raw_svg = f"""
        <svg viewBox="0 0 100 100" style="{svg_style}" class="{css_class}">
            <style>
                @keyframes wood-log-carving {{
                    0%, 20% {{ opacity: 1; clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }}
                    35% {{ clip-path: polygon(0% 20%, 100% 10%, 100% 100%, 0% 100%); opacity: 0.95; }}
                    50% {{ clip-path: polygon(0% 50%, 100% 40%, 100% 100%, 0% 100%); opacity: 0.75; }}
                    70%, 92% {{ clip-path: polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%); opacity: 0; }}
                    100% {{ opacity: 1; clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }}
                }}
                
                @keyframes inner-bottle-reveal {{
                    0%, 15% {{ opacity: 0.25; transform: scale(0.96); filter: brightness(0.7); }}
                    40% {{ opacity: 0.7; filter: brightness(0.9); }}
                    70%, 92% {{ opacity: 1; transform: scale(1); filter: brightness(1.2) drop-shadow(0 0 14px #e5a93c); }}
                    100% {{ opacity: 0.25; transform: scale(0.96); filter: brightness(0.7); }}
                }}

                @keyframes chisel-carving-path {{
                    0% {{ transform: translate(12px, 10px) rotate(40deg); opacity: 0; }}
                    15% {{ opacity: 1; transform: translate(25px, 20px) rotate(25deg); }}
                    35% {{ transform: translate(75px, 35px) rotate(-135deg); opacity: 1; }}
                    55% {{ transform: translate(20px, 60px) rotate(30deg); opacity: 1; }}
                    70% {{ transform: translate(78px, 75px) rotate(-155deg); opacity: 1; }}
                    82%, 100% {{ transform: translate(85px, 85px) rotate(-170deg); opacity: 0; }}
                }}

                .raw-wood-log-block {{
                    animation: wood-log-carving 6.5s ease-in-out infinite !important;
                }}
                
                .polished-oud-bottle {{
                    animation: inner-bottle-reveal 6.5s ease-in-out infinite !important;
                }}

                .active-chisel-tool {{
                    transform-origin: 0 0;
                    animation: chisel-carving-path 6.5s ease-in-out infinite !important;
                }}
            </style>

            <!-- Flying Wood Shavings & Chips -->
            <g class="wood-shavings">
                <path class="shaving s1" d="M 30,42 Q 18,35 12,45" stroke="#c86414" stroke-width="1.8" fill="none" stroke-linecap="round" />
                <path class="shaving s2" d="M 70,52 Q 82,45 88,55" stroke="#e5a93c" stroke-width="1.8" fill="none" stroke-linecap="round" />
                <path class="shaving s3" d="M 28,68 Q 16,62 10,72" stroke="#7a4213" stroke-width="1.8" fill="none" stroke-linecap="round" />
                <circle class="chip c1" cx="22" cy="40" r="1.5" fill="#e5a93c" />
                <circle class="chip c2" cx="78" cy="50" r="2.0" fill="#c86414" />
                <circle class="chip c3" cx="18" cy="65" r="1.8" fill="#7a4213" />
            </g>

            <!-- Layer 1 (Behind): Inner Polished Oud Bottle (Revealed as Wood Log is Carved Away) -->
            <g class="polished-oud-bottle">
                <!-- Carved Wooden Stopper / Cap -->
                <g class="bottle-cap">
                    <rect x="40" y="4" width="20" height="15" rx="3" fill="#3a1e05" stroke="#e5a93c" stroke-width="1.2" />
                    <ellipse cx="50" cy="8" rx="6" ry="2" fill="none" stroke="#7a4213" stroke-width="0.8" />
                    <ellipse cx="50" cy="8" rx="2.5" ry="1" fill="none" stroke="#e5a93c" stroke-width="0.6" />
                    <rect x="39" y="17" width="22" height="3" rx="0.5" fill="#e5a93c" />
                    <circle cx="61" cy="11" r="1.5" fill="#e5a93c" />
                </g>

                <!-- Antique Brass Collar -->
                <rect x="44" y="20" width="12" height="7" rx="0.8" fill="url(#wood-brass)" stroke="#c86414" stroke-width="0.5" />

                <!-- Carved Wood Log Bottle Body Contour -->
                <path d="M 32,28 C 32,26 40,26 44,26 L 56,26 C 60,26 68,26 68,28 L 68,82 C 68,87 63,89 50,89 C 37,89 32,87 32,82 Z" 
                      fill="url(#carved-wood-bark)" stroke="#e5a93c" stroke-width="1.8" />

                <!-- Carved Wood Grain Rings -->
                <path d="M 35,32 C 37,45 35,65 36,80" stroke="#261202" stroke-width="1.2" fill="none" />
                <path d="M 65,32 C 63,45 65,65 64,80" stroke="#261202" stroke-width="1.2" fill="none" />

                <!-- Glowing Golden Amber Elixir Core Window -->
                <rect x="38" y="44" width="24" height="36" rx="3" fill="url(#amber-oud-liquid)" stroke="#e5a93c" stroke-width="1" />

                <!-- Minimalist Royal Oud Label Plaque -->
                <rect x="40" y="52" width="20" height="20" rx="1.5" fill="#0d0702" stroke="#e5a93c" stroke-width="1" />
                <text x="50" y="60" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.8" font-weight="800" fill="#e5a93c" text-anchor="middle">WOODY</text>
                <text x="50" y="66" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.4" font-weight="700" fill="#c86414" text-anchor="middle">🪵 OUD</text>
            </g>

            <!-- Layer 2 (In Front): Raw Wood Log Block (Carving Away Top-to-Bottom) -->
            <g class="raw-wood-log-block">
                <rect x="25" y="16" width="50" height="74" rx="6" fill="url(#bark-texture)" stroke="#190c02" stroke-width="2" />
                <ellipse cx="50" cy="16" rx="25" ry="7" fill="#5a2f0a" stroke="#190c02" stroke-width="1.5" />
                <ellipse cx="50" cy="16" rx="16" ry="4.5" fill="none" stroke="#3a1e05" stroke-width="1" />
                <ellipse cx="50" cy="16" rx="8" ry="2" fill="none" stroke="#7a4213" stroke-width="0.8" />
                <line x1="33" y1="23" x2="33" y2="88" stroke="#1d0c01" stroke-width="1.5" />
                <line x1="67" y1="23" x2="67" y2="88" stroke="#1d0c01" stroke-width="1.5" />
            </g>

            <!-- Layer 3: Animated Carving Chisel Tool -->
            <g class="active-chisel-tool">
                <path d="M 0,0 L 16,-6 L 18,0 L 2,6 Z" fill="url(#steel-blade)" stroke="#ffffff" stroke-width="0.8" />
                <rect x="-16" y="-3.5" width="17" height="7" rx="2" fill="#5a2f0a" stroke="#e5a93c" stroke-width="0.6" />
                <circle cx="18" cy="0" r="2.5" fill="#e5a93c" />
            </g>

            <defs>
                <linearGradient id="bark-texture" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#4a2608" />
                    <stop offset="50%" stop-color="#2d1704" />
                    <stop offset="100%" stop-color="#190c02" />
                </linearGradient>
                <linearGradient id="steel-blade" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ffffff" />
                    <stop offset="50%" stop-color="#cbd5e1" />
                    <stop offset="100%" stop-color="#64748b" />
                </linearGradient>
                <linearGradient id="carved-wood-bark" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#5a2f0a" />
                    <stop offset="50%" stop-color="#3a1e05" />
                    <stop offset="100%" stop-color="#241102" />
                </linearGradient>
                <linearGradient id="wood-brass" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#f5d061" />
                    <stop offset="100%" stop-color="#c86414" />
                </linearGradient>
                <linearGradient id="amber-oud-liquid" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(229, 169, 60, 0.9)" />
                    <stop offset="100%" stop-color="rgba(200, 100, 20, 0.9)" />
                </linearGradient>
            </defs>
        </svg>
        """

    else:
        # Beach Vibes LV Flacon (Default)
        raw_svg = f"""
        <svg viewBox="0 0 100 100" style="{svg_style}" class="{css_class}">
            <circle class="spray-cloud sc1" cx="66" cy="12" r="2.2" fill="rgba(0, 229, 255, 0.95)" />
            <circle class="spray-cloud sc2" cx="70" cy="9" r="3.0" fill="rgba(255, 183, 3, 0.9)" />
            <circle class="spray-cloud sc3" cx="74" cy="6" r="3.8" fill="rgba(0, 229, 255, 0.75)" />

            <g class="bottle-cap">
                <rect x="40" y="4" width="20" height="15" rx="2" fill="#0c1017" stroke="#1e293b" stroke-width="0.8" />
                <ellipse cx="50" cy="5.5" rx="9.5" ry="1.5" fill="#334155" />
                <rect x="39.5" y="17" width="21" height="3" rx="0.5" fill="url(#lv-gold)" stroke="#ffb703" stroke-width="0.4" />
                <circle cx="61" cy="12" r="1.2" fill="#00e5ff" />
            </g>

            <rect x="44" y="20" width="12" height="7" rx="0.8" fill="url(#lv-gold)" stroke="#d48806" stroke-width="0.5" />
            <line x1="44" y1="24.5" x2="56" y2="24.5" stroke="#ffffff" stroke-width="0.8" opacity="0.7" />

            <path d="M 32,32 C 32,27 40,27 44,27 L 56,27 C 60,27 68,27 68,32 L 68,82 C 68,87 63,89 50,89 C 37,89 32,87 32,82 Z" fill="url(#lv-crystal-glass)" stroke="url(#lv-bottle-stroke)" stroke-width="2.2" />
            <path d="M 33.5,42 L 66.5,42 L 66.5,81 C 66.5,85 62,87.5 50,87.5 C 38,87.5 33.5,85 33.5,81 Z" fill="url(#lv-elixir-liquid)" opacity="0.88" />
            <path d="M 33.5,79 L 66.5,79 L 66.5,82 C 66.5,86.5 61,88.5 50,88.5 C 39,88.5 33.5,86.5 33.5,82 Z" fill="rgba(255,255,255,0.22)" stroke="rgba(255,255,255,0.4)" stroke-width="0.8" />

            <path d="M 34.5,32 L 34.5,80" stroke="rgba(255,255,255,0.7)" stroke-width="1.8" stroke-linecap="round" />
            <path d="M 37.5,30 L 37.5,78" stroke="rgba(255,255,255,0.3)" stroke-width="0.8" />
            <path d="M 65.5,32 L 65.5,80" stroke="#00e5ff" stroke-width="1.5" stroke-linecap="round" opacity="0.6" />

            <rect x="38" y="46" width="24" height="24" rx="2" fill="rgba(3, 20, 36, 0.85)" stroke="url(#lv-gold)" stroke-width="1.2" />
            <rect x="39.5" y="47.5" width="21" height="21" rx="1" fill="none" stroke="#00e5ff" stroke-width="0.5" opacity="0.5" />
            <text x="50" y="55" font-family="'Plus Jakarta Sans', sans-serif" font-size="3.2" font-weight="800" fill="#00e5ff" text-anchor="middle" letter-spacing="0.4">PERFUME</text>
            <text x="50" y="60" font-family="'Plus Jakarta Sans', sans-serif" font-size="2.6" font-weight="700" fill="#ffb703" text-anchor="middle" letter-spacing="0.3">SCANNER</text>
            <line x1="43" y1="63" x2="57" y2="63" stroke="#00e5ff" stroke-width="0.5" />
            <text x="50" y="67.5" font-family="'Plus Jakarta Sans', sans-serif" font-size="1.8" font-weight="600" fill="#8ea8c3" text-anchor="middle" letter-spacing="0.2">EAU DE PARFUM</text>
            <line x1="50" y1="27" x2="50" y2="82" stroke="#00e5ff" stroke-width="1.2" stroke-dasharray="2,2" opacity="0.6" />

            <defs>
                <linearGradient id="lv-gold" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ffe699" />
                    <stop offset="50%" stop-color="#ffb703" />
                    <stop offset="100%" stop-color="#d48806" />
                </linearGradient>
                <linearGradient id="lv-bottle-stroke" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#00e5ff" />
                    <stop offset="50%" stop-color="#ffffff" />
                    <stop offset="100%" stop-color="#ffb703" />
                </linearGradient>
                <linearGradient id="lv-crystal-glass" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="rgba(0, 229, 255, 0.15)" />
                    <stop offset="100%" stop-color="rgba(2, 20, 36, 0.7)" />
                </linearGradient>
                <linearGradient id="lv-elixir-liquid" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(0, 229, 255, 0.55)" />
                    <stop offset="60%" stop-color="rgba(0, 180, 216, 0.65)" />
                    <stop offset="100%" stop-color="rgba(255, 183, 3, 0.5)" />
                </linearGradient>
            </defs>
        </svg>
        """

    return clean_html(raw_svg)

# Theme-Specific Header Banner & Animation Builder
def get_header_animation_html(theme_key: str, theme: dict) -> str:
    bottle_svg = get_theme_bottle_svg(theme_key, theme, is_floating=True)
    
    card_bg = theme['card_bg']
    card_border = theme['card_border']
    card_shadow = theme['card_shadow']
    accent = theme['accent']
    glow = theme['glow']
    wave_1 = theme.get('wave_1', '%2300e5ff')
    wave_2 = theme.get('wave_2', '%23ffb703')

    if "Crimson" in theme_key or "Cyber" in theme_key:
        bg_overlay = """
        <div style="position:absolute; inset:0; background-image: linear-gradient(to right, rgba(255,0,51,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,0,51,0.15) 1px, transparent 1px); background-size:20px 20px; opacity:0.4; pointer-events:none;"></div>
        <div style="position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, transparent 0%, #ff0033 50%, transparent 100%); box-shadow:0 0 15px #ff0033; animation: laser-sweep 2.5s ease-in-out infinite; z-index:2;"></div>
        """
    elif "Floral" in theme_key:
        bg_overlay = """
        <div style="position:absolute; inset:0; overflow:hidden; pointer-events:none; z-index:1;">
            <div style="position:absolute; font-size:1.8rem; left:6%; top:12%; opacity:0.9; animation: float-petal-1 6s ease-in-out infinite;">🌸</div>
            <div style="position:absolute; font-size:1.5rem; left:18%; top:50%; opacity:0.85; animation: float-petal-2 7s ease-in-out infinite 1s;">🌺</div>
            <div style="position:absolute; font-size:1.7rem; left:26%; top:18%; opacity:0.9; animation: float-petal-3 5.5s ease-in-out infinite 2s;">🌹</div>
            <div style="position:absolute; font-size:1.4rem; left:36%; top:62%; opacity:0.85; animation: float-petal-1 8s ease-in-out infinite 0.5s;">🌷</div>
            <div style="position:absolute; font-size:1.6rem; left:56%; top:12%; opacity:0.9; animation: float-petal-2 6.5s ease-in-out infinite 1.5s;">🌸</div>
            <div style="position:absolute; font-size:1.5rem; left:70%; top:58%; opacity:0.85; animation: float-petal-3 7.5s ease-in-out infinite 2.5s;">🌺</div>
            <div style="position:absolute; font-size:1.4rem; left:84%; top:15%; opacity:0.85; animation: float-petal-1 5s ease-in-out infinite 3s;">🌿</div>
            <div style="position:absolute; font-size:1.3rem; left:12%; top:32%; opacity:0.8; animation: float-petal-2 9s ease-in-out infinite 4s;">🌸</div>
            <div style="position:absolute; font-size:1.5rem; left:66%; top:38%; opacity:0.85; animation: float-petal-3 6s ease-in-out infinite 0.8s;">🌹</div>
            <div style="position:absolute; font-size:1.4rem; left:90%; top:65%; opacity:0.8; animation: float-petal-1 7.2s ease-in-out infinite 1.8s;">🌷</div>
            <div style="position:absolute; font-size:1.4rem; left:44%; top:58%; opacity:0.85; animation: float-petal-2 6.8s ease-in-out infinite 2.2s;">🌷</div>
            <div style="position:absolute; font-size:1.5rem; left:60%; top:58%; opacity:0.85; animation: float-petal-3 7.0s ease-in-out infinite 1.2s;">🌺</div>
        </div>
        """
    elif "Woody" in theme_key or "Oud" in theme_key:
        bg_overlay = """
        <div style="position:absolute; width:6px; height:6px; background:#e5a93c; border-radius:50%; box-shadow:0 0 10px #e5a93c; left:20%; bottom:10px; animation: ember-up 3s ease-out infinite;"></div>
        <div style="position:absolute; width:8px; height:8px; background:#c86414; border-radius:50%; box-shadow:0 0 12px #c86414; right:25%; bottom:15px; animation: ember-up 3.8s ease-out infinite 1s;"></div>
        """
    else:
        bg_overlay = f"""
        <div style="position:absolute; left:-100%; width:300%; height:100%; bottom:0; pointer-events:none; z-index:1; opacity:0.38; background: repeat-x url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0,20 C150,90 350,-20 500,50 C650,110 900,10 1200,40 L1200,120 L0,120 Z' fill='{wave_1}'%3E%3C/path%3E%3C/svg%3E&quot;); background-size:600px 100%; animation: wave-roll-1 7s linear infinite;"></div>
        <div style="position:absolute; left:-100%; width:300%; height:100%; bottom:0; pointer-events:none; z-index:1; opacity:0.28; background: repeat-x url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0,40 C200,-10 400,80 600,30 C800,-30 1000,70 1200,20 L1200,120 L0,120 Z' fill='{wave_2}'%3E%3C/path%3E%3C/svg%3E&quot;); background-size:700px 100%; animation: wave-roll-2 11s linear infinite;"></div>
        """

    if "Beach" in theme_key:
        bottle_anim_css = f"""
        @keyframes surf-waves-bottle {{
            0% {{ transform: translate(-220px, 0px) rotate(-8deg); }}
            25% {{ transform: translate(-110px, -14px) rotate(6deg); }}
            50% {{ transform: translate(0px, -4px) rotate(-6deg); }}
            75% {{ transform: translate(110px, -16px) rotate(8deg); }}
            100% {{ transform: translate(220px, 0px) rotate(-6deg); }}
        }}
        .hero-wave-bottle-center svg,
        .hero-wave-bottle-center .floating-bottle {{
            width: 110px !important;
            height: 110px !important;
            max-width: 110px !important;
            max-height: 110px !important;
            filter: drop-shadow(0 10px 22px {glow}) !important;
            animation: surf-waves-bottle 10s ease-in-out infinite alternate !important;
        }}
        """
    elif "Cyber" in theme_key or "Crimson" in theme_key:
        bottle_anim_css = """
        @keyframes cyber-hud-hover {
            0%, 100% { transform: translateY(0px) scale(1); filter: drop-shadow(0 0 20px #ff0055) drop-shadow(0 0 35px rgba(255, 204, 0, 0.6)); }
            50% { transform: translateY(-12px) scale(1.05); filter: drop-shadow(0 0 32px #ff0055) drop-shadow(0 0 55px rgba(255, 0, 51, 0.8)); }
        }
        @keyframes spin-reticle {
            0% { transform: rotate(0deg); transform-origin: 50px 53px; }
            100% { transform: rotate(360deg); transform-origin: 50px 53px; }
        }
        .cyber-reticle {
            animation: spin-reticle 8s linear infinite;
        }
        .hero-wave-bottle-center svg,
        .hero-wave-bottle-center .floating-bottle {
            width: 115px !important;
            height: 115px !important;
            max-width: 115px !important;
            max-height: 115px !important;
            animation: cyber-hud-hover 3.2s ease-in-out infinite !important;
        }
        """
    elif "Floral" in theme_key:
        bottle_anim_css = f"""
        @keyframes press-spray-cap {{
            0%, 15%, 85%, 100% {{ transform: translateY(0); }}
            20%, 30% {{ transform: translateY(3.5px); }}
        }}

        .bottle-cap {{
            animation: press-spray-cap 4s ease-in-out infinite !important;
            transform-origin: 50px 15px;
        }}

        /* Active Spray Bursts Erupting Out from Nozzle Tip (61, 11) */
        @keyframes emit-fill-1 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            20% {{ opacity: 1; transform: translate(15px, -15px) scale(0.8) rotate(45deg); }}
            50% {{ opacity: 0.95; transform: translate(90px, -45px) scale(1.3) rotate(160deg); }}
            85% {{ opacity: 0.8; transform: translate(190px, -15px) scale(1) rotate(320deg); }}
            100% {{ opacity: 0; transform: translate(260px, 25px) scale(0.7) rotate(420deg); }}
        }}

        @keyframes emit-fill-2 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            22% {{ opacity: 1; transform: translate(-15px, -12px) scale(0.7) rotate(-45deg); }}
            50% {{ opacity: 0.95; transform: translate(-85px, -40px) scale(1.2) rotate(-140deg); }}
            85% {{ opacity: 0.8; transform: translate(-180px, 15px) scale(0.95) rotate(-280deg); }}
            100% {{ opacity: 0; transform: translate(-250px, 55px) scale(0.7) rotate(-380deg); }}
        }}

        @keyframes emit-fill-3 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            24% {{ opacity: 1; transform: translate(12px, -22px) scale(0.75) rotate(30deg); }}
            55% {{ opacity: 0.9; transform: translate(60px, -65px) scale(1.25) rotate(190deg); }}
            88% {{ opacity: 0.75; transform: translate(140px, -85px) scale(0.9) rotate(340deg); }}
            100% {{ opacity: 0; transform: translate(210px, -95px) scale(0.65) rotate(450deg); }}
        }}

        @keyframes emit-fill-4 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            20% {{ opacity: 1; transform: translate(-12px, -20px) scale(0.7) rotate(-30deg); }}
            52% {{ opacity: 0.95; transform: translate(-70px, -60px) scale(1.3) rotate(-180deg); }}
            85% {{ opacity: 0.8; transform: translate(-150px, -75px) scale(0.85) rotate(-310deg); }}
            100% {{ opacity: 0; transform: translate(-220px, -85px) scale(0.6) rotate(-400deg); }}
        }}

        @keyframes emit-fill-5 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            26% {{ opacity: 1; transform: translate(0px, -28px) scale(0.75) rotate(60deg); }}
            58% {{ opacity: 0.9; transform: translate(25px, -75px) scale(1.35) rotate(210deg); }}
            88% {{ opacity: 0.75; transform: translate(45px, -115px) scale(0.95) rotate(360deg); }}
            100% {{ opacity: 0; transform: translate(65px, -145px) scale(0.6) rotate(480deg); }}
        }}

        @keyframes emit-fill-6 {{
            0%, 15% {{ transform: translate(0, 0) scale(0.1) rotate(0deg); opacity: 0; }}
            22% {{ opacity: 1; transform: translate(-15px, 15px) scale(0.7) rotate(-50deg); }}
            55% {{ opacity: 0.9; transform: translate(-90px, 35px) scale(1.2) rotate(-220deg); }}
            88% {{ opacity: 0.75; transform: translate(-160px, 50px) scale(0.85) rotate(-360deg); }}
            100% {{ opacity: 0; transform: translate(-210px, 65px) scale(0.6) rotate(-460deg); }}
        }}

        .emitted-petal {{ transform-origin: center; }}
        .emitted-petal.ep1 {{ animation: emit-fill-1 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; }}
        .emitted-petal.ep2 {{ animation: emit-fill-2 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; animation-delay: 0.1s !important; }}
        .emitted-petal.ep3 {{ animation: emit-fill-3 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; animation-delay: 0.2s !important; }}
        .emitted-petal.ep4 {{ animation: emit-fill-4 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; animation-delay: 0.3s !important; }}
        .emitted-petal.ep5 {{ animation: emit-fill-5 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; animation-delay: 0.4s !important; }}
        .emitted-petal.ep6 {{ animation: emit-fill-6 4s cubic-bezier(0.16, 1, 0.3, 1) infinite !important; animation-delay: 0.5s !important; }}

        @keyframes floral-breeze-float {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); filter: drop-shadow(0 8px 20px {glow}); }}
            50% {{ transform: translateY(-12px) rotate(3deg); filter: drop-shadow(0 14px 28px {glow}); }}
        }}
        .hero-wave-bottle-center svg,
        .hero-wave-bottle-center .floating-bottle {{
            width: 110px !important;
            height: 110px !important;
            max-width: 110px !important;
            max-height: 110px !important;
            animation: floral-breeze-float 4.2s ease-in-out infinite !important;
        }}
        """
    else:
        bottle_anim_css = f"""
        @keyframes wood-center-float {{
            0%, 100% {{ transform: translateY(0px); filter: drop-shadow(0 8px 20px {glow}); }}
            50% {{ transform: translateY(-8px); filter: drop-shadow(0 14px 26px {glow}); }}
        }}
        .hero-wave-bottle-center svg,
        .hero-wave-bottle-center .floating-bottle {{
            width: 110px !important;
            height: 110px !important;
            max-width: 110px !important;
            max-height: 110px !important;
            animation: wood-center-float 4.5s ease-in-out infinite !important;
        }}
        """

    header_html = f"""
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2.2rem 2rem 1.8rem 2rem; margin: 0.8rem auto 1rem auto; background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 24px; overflow: hidden; max-width: 680px; width: 100%; box-shadow: 0 12px 45px rgba(0, 0, 0, 0.75), inset 0 0 30px {card_shadow}; backdrop-filter: blur(16px); font-family: 'Plus Jakarta Sans', sans-serif;">
        <style>
            .hero-wave-bottle-center {{
                position: relative;
                z-index: 5;
                margin-bottom: 0.8rem;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
            }}
            {bottle_anim_css}
            @keyframes wave-roll-1 {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(600px); }}
            }}
            @keyframes wave-roll-2 {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(-700px); }}
            }}
            @keyframes laser-sweep {{
                0% {{ top: 0%; opacity: 0; }}
                15% {{ opacity: 1; }}
                85% {{ opacity: 1; }}
                100% {{ top: 100%; opacity: 0; }}
            }}
            @keyframes float-petal-1 {{
                0% {{ transform: translateY(0px) rotate(0deg) scale(0.9); opacity: 0.3; }}
                50% {{ transform: translateY(-16px) rotate(180deg) scale(1.1); opacity: 0.95; }}
                100% {{ transform: translateY(-32px) rotate(360deg) scale(0.9); opacity: 0.3; }}
            }}
            @keyframes float-petal-2 {{
                0% {{ transform: translateY(0px) rotate(0deg) scale(1); opacity: 0.35; }}
                50% {{ transform: translateY(-20px) rotate(-150deg) scale(0.85); opacity: 1; }}
                100% {{ transform: translateY(-38px) rotate(-300deg) scale(1); opacity: 0.35; }}
            }}
            @keyframes float-petal-3 {{
                0% {{ transform: translateY(0px) rotate(0deg) scale(0.85); opacity: 0.3; }}
                50% {{ transform: translateY(-18px) rotate(120deg) scale(1.15); opacity: 0.9; }}
                100% {{ transform: translateY(-34px) rotate(240deg) scale(0.85); opacity: 0.3; }}
            }}
            @keyframes ember-up {{
                0% {{ bottom: 5px; transform: scale(0.4); opacity: 0; }}
                30% {{ opacity: 0.9; }}
                100% {{ bottom: 65px; transform: scale(1.5); opacity: 0; }}
            }}
            .bottle-cap {{
                animation: press-cap 2.5s ease-in-out infinite;
                transform-origin: 50px 15px;
            }}
            @keyframes press-cap {{
                0%, 40%, 100% {{ transform: translateY(0); }}
                60%, 80% {{ transform: translateY(2.5px); }}
            }}
            .spray-cloud {{
                opacity: 0;
                animation: spray-out 2.5s cubic-bezier(0.16, 1, 0.3, 1) infinite;
                transform-origin: 61px 12px;
            }}
            @keyframes spray-out {{
                0%, 55% {{ transform: translate(0, 0) scale(1); opacity: 0; }}
                60% {{ opacity: 0.85; }}
                90% {{ opacity: 0.15; }}
                100% {{ transform: translate(28px, -4px) scale(6); opacity: 0; }}
            }}
            @keyframes chisel-carving-motion {{
                0% {{ transform: translate(15px, 20px) rotate(35deg); opacity: 0; }}
                10% {{ opacity: 1; }}
                45% {{ transform: translate(18px, 78px) rotate(15deg); opacity: 1; }}
                50% {{ transform: translate(82px, 20px) rotate(-145deg); opacity: 1; }}
                90% {{ transform: translate(80px, 78px) rotate(-165deg); opacity: 1; }}
                100% {{ transform: translate(15px, 20px) rotate(35deg); opacity: 0; }}
            }}
            .chisel-blade-tool {{
                transform-origin: 0 0;
                animation: chisel-carving-motion 3.5s cubic-bezier(0.4, 0, 0.2, 1) infinite !important;
            }}
            .raw-bark-layer {{
                animation: bark-fade 3.5s ease-in-out infinite !important;
            }}
            @keyframes bark-fade {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.25; }}
            }}
            .shaving.s1 {{ animation: shaving-left 3.5s ease-out infinite !important; }}
            .shaving.s2 {{ animation: shaving-right 3.5s ease-out infinite !important; animation-delay: 1.8s !important; }}
            @keyframes shaving-left {{
                0% {{ transform: translate(10px, 0) scale(0.4); opacity: 0; }}
                20% {{ opacity: 1; }}
                45% {{ transform: translate(-30px, 20px) rotate(-120deg) scale(1.4); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}
            @keyframes shaving-right {{
                0% {{ transform: translate(-10px, 0) scale(0.4); opacity: 0; }}
                20% {{ opacity: 1; }}
                45% {{ transform: translate(30px, 20px) rotate(120deg) scale(1.4); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}
        </style>
        
        {bg_overlay}
        
        <div class="hero-wave-bottle-center">
            {bottle_svg}
        </div>
        
        <h1 style="font-size: 2.3rem; font-weight: 900; letter-spacing: 0.16em; margin: 0; text-transform: uppercase; position: relative; z-index: 5; text-align: center; width: 100%; color: {accent}; text-shadow: 0 0 25px {glow}, 0 0 45px {glow}; font-family: 'Plus Jakarta Sans', sans-serif;">
            PERFUME SCANNER
        </h1>
    </div>
    """
    return clean_html(header_html)

# Theme-Specific Scanner Box HTML Generator
def get_scanner_html(theme_key: str, theme: dict, stage_text: str, sub_text: str) -> str:
    bottle_svg = get_theme_bottle_svg(theme_key, theme, is_floating=False)
    
    if "Crimson" in theme_key or "Cyber" in theme_key:
        overlay_elements = """
        <div class="cyber-scan-grid"></div>
        <div class="cyber-laser-bar"></div>
        """
    elif "Floral" in theme_key:
        overlay_elements = """
        <div class="floating-petals-box">
            <span class="fp p1">🌸</span>
            <span class="fp p2">🌺</span>
            <span class="fp p3">🌹</span>
            <span class="fp p4">🌿</span>
        </div>
        """
    elif "Woody" in theme_key or "Oud" in theme_key:
        overlay_elements = """
        <div class="wood-smoke-cloud">
            <div class="ember-particle ep1"></div>
            <div class="ember-particle ep2"></div>
            <div class="ember-particle ep3"></div>
        </div>
        """
    else:
        overlay_elements = """
        <div class="mist-cloud">
            <div class="mist-particle p1"></div>
            <div class="mist-particle p2"></div>
            <div class="mist-particle p3"></div>
            <div class="mist-particle p4"></div>
            <div class="mist-particle p5"></div>
            <div class="mist-particle p6"></div>
        </div>
        """

    scanner_html = f"""
    <div class="spray-box">
        <div class="spray-container">
            {bottle_svg}
            {overlay_elements}
        </div>
        <div class="scanner-text">{stage_text}</div>
        <div class="scanning-subtext">{sub_text}</div>
    </div>
    """
    return clean_html(scanner_html)

# Session State Theme Manager
if "active_theme_key" not in st.session_state:
    st.session_state["active_theme_key"] = "Beach Vibes 🌊"

theme = THEMES[st.session_state["active_theme_key"]]

# Top Right Luxury Theme Button Popover
top_bar_c1, top_bar_c2 = st.columns([4.2, 1.8])
with top_bar_c2, st.popover("✏️ Customize Theme", use_container_width=False, help="Click to switch luxury fragrance theme & bottle animators"):
    st.markdown(
        f"""
        <div style="font-size:0.75rem; font-weight:800; color:{theme['sub_text']}; text-transform:uppercase; letter-spacing:0.12em; text-align:center; padding-bottom:8px; border-bottom:1px solid {theme['card_border']}; margin-bottom:8px;">
            Select Luxury Theme
        </div>
        """,
        unsafe_allow_html=True
    )
    for t_key in THEMES:
        is_active = (t_key == st.session_state["active_theme_key"])
        btn_label = f"{'✨ ' if is_active else '   '}{t_key}"
        if st.button(btn_label, key=f"popover_theme_{t_key}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state["active_theme_key"] = t_key
            st.rerun()

# Dynamic Theme Injector CSS
st.markdown(
    clean_html(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        
        <style>
            [data-testid="stAppViewContainer"] {{
                background-color: {theme['bg_base']} !important;
                background-image: {theme['bg_radial']} !important;
                color: #ffffff !important;
            }}
            
            [data-testid="stHeader"] {{
                background-color: {theme['header_bg']} !important;
                backdrop-filter: blur(8px);
            }}

            [data-testid="stSidebar"] {{
                background-color: {theme['header_bg']} !important;
                backdrop-filter: blur(14px);
                border-right: 1px solid {theme['card_border']} !important;
            }}

            /* Floating Pill Theme Button (Theme Blended Glass Style) */
            div[data-testid="stPopover"],
            .stPopover {{
                display: flex !important;
                justify-content: flex-end !important;
            }}

            div[data-testid="stPopover"] button,
            .stPopover button,
            button[aria-haspopup="dialog"] {{
                background: {theme['card_bg']} !important;
                background-color: {theme['card_bg']} !important;
                color: #ffffff !important;
                border: 1.5px solid {theme['card_border']} !important;
                border-radius: 999px !important;
                padding: 0.45rem 1.4rem !important;
                font-weight: 800 !important;
                font-size: 0.9rem !important;
                box-shadow: 0 4px 20px {theme['card_shadow']} !important;
                backdrop-filter: blur(16px) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                margin-top: 4px !important;
                width: auto !important;
                min-width: 170px !important;
            }}

            div[data-testid="stPopover"] button:hover,
            .stPopover button:hover,
            button[aria-haspopup="dialog"]:hover {{
                background: {theme['accent']} !important;
                background-color: {theme['accent']} !important;
                color: {theme['bg_base']} !important;
                border-color: #ffffff !important;
                box-shadow: 0 6px 25px {theme['glow']} !important;
                transform: translateY(-2px) !important;
            }}

            div[data-testid="stPopover"] button *,
            .stPopover button *,
            button[aria-haspopup="dialog"] * {{
                color: #ffffff !important;
                font-weight: 800 !important;
                font-size: 0.9rem !important;
            }}

            div[data-testid="stPopover"] button:hover *,
            .stPopover button:hover *,
            button[aria-haspopup="dialog"]:hover * {{
                color: {theme['bg_base']} !important;
            }}

            /* Popover Floating Overlay Box */
            div[data-testid="stPopoverBody"] {{
                background-color: {theme['bg_base']} !important;
                background: {theme['bg_base']} !important;
                border: 1.5px solid {theme['card_border']} !important;
                border-radius: 18px !important;
                box-shadow: 0 14px 45px rgba(0, 0, 0, 0.95), 0 0 25px {theme['card_shadow']} !important;
                padding: 12px !important;
            }}

            li[data-baseweb="option"] {{
                color: #ffffff !important;
                background-color: transparent !important;
                font-size: 0.95rem !important;
                font-weight: 700 !important;
                border-radius: 8px !important;
                padding: 10px 14px !important;
                transition: all 0.2s ease !important;
            }}

            li[data-baseweb="option"]:hover,
            li[data-baseweb="option"][aria-selected="true"] {{
                background-color: {theme['card_bg']} !important;
                color: {theme['accent']} !important;
                border-left: 3px solid {theme['accent']} !important;
            }}
            
            * {{
                font-family: 'Plus Jakarta Sans', sans-serif;
            }}
            
            .high-tech-header-wrap {{
                position: relative;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                align-items: center !important;
                padding: 1.8rem 1.5rem 1.4rem 1.5rem !important;
                margin: 0.8rem auto 1rem auto !important;
                background: {theme['card_bg']} !important;
                border: 1.5px solid {theme['card_border']} !important;
                border-radius: 24px !important;
                overflow: visible !important;
                max-width: 680px !important;
                width: 100% !important;
                box-shadow: 0 12px 45px rgba(0, 0, 0, 0.7), inset 0 0 30px {theme['card_shadow']} !important;
                backdrop-filter: blur(16px);
            }}
            
            /* Center Hero Bottle Directly Above Title */
            .hero-bottle-center {{
                position: relative;
                z-index: 10;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 125px;
                height: 125px;
            }}

            .hero-bottle-center svg,
            .hero-bottle-center .floating-bottle {{
                width: 125px !important;
                height: 125px !important;
                filter: drop-shadow(0 10px 25px {theme['glow']}) !important;
                animation: float 4s ease-in-out infinite !important;
            }}

            /* Beach Sea Waves */
            .sea-wave-layer {{
                position: absolute;
                left: -100%;
                width: 300%;
                height: 100%;
                bottom: 0;
                pointer-events: none;
                z-index: 1;
            }}
            
            .wave-1 {{
                background: repeat-x url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0,20 C150,90 350,-20 500,50 C650,110 900,10 1200,40 L1200,120 L0,120 Z' fill='{theme['wave_1']}'%3E%3C/path%3E%3C/svg%3E");
                background-size: 600px 100%;
                animation: wave-roll-1 7s linear infinite;
                opacity: 0.35;
            }}
            
            .wave-2 {{
                background: repeat-x url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0,40 C200,-10 400,80 600,30 C800,-30 1000,70 1200,20 L1200,120 L0,120 Z' fill='{theme['wave_2']}'%3E%3C/path%3E%3C/svg%3E");
                background-size: 700px 100%;
                animation: wave-roll-2 11s linear infinite;
                opacity: 0.25;
            }}
            
            @keyframes wave-roll-1 {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(600px); }}
            }}
            
            @keyframes wave-roll-2 {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(-700px); }}
            }}

            /* Cyberpunk Laser Grid Animation */
            .cyber-scan-grid {{
                position: absolute;
                inset: 0;
                background-image: linear-gradient(to right, rgba(255,0,51,0.15) 1px, transparent 1px),
                                  linear-gradient(to bottom, rgba(255,0,51,0.15) 1px, transparent 1px);
                background-size: 20px 20px;
                opacity: 0.4;
                pointer-events: none;
            }}

            .cyber-laser-bar {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, transparent 0%, #ff0033 50%, transparent 100%);
                box-shadow: 0 0 15px #ff0033;
                animation: laser-sweep 2.5s ease-in-out infinite;
                z-index: 2;
            }}

            @keyframes laser-sweep {{
                0% {{ top: 0%; opacity: 0; }}
                15% {{ opacity: 1; }}
                85% {{ opacity: 1; }}
                100% {{ top: 100%; opacity: 0; }}
            }}

            /* Floral Floating Petals */
            .floating-petal {{
                position: absolute;
                font-size: 1.2rem;
                opacity: 0;
                pointer-events: none;
                animation: petal-drift 4s ease-in-out infinite;
                z-index: 2;
            }}

            .petal-1 {{ left: 15%; animation-delay: 0s; }}
            .petal-2 {{ left: 35%; animation-delay: 1.2s; }}
            .petal-3 {{ left: 65%; animation-delay: 0.6s; }}
            .petal-4 {{ left: 85%; animation-delay: 2s; }}

            @keyframes petal-drift {{
                0% {{ transform: translateY(-10px) rotate(0deg); opacity: 0; }}
                20% {{ opacity: 0.9; }}
                80% {{ opacity: 0.7; }}
                100% {{ transform: translateY(80px) rotate(180deg); opacity: 0; }}
            }}

            /* Woody Amber Embers */
            .wood-ember {{
                position: absolute;
                width: 6px;
                height: 6px;
                background: radial-gradient(circle, #e5a93c 0%, #c86414 100%);
                border-radius: 50%;
                box-shadow: 0 0 8px #e5a93c;
                opacity: 0;
                animation: ember-rise 3.2s ease-out infinite;
                z-index: 2;
            }}

            .ember-1 {{ left: 20%; animation-delay: 0s; }}
            .ember-2 {{ left: 50%; animation-delay: 1s; }}
            .ember-3 {{ left: 80%; animation-delay: 2s; }}

            @keyframes ember-rise {{
                0% {{ bottom: 5px; transform: scale(0.4); opacity: 0; }}
                30% {{ opacity: 0.9; }}
                100% {{ bottom: 65px; transform: scale(1.5); opacity: 0; }}
            }}

            /* Wood Carving Chisel Tool Motion & Shavings */
            .chisel-blade-tool {{
                transform-origin: 0 0;
                animation: chisel-carving-motion 3.5s cubic-bezier(0.4, 0, 0.2, 1) infinite !important;
            }}

            @keyframes chisel-carving-motion {{
                0% {{ transform: translate(15px, 20px) rotate(35deg); opacity: 0; }}
                10% {{ opacity: 1; }}
                45% {{ transform: translate(18px, 78px) rotate(15deg); opacity: 1; }}
                50% {{ transform: translate(82px, 20px) rotate(-145deg); opacity: 1; }}
                90% {{ transform: translate(80px, 78px) rotate(-165deg); opacity: 1; }}
                100% {{ transform: translate(15px, 20px) rotate(35deg); opacity: 0; }}
            }}

            .raw-bark-layer {{
                animation: bark-carve-peel 3.5s ease-in-out infinite !important;
                transform-origin: 50% 50%;
            }}

            @keyframes bark-carve-peel {{
                0%, 100% {{ opacity: 1; clip-path: polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%); }}
                40% {{ clip-path: polygon(0% 0%, 50% 0%, 35% 100%, 0% 100%); opacity: 0.8; }}
                80% {{ clip-path: polygon(50% 0%, 100% 0%, 100% 100%, 65% 100%); opacity: 0.4; }}
            }}

            .shaving.s1 {{ animation: shaving-left 3.5s ease-out infinite !important; }}
            .shaving.s2 {{ animation: shaving-right 3.5s ease-out infinite !important; animation-delay: 1.8s !important; }}
            .shaving.s3 {{ animation: shaving-left 3.5s ease-out infinite !important; animation-delay: 0.8s !important; }}

            .chip.c1 {{ animation: chip-fly-1 3.5s ease-out infinite !important; }}
            .chip.c2 {{ animation: chip-fly-2 3.5s ease-out infinite !important; animation-delay: 1.5s !important; }}
            .chip.c3 {{ animation: chip-fly-1 3.5s ease-out infinite !important; animation-delay: 1s !important; }}

            @keyframes shaving-left {{
                0% {{ transform: translate(10px, 0) scale(0.4); opacity: 0; }}
                20% {{ opacity: 1; }}
                45% {{ transform: translate(-30px, 20px) rotate(-120deg) scale(1.4); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}

            @keyframes shaving-right {{
                0% {{ transform: translate(-10px, 0) scale(0.4); opacity: 0; }}
                20% {{ opacity: 1; }}
                45% {{ transform: translate(30px, 20px) rotate(120deg) scale(1.4); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}

            @keyframes chip-fly-1 {{
                0% {{ transform: translate(0, 0); opacity: 0; }}
                25% {{ opacity: 1; }}
                50% {{ transform: translate(-25px, -15px); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}

            @keyframes chip-fly-2 {{
                0% {{ transform: translate(0, 0); opacity: 0; }}
                25% {{ opacity: 1; }}
                50% {{ transform: translate(25px, -15px); opacity: 0; }}
                100% {{ opacity: 0; }}
            }}

            @keyframes bottle-sea-bob {{
                0%, 100% {{ transform: translateY(0px) rotate(-5deg); }}
                50% {{ transform: translateY(-9px) rotate(6deg); }}
            }}
            
            .futuristic-title {{
                font-size: 2.4rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.14em !important;
                margin: 0 !important;
                padding: 0.3rem 0 !important;
                text-transform: uppercase !important;
                position: relative !important;
                z-index: 3 !important;
                white-space: nowrap !important;
                text-align: center !important;
                width: 100% !important;
                background: {theme['title_gradient']} !important;
                background-size: 250% auto !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                animation: wave-pass 4s linear infinite, theme-glow 3s ease-in-out infinite !important;
            }}
            
            @keyframes wave-pass {{
                0% {{ background-position: 250% center; }}
                100% {{ background-position: -250% center; }}
            }}
            
            @keyframes theme-glow {{
                0%, 100% {{ filter: drop-shadow(0 0 10px {theme['glow']}); }}
                50% {{ filter: drop-shadow(0 0 25px {theme['glow']}) drop-shadow(0 0 35px {theme['glow_alt']}); }}
            }}
            
            .sub-header {{
                text-align: center;
                font-size: 1.1rem;
                color: {theme['sub_text']};
                margin-bottom: 2rem;
                font-weight: 400;
            }}
            
            .logo-container {{
                display: flex;
                justify-content: center;
                margin-top: 1rem;
                margin-bottom: 1rem;
            }}
            
            .logo-container .floating-bottle {{
                width: 150px !important;
                height: 150px !important;
                filter: drop-shadow(0 12px 28px {theme['card_shadow']});
                animation: float 4s ease-in-out infinite !important;
            }}

            .spray-container .spray-bottle {{
                width: 110px !important;
                height: 110px !important;
                filter: drop-shadow(0 8px 22px {theme['glow']});
                animation: float 3.5s ease-in-out infinite !important;
            }}

            /* Segmented Luxury Theme Control Pills */
            div[data-testid="stColumn"] button[key^="theme_segmented_"] {{
                border-radius: 30px !important;
                font-weight: 800 !important;
                font-size: 0.9rem !important;
                padding: 0.55rem 1rem !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                backdrop-filter: blur(12px) !important;
            }}

            /* Inactive Theme Pill */
            div[data-testid="stColumn"] button[key^="theme_segmented_"][data-testid="stBaseButton-secondary"] {{
                background: {theme['card_bg']} !important;
                background-color: {theme['card_bg']} !important;
                color: {theme['sub_text']} !important;
                border: 1.5px solid {theme['card_border']} !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
            }}

            div[data-testid="stColumn"] button[key^="theme_segmented_"][data-testid="stBaseButton-secondary"]:hover {{
                background: {theme['bg_base']} !important;
                color: #ffffff !important;
                border-color: {theme['accent']} !important;
                transform: translateY(-2px) scale(1.03) !important;
                box-shadow: 0 6px 20px {theme['card_shadow']} !important;
            }}

            /* Active Theme Pill */
            div[data-testid="stColumn"] button[key^="theme_segmented_"][data-testid="stBaseButton-primary"] {{
                background: {theme['button_bg']} !important;
                color: {theme['button_text']} !important;
                border: 2px solid {theme['accent']} !important;
                box-shadow: 0 6px 22px {theme['glow']} !important;
                transform: scale(1.04) !important;
            }}
            
            .bottle-cap {{
                animation: press-cap 2.5s ease-in-out infinite;
                transform-origin: 50px 15px;
            }}
            
            .spray-cloud {{
                opacity: 0;
                animation: spray-out 2.5s cubic-bezier(0.16, 1, 0.3, 1) infinite;
                transform-origin: 61px 12px;
                filter: blur(0.5px);
            }}
            
            .sc1 {{ animation-delay: 0.8s; }}
            .sc2 {{ animation-delay: 1.1s; }}
            .sc3 {{ animation-delay: 1.4s; }}
            
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-6px); }}
            }}
            
            @keyframes press-cap {{
                0%, 40%, 100% {{ transform: translateY(0); }}
                60%, 80% {{ transform: translateY(2.5px); }}
            }}
            
            @keyframes spray-out {{
                0%, 55% {{
                    transform: translate(0, 0) scale(1);
                    opacity: 0;
                }}
                60% {{
                    opacity: 0.85;
                }}
                90% {{
                    opacity: 0.15;
                }}
                100% {{
                    transform: translate(28px, -4px) scale(6);
                    opacity: 0;
                }}
            }}
            
            .deals-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }}
            
            .deal-card {{
                background: {theme['card_bg']} !important;
                border: 1px solid {theme['card_border']} !important;
                border-radius: 16px !important;
                padding: 1.5rem !important;
                backdrop-filter: blur(14px) !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
                overflow: hidden !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: space-between !important;
                min-height: 440px !important;
            }}
            
            .deal-card:hover {{
                transform: translateY(-5px) !important;
                border-color: {theme['accent']} !important;
                box-shadow: 0 10px 25px {theme['card_shadow']} !important;
            }}
            
            .cheapest-card {{
                background: linear-gradient(135deg, {theme['card_bg']} 0%, {theme['card_shadow']} 100%) !important;
                border: 1.5px solid {theme['accent']} !important;
                box-shadow: 0 8px 32px {theme['card_shadow']} !important;
            }}
            
            .cheapest-card:hover {{
                border-color: {theme['secondary']} !important;
                box-shadow: 0 12px 35px {theme['card_shadow']} !important;
            }}
            
            .product-image-container {{
                width: 100% !important;
                height: 190px !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                background: rgba(255, 255, 255, 0.04) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-bottom: 1.25rem !important;
                border: 1px solid {theme['card_border']} !important;
                box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3) !important;
                position: relative !important;
            }}
            
            .product-image {{
                max-width: 90% !important;
                max-height: 90% !important;
                object-fit: contain !important;
                transition: transform 0.5s ease !important;
                padding: 4px !important;
            }}
            
            .deal-card:hover .product-image {{
                transform: scale(1.06) !important;
            }}
            
            .badge {{
                position: absolute !important;
                top: 1rem !important;
                right: 1rem !important;
                font-size: 0.7rem !important;
                font-weight: 700 !important;
                padding: 0.25rem 0.65rem !important;
                border-radius: 20px !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                z-index: 10 !important;
            }}
            
            .cheapest-badge {{
                background: linear-gradient(135deg, {theme['secondary']}, {theme['accent']}) !important;
                color: #ffffff !important;
                box-shadow: 0 2px 10px {theme['card_shadow']} !important;
            }}
            
            .real-badge {{
                background-color: {theme['card_shadow']} !important;
                color: {theme['accent']} !important;
                border: 1px solid {theme['card_border']} !important;
            }}
            
            .retailer-name {{
                font-size: 0.85rem !important;
                text-transform: uppercase !important;
                letter-spacing: 0.1em !important;
                color: {theme['sub_text']} !important;
                font-weight: 700 !important;
                margin-bottom: 0.4rem !important;
            }}
            
            .product-title {{
                font-size: 1.12rem !important;
                font-weight: 600 !important;
                color: #ffffff !important;
                margin-bottom: 1rem !important;
                line-height: 1.4 !important;
                display: -webkit-box !important;
                -webkit-line-clamp: 2 !important;
                -webkit-box-orient: vertical !important;
                overflow: hidden;
                height: 3.1rem !important;
            }}
            
            .price-section {{
                margin-bottom: 1.25rem !important;
            }}
            
            .price-label {{
                font-size: 0.8rem !important;
                color: {theme['sub_text']} !important;
            }}
            
            .price-value {{
                font-size: 2rem !important;
                font-weight: 800 !important;
                color: #ffffff !important;
            }}
            
            .cheapest-card .price-value {{
                color: {theme['accent']} !important;
            }}
            
            .action-link {{
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
                padding: 0.75rem 1rem !important;
                background: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                color: #ffffff !important;
                text-decoration: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 0.9rem !important;
                transition: all 0.2s ease !important;
                text-align: center !important;
            }}
            
            .action-link:hover {{
                background: #ffffff !important;
                color: {theme['bg_base']} !important;
                border-color: #ffffff !important;
            }}
            
            .cheapest-card .action-link {{
                background: {theme['button_bg']} !important;
                color: {theme['button_text']} !important;
                border-color: {theme['accent']} !important;
                box-shadow: 0 4px 15px {theme['card_shadow']} !important;
            }}
            
            .cheapest-card .action-link:hover {{
                background: #ffffff !important;
                border-color: #ffffff !important;
                color: {theme['bg_base']} !important;
            }}
            
            .spray-box {{
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                padding: 3rem !important;
                background: {theme['card_bg']} !important;
                border: 1px solid {theme['card_border']} !important;
                border-radius: 24px !important;
                backdrop-filter: blur(10px) !important;
                margin: 2rem 0 !important;
            }}

            .spray-container {{
                position: relative;
                width: 250px;
                height: 180px;
                margin: 1.5rem auto;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .scanner-text {{
                font-size: 1.25rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.1em !important;
                color: {theme['accent']} !important;
                margin-bottom: 0.5rem !important;
                animation: pulse-text 1.5s ease-in-out infinite !important;
                text-transform: uppercase !important;
            }}
            
            .scanning-subtext {{
                color: {theme['sub_text']} !important;
                font-size: 0.9rem !important;
            }}

            /* Cyber Laser Beam for Scanner Box */
            .cyber-laser-scanner {{
                position: absolute;
                inset: 10px;
                border: 1px solid #ff0033;
                box-shadow: inset 0 0 15px rgba(255,0,51,0.4);
                border-radius: 12px;
                animation: pulse-cyber 1.5s ease-in-out infinite;
            }}

            @keyframes pulse-cyber {{
                0%, 100% {{ opacity: 0.3; }}
                50% {{ opacity: 0.9; }}
            }}
            
            div[data-testid="stFormSubmitButton"] button, 
            div[data-testid="stButton"] button {{
                background: {theme['button_bg']} !important;
                color: {theme['button_text']} !important;
                border: 2px solid {theme['accent']} !important;
                border-radius: 8px !important;
                font-weight: 800 !important;
                letter-spacing: 0.05em !important;
                text-transform: uppercase !important;
                padding: 0.6rem 1.5rem !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px {theme['card_shadow']} !important;
            }}
            
            div[data-testid="stFormSubmitButton"] button:hover, 
            div[data-testid="stButton"] button:hover {{
                background-color: #ffffff !important;
                border-color: #ffffff !important;
                color: {theme['bg_base']} !important;
                box-shadow: 0 6px 20px {theme['card_shadow']} !important;
                transform: translateY(-1px) !important;
            }}
            
            div[data-testid="stFormSubmitButton"] button div, 
            div[data-testid="stFormSubmitButton"] button p,
            div[data-testid="stButton"] button div,
            div[data-testid="stButton"] button p {{
                color: {theme['button_text']} !important;
                font-weight: 800 !important;
            }}
        </style>
    """
    ),
    unsafe_allow_html=True
)

# Header Section (Theme Specific Banner & Animation with Floating Flacon on Waves)
st.markdown(get_header_animation_html(st.session_state["active_theme_key"], theme), unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{theme["tagline"]}</div>', unsafe_allow_html=True)

# Main search area in a centered container layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2, st.form("search_form", clear_on_submit=False):
    perfume_query = st.text_input(
        label="Search Perfume",
        placeholder="Type perfume name (e.g. Dior Sauvage, Khamrah, Asad, Creed)...",
        label_visibility="collapsed",
    )
    # Real-time, typo-tolerant autocomplete dropdown (client-side only,
    # debounced) layered on top of the text input above. See
    # search_widget.py for how it stays in sync with the form field.
    render_search_autocomplete(input_label="Search Perfume")
    submit_button = st.form_submit_button(
        "Scan & Compare Prices", use_container_width=True
    )

# Actions on Form Submit
if submit_button or perfume_query:
    if not perfume_query.strip():
        st.warning("Please enter a valid perfume name to scan.")
    else:
        all_retailers_list = list(RETAILERS.keys())

        # Play spray sound immediately when form submits (via parent document audio element)
        st.markdown(
            f'<audio autoplay src="{generate_spray_wav_base64(1.2)}"></audio>',
            unsafe_allow_html=True,
        )

        # Display the custom spray-scanning animation box (Theme Specific)
        scanner_placeholder = st.empty()
        scanner_html = get_scanner_html(
            st.session_state["active_theme_key"],
            theme,
            "Scanning Live Fragrance Deals...",
            "Searching 11 Indian specialty platforms"
        )
        scanner_placeholder.markdown(
            sanitize_html(scanner_html), unsafe_allow_html=True
        )

        time.sleep(0.4)
        scanner_html_2 = get_scanner_html(
            st.session_state["active_theme_key"],
            theme,
            "Filtering Decants & Real Image Matches...",
            "Parsing live prices and CDN product images"
        )
        scanner_placeholder.markdown(
            sanitize_html(scanner_html_2), unsafe_allow_html=True
        )
        scanner_placeholder.markdown(
            sanitize_html(scanner_html_2), unsafe_allow_html=True
        )

        # Execute parallel scraping
        raw_deals = scrape_all_retailers(
            perfume_query, selected_retailers=all_retailers_list
        )
        processed_data = process_and_compare_deals(raw_deals)

        # Clear the scanner animation
        scanner_placeholder.empty()

        sorted_deals = processed_data["sorted_deals"]

        if not sorted_deals:
            # Play a distinct "no match" sound effect so an invalid/typo'd
            # search is unmistakable, separate from the scan-start spray sound.
            no_match_audio = load_audio_base64("audio/faaah.mp3")
            if no_match_audio:
                st.markdown(
                    f'<audio autoplay src="{no_match_audio}"></audio>',
                    unsafe_allow_html=True,
                )
            st.info(
                "🏄‍♂️ Bummer! That perfume wiped out on the beach. "
                "Double-check the spelling, or try a different fragrance name "
                "(e.g. Dior Sauvage, Khamrah, Asad, Creed)."
            )
        else:
            # Unified grid sorted from cheapest to expensive
            st.subheader("⚖️ All Platform Pricing (Sorted from Cheapest to Expensive)")

            deals_html = '<div class="deals-grid">'
            for deal in sorted_deals:
                is_cheapest = deal.get("is_cheapest", False)
                card_class = "deal-card cheapest-card" if is_cheapest else "deal-card"
                badge_html = ""

                # Resolve product image from scraper
                product_img_src = deal.get("image_url", "").strip()
                fallback_svg = get_theme_bottle_svg(st.session_state["active_theme_key"], theme, is_floating=False, size="95px")

                if is_cheapest:
                    badge_html = (
                        '<span class="badge cheapest-badge">🥇 CHEAPEST DEAL</span>'
                    )
                else:
                    badge_html = '<span class="badge real-badge">LIVE</span>'

                image_markup = ""
                if product_img_src:
                    image_markup = f"""
                    <img class="product-image" src="{product_img_src}" referrerpolicy="no-referrer" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                    <div class="product-image-fallback" style="display: none; align-items: center; justify-content: center; width: 100%; height: 100%;">
                        {fallback_svg}
                    </div>
                    """
                else:
                    image_markup = f"""
                    <div class="product-image-fallback" style="display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">
                        {fallback_svg}
                    </div>
                    """

                deals_html += f"""
                <div class="{card_class}">
                    {badge_html}
                    <div>
                        <div class="product-image-container">
                            {image_markup}
                        </div>
                        <div class="retailer-name">{deal['retailer']}</div>
                        <div class="product-title">{deal['product_name']}</div>
                    </div>
                    <div>
                        <div class="price-section">
                            <span class="price-label">Price</span>
                            <div class="price-value">{deal['price_str']}</div>
                        </div>
                        <a href="{deal['link']}" target="_blank" class="action-link">View Deal ↗</a>
                    </div>
                </div>
                """
            deals_html += "</div>"

            st.markdown(sanitize_html(deals_html), unsafe_allow_html=True)
else:
    # Landing page layout with instructions/intro cards and previews
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="color: #8ea8c3; font-size: 1.1rem;">Search for top Arabic, designer, and niche brands to compare deals instantly:</p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; flex-wrap: wrap; color: #00e5ff; font-weight: 600;">
                <span style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.2); padding: 0.5rem 1rem; border-radius: 20px;">🌊 Lattafa Khamrah</span>
                <span style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.2); padding: 0.5rem 1rem; border-radius: 20px;">🏖️ Dior Sauvage</span>
                <span style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.2); padding: 0.5rem 1rem; border-radius: 20px;">☀️ Creed Aventus</span>
                <span style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.2); padding: 0.5rem 1rem; border-radius: 20px;">🌴 Afnan 9 PM</span>
            </div>
        </div>

        <div class="deals-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Smart Search</div>
                    <p style="color: #8ea8c3; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Type any fragrance name. Our search engine will query the store's backend queries to pull down the matching product listings.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚀</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">11 Retailers Compared</div>
                    <p style="color: #8ea8c3; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        We automatically analyze prices from 11 specialty Arabian stores, niche boutiques, and general luxury e-commerce platforms in India.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">💡</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Real CDN Product Images</div>
                    <p style="color: #8ea8c3; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Live e-commerce scrapers pull the actual product listing image directly from the retailer's CDN, showing the true perfume bottle.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

