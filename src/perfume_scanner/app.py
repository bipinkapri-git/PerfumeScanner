"""Streamlit Web Application for Perfume Scanner."""

import re
import time
import streamlit as st

# Import backend scraper and comparator
from perfume_scanner.comparator import process_and_compare_deals
from perfume_scanner.scraper import RETAILERS, scrape_all_retailers

# Page Configuration
st.set_page_config(
    page_title="Indian Perfume Scanner | Compare Fragrance Deals",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def sanitize_html(html_str: str) -> str:
    """Removes newlines and redundant spaces from HTML to prevent Markdown parser bugs."""
    html_str = html_str.replace("\n", " ")
    return re.sub(r"\s+", " ", html_str).strip()


def generate_spray_wav_base64(duration_seconds=1.2, sample_rate=22050) -> str:
    """Generates a 16-bit high-passed white noise wave file in bytes and encodes it as Base64."""
    import math
    import random
    import struct
    import base64

    num_samples = int(sample_rate * duration_seconds)
    samples = []
    
    # Simple high-pass white noise difference filter: y[n] = x[n] - x[n-1]
    prev_x = 0.0
    for i in range(num_samples):
        t = i / sample_rate
        # Quick spray attack (0.08s) followed by exponential decay
        if t < 0.08:
            envelope = t / 0.08
        else:
            envelope = math.exp(-3.5 * (t - 0.08))
            
        x = random.uniform(-1.0, 1.0)
        y = x - prev_x
        prev_x = x
        
        # Scale volume and clamp PCM limit
        val = max(-1.0, min(1.0, y * envelope * 0.12))
        samples.append(int(val * 32767))
        
    subchunk2_size = num_samples * 2
    chunk_size = 36 + subchunk2_size
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', chunk_size, b'WAVE',
        b'fmt ', 16, 1, 1, sample_rate,
        sample_rate * 2, 2, 16,
        b'data', subchunk2_size
    )
    
    wav_bytes = header + struct.pack(f'<{len(samples)}h', *samples)
    return "data:audio/wav;base64," + base64.b64encode(wav_bytes).decode('utf-8')


# Custom Premium Red & Black Styling
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        /* Force global dark red-black theme */
        [data-testid="stAppViewContainer"] {
            background-color: #030304 !important;
            background-image: radial-gradient(circle at top, #260508 0%, #030304 85%) !important;
            color: #ffffff !important;
        }
        
        [data-testid="stHeader"] {
            background-color: rgba(3, 3, 4, 0.8) !important;
            backdrop-filter: blur(8px);
        }
        
        * {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        .main-header {
            text-align: center;
            padding: 1rem 0 0.25rem 0;
            background: linear-gradient(135deg, #ff1a40 0%, #99001a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        
        .sub-header {
            text-align: center;
            font-size: 1.1rem;
            color: #b0b3c2;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Floating vector logo */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .floating-bottle {
            width: 90px;
            height: 90px;
            animation: float 4s ease-in-out infinite;
        }
        
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
            100% { transform: translateY(0px); }
        }
        
        /* Grid container */
        .deals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        /* Glassmorphic card styling - Black & Red theme */
        .deal-card {
            background: rgba(255, 255, 255, 0.015) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            backdrop-filter: blur(12px) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            min-height: 440px !important;
        }
        
        .deal-card:hover {
            transform: translateY(-5px) !important;
            border-color: rgba(255, 26, 64, 0.4) !important;
            box-shadow: 0 10px 25px rgba(255, 26, 64, 0.15) !important;
            background: rgba(255, 255, 255, 0.035) !important;
        }
        
        /* Cheapest Deal styling - Gold & Crimson */
        .cheapest-card {
            background: linear-gradient(135deg, rgba(255, 26, 64, 0.03) 0%, rgba(255, 26, 64, 0.09) 100%) !important;
            border: 1px solid rgba(255, 26, 64, 0.45) !important;
            box-shadow: 0 8px 32px rgba(255, 26, 64, 0.15) !important;
        }
        
        .cheapest-card:hover {
            border-color: rgba(255, 26, 64, 0.75) !important;
            box-shadow: 0 12px 35px rgba(255, 26, 64, 0.25) !important;
            background: linear-gradient(135deg, rgba(255, 26, 64, 0.05) 0%, rgba(255, 26, 64, 0.14) 100%) !important;
        }
        
        /* Product Image Layout */
        .product-image-container {
            width: 100% !important;
            height: 190px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            background: #ffffff !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-bottom: 1.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        }
        
        .product-image {
            max-width: 90% !important;
            max-height: 90% !important;
            object-fit: contain !important;
            transition: transform 0.5s ease !important;
            padding: 4px !important;
        }
        
        .deal-card:hover .product-image {
            transform: scale(1.06) !important;
        }
        
        /* Badges */
        .badge {
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
        }
        
        .cheapest-badge {
            background-color: #ff1a40 !important;
            color: #ffffff !important;
            box-shadow: 0 2px 10px rgba(255, 26, 64, 0.4) !important;
        }
        
        .real-badge {
            background-color: rgba(255, 26, 64, 0.15) !important;
            color: #ff6b81 !important;
            border: 1px solid rgba(255, 26, 64, 0.25) !important;
        }
        
        /* Card Content */
        .retailer-name {
            font-size: 0.85rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            color: #b0b3c2 !important;
            font-weight: 700 !important;
            margin-bottom: 0.4rem !important;
        }
        
        .product-title {
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
        }
        
        .price-section {
            margin-bottom: 1.25rem !important;
        }
        
        .price-label {
            font-size: 0.8rem !important;
            color: #8f92a1 !important;
        }
        
        .price-value {
            font-size: 2rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
        }
        
        .cheapest-card .price-value {
            color: #ff1a40 !important;
        }
        
        .action-link {
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
        }
        
        .action-link:hover {
            background: #ffffff !important;
            color: #0c0d14 !important;
            border-color: #ffffff !important;
        }
        
        .cheapest-card .action-link {
            background: #ff1a40 !important;
            color: #ffffff !important;
            border-color: #ff1a40 !important;
            box-shadow: 0 4px 15px rgba(255, 26, 64, 0.3) !important;
        }
        
        .cheapest-card .action-link:hover {
            background: #cc0024 !important;
            border-color: #cc0024 !important;
            color: #ffffff !important;
        }
 
        /* Premium Spray Atomizer Animations */
        .spray-box {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 3rem !important;
            background: rgba(255, 255, 255, 0.01) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 24px !important;
            backdrop-filter: blur(10px) !important;
            margin: 2rem 0 !important;
        }

        .spray-container {
            position: relative;
            width: 250px;
            height: 180px;
            margin: 1.5rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .spray-bottle {
            width: 90px;
            height: 90px;
            position: relative;
            animation: spray-press 1.2s ease-in-out infinite;
        }

        @keyframes spray-press {
            0%, 100% { transform: scaleY(1); }
            50% { transform: scaleY(0.92) translateY(4px); }
        }

        .mist-cloud {
            position: absolute;
            top: 32px;
            left: 170px;
            width: 120px;
            height: 60px;
        }

        .mist-particle {
            position: absolute;
            background: radial-gradient(circle, rgba(255, 26, 64, 0.6) 0%, rgba(255, 255, 255, 0) 70%);
            border-radius: 50%;
            opacity: 0;
        }

        .p1 { width: 15px; height: 15px; top: 20px; left: 0px; animation: spray-mist-1 1.2s ease-out infinite; }
        .p2 { width: 25px; height: 25px; top: 15px; left: 10px; animation: spray-mist-2 1.2s ease-out infinite; animation-delay: 0.1s; }
        .p3 { width: 35px; height: 35px; top: 10px; left: 20px; animation: spray-mist-3 1.2s ease-out infinite; animation-delay: 0.2s; }
        .p4 { width: 45px; height: 45px; top: 5px; left: 30px; animation: spray-mist-4 1.2s ease-out infinite; animation-delay: 0.3s; }
        .p5 { width: 20px; height: 20px; top: 25px; left: 15px; animation: spray-mist-2 1.2s ease-out infinite; animation-delay: 0.15s; }
        .p6 { width: 30px; height: 30px; top: 5px; left: 25px; animation: spray-mist-3 1.2s ease-out infinite; animation-delay: 0.25s; }

        @keyframes spray-mist-1 {
            0% { transform: scale(0.2) translate(-30px, 0); opacity: 0; }
            20% { opacity: 0.8; }
            100% { transform: scale(1.5) translate(40px, -10px); opacity: 0; }
        }

        @keyframes spray-mist-2 {
            0% { transform: scale(0.2) translate(-30px, 0); opacity: 0; }
            20% { opacity: 0.7; }
            100% { transform: scale(1.8) translate(60px, 0px); opacity: 0; }
        }

        @keyframes spray-mist-3 {
            0% { transform: scale(0.2) translate(-30px, 0); opacity: 0; }
            20% { opacity: 0.6; }
            100% { transform: scale(2.2) translate(80px, 10px); opacity: 0; }
        }

        @keyframes spray-mist-4 {
            0% { transform: scale(0.2) translate(-30px, 0); opacity: 0; }
            20% { opacity: 0.4; }
            100% { transform: scale(2.8) translate(100px, -5px); opacity: 0; }
        }
 
        .scanner-text {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.1em !important;
            color: #ff1a40 !important;
            margin-bottom: 0.5rem !important;
            animation: pulse-text 1.5s ease-in-out infinite !important;
            text-transform: uppercase !important;
        }
 
        @keyframes pulse-text {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
 
        .scanning-subtext {
            color: #b0b3c2 !important;
            font-size: 0.9rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Floating Vector Logo
st.markdown(
    """
    <div class="logo-container">
        <svg viewBox="0 0 100 100" class="floating-bottle">
            <!-- Perfume bottle cap -->
            <rect x="42" y="10" width="16" height="15" rx="3" fill="none" stroke="#ff1a40" stroke-width="3" />
            <!-- Bottle neck -->
            <rect x="46" y="25" width="8" height="5" fill="#ff1a40" />
            <!-- Main body of bottle -->
            <path d="M25,30 h50 a8,8 0 0 1 8,8 v45 a8,8 0 0 1 -8,8 h-50 a8,8 0 0 1 -8,-8 v-45 a8,8 0 0 1 8,-8 Z" fill="none" stroke="url(#gradient)" stroke-width="4" />
            <!-- Label -->
            <rect x="35" y="45" width="30" height="20" rx="2" fill="none" stroke="#99001a" stroke-width="2" />
            <!-- Sprayer dip tube -->
            <line x1="50" y1="30" x2="50" y2="75" stroke="#99001a" stroke-width="1.5" stroke-dasharray="3,3" />
            <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#ff1a40" />
                    <stop offset="100%" stop-color="#99001a" />
                </linearGradient>
            </defs>
        </svg>
    </div>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown('<div class="main-header">Perfume Scanner</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Compare live fragrance deals and real images across 14 leading Indian retailers</div>',
    unsafe_allow_html=True,
)

# Main search area in a centered container layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.form("search_form", clear_on_submit=False):
        perfume_query = st.text_input(
            label="Search Perfume",
            placeholder="Type perfume name (e.g. Dior Sauvage, Khamrah, Asad, Creed)...",
            label_visibility="collapsed",
        )
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
        st.markdown(f'<audio autoplay src="{generate_spray_wav_base64(1.2)}"></audio>', unsafe_allow_html=True)
        
        # Display the custom spray-scanning animation box
        scanner_placeholder = st.empty()
        scanner_html = """
        <div class="spray-box">
            <div class="spray-container">
                <svg class="spray-bottle" viewBox="0 0 100 100">
                    <rect x="42" y="10" width="16" height="15" rx="3" fill="none" stroke="#ff1a40" stroke-width="3" />
                    <rect x="46" y="25" width="8" height="5" fill="#ff1a40" />
                    <path d="M25,30 h50 a8,8 0 0 1 8,8 v45 a8,8 0 0 1 -8,8 h-50 a8,8 0 0 1 -8,-8 v-45 a8,8 0 0 1 8,-8 Z" fill="none" stroke="url(#red-gradient)" stroke-width="4" />
                    <rect x="35" y="45" width="30" height="20" rx="2" fill="none" stroke="#99001a" stroke-width="2" />
                    <line x1="50" y1="30" x2="50" y2="75" stroke="#99001a" stroke-width="1.5" stroke-dasharray="3,3" />
                    <defs>
                        <linearGradient id="red-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#ff1a40" />
                            <stop offset="100%" stop-color="#99001a" />
                        </linearGradient>
                    </defs>
                </svg>
                <div class="mist-cloud">
                    <div class="mist-particle p1"></div>
                    <div class="mist-particle p2"></div>
                    <div class="mist-particle p3"></div>
                    <div class="mist-particle p4"></div>
                    <div class="mist-particle p5"></div>
                    <div class="mist-particle p6"></div>
                </div>
            </div>
            <div class="scanner-text">Atomizing Fragrance Search...</div>
            <div class="scanning-subtext">Searching 14 Indian specialty platforms</div>
        </div>
        """
        scanner_placeholder.markdown(sanitize_html(scanner_html), unsafe_allow_html=True)
        
        time.sleep(0.4)
        scanner_html_2 = """
        <div class="spray-box">
            <div class="spray-container">
                <svg class="spray-bottle" viewBox="0 0 100 100">
                    <rect x="42" y="10" width="16" height="15" rx="3" fill="none" stroke="#ff1a40" stroke-width="3" />
                    <rect x="46" y="25" width="8" height="5" fill="#ff1a40" />
                    <path d="M25,30 h50 a8,8 0 0 1 8,8 v45 a8,8 0 0 1 -8,8 h-50 a8,8 0 0 1 -8,-8 v-45 a8,8 0 0 1 8,-8 Z" fill="none" stroke="url(#red-gradient)" stroke-width="4" />
                    <rect x="35" y="45" width="30" height="20" rx="2" fill="none" stroke="#99001a" stroke-width="2" />
                    <line x1="50" y1="30" x2="50" y2="75" stroke="#99001a" stroke-width="1.5" stroke-dasharray="3,3" />
                    <defs>
                        <linearGradient id="red-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#ff1a40" />
                            <stop offset="100%" stop-color="#99001a" />
                        </linearGradient>
                    </defs>
                </svg>
                <div class="mist-cloud">
                    <div class="mist-particle p1"></div>
                    <div class="mist-particle p2"></div>
                    <div class="mist-particle p3"></div>
                    <div class="mist-particle p4"></div>
                    <div class="mist-particle p5"></div>
                    <div class="mist-particle p6"></div>
                </div>
            </div>
            <div class="scanner-text">Filtering Decants & Matches...</div>
            <div class="scanning-subtext">Parsing live prices and CDN product images</div>
        </div>
        """
        scanner_placeholder.markdown(sanitize_html(scanner_html_2), unsafe_allow_html=True)

        # Execute parallel scraping
        raw_deals = scrape_all_retailers(perfume_query, selected_retailers=all_retailers_list)
        processed_data = process_and_compare_deals(raw_deals)
        
        # Clear the scanner animation
        scanner_placeholder.empty()

        sorted_deals = processed_data["sorted_deals"]

        if not sorted_deals:
            st.info("No matching products found across the 14 Indian retailers. Make sure the name is typed correctly!")
        else:
            # Unified grid sorted from cheapest to expensive
            st.subheader("⚖️ All Platform Pricing (Sorted from Cheapest to Expensive)")
            
            deals_html = '<div class="deals-grid">'
            for deal in sorted_deals:
                is_cheapest = deal.get("is_cheapest", False)
                card_class = "deal-card cheapest-card" if is_cheapest else "deal-card"
                badge_html = ""
                
                # Resolve product image from scraper
                product_img_src = deal.get("image_url", "")
                
                if is_cheapest:
                    badge_html = '<span class="badge cheapest-badge">🥇 CHEAPEST DEAL</span>'
                else:
                    badge_html = '<span class="badge real-badge">LIVE</span>'

                deals_html += f"""
                <div class="{card_class}">
                    {badge_html}
                    <div>
                        <div class="product-image-container">
                            <img class="product-image" src="{product_img_src or ''}" />
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
            <p style="color: #b0b3c2; font-size: 1.1rem;">Search for top Arabic, designer, and niche brands to compare deals instantly:</p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; flex-wrap: wrap; color: #ff1a40; font-weight: 600;">
                <span style="background: rgba(255,255,255,0.03); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Lattafa Khamrah</span>
                <span style="background: rgba(255,255,255,0.03); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Dior Sauvage</span>
                <span style="background: rgba(255,255,255,0.03); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Creed Aventus</span>
                <span style="background: rgba(255,255,255,0.03); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Afnan 9 PM</span>
            </div>
        </div>

        <div class="deals-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Smart Search</div>
                    <p style="color: #b0b3c2; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Type any fragrance name. Our search engine will query the store's backend queries to pull down the matching product listings.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚀</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">14 Retailers Compared</div>
                    <p style="color: #b0b3c2; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        We automatically analyze prices from 14 specialty Arabian stores, niche boutiques, and general luxury e-commerce platforms in India.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">💡</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Real CDN Product Images</div>
                    <p style="color: #b0b3c2; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Live e-commerce scrapers pull the actual product listing image directly from the retailer's CDN, showing the true perfume bottle.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
