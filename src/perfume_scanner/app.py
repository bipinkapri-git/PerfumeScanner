"""Streamlit Web Application for Perfume Scanner."""

import base64
import os
import re
import time
import pandas as pd
import streamlit as st

# Import backend scraper and comparator
from perfume_scanner.comparator import process_and_compare_deals
from perfume_scanner.scraper import scrape_all_retailers

# Page Configuration
st.set_page_config(
    page_title="Perfume Scanner | Compare Perfumes",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_image_base64(image_filename: str) -> str:
    """Reads a local asset image and returns it as a base64 encoded data URI."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "assets", image_filename)
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            encoded_str = base64.b64encode(img_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded_str}"
    return ""


def get_perfume_image(query: str) -> str:
    """Matches search query to available perfume assets, returning base64 URI."""
    q_lower = query.lower().strip()
    if "sauvage" in q_lower:
        return get_image_base64("sauvage.png")
    elif "bleu" in q_lower or "chanel" in q_lower:
        return get_image_base64("bleu_de_chanel.png")
    elif "aventus" in q_lower or "creed" in q_lower:
        return get_image_base64("aventus.png")
    elif "libre" in q_lower:
        return get_image_base64("libre.png")
    else:
        return get_image_base64("generic_perfume.png")


def sanitize_html(html_str: str) -> str:
    """Removes newlines and redundant spaces from HTML to prevent Markdown parser bugs."""
    html_str = html_str.replace("\n", " ")
    return re.sub(r"\s+", " ", html_str).strip()


# Custom Premium Styling - Forces Dark Theme & Card Aesthetics
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        /* Force global dark theme to prevent text visibility bugs in light mode */
        [data-testid="stAppViewContainer"] {
            background-color: #0b0c10 !important;
            background-image: radial-gradient(circle at top, #141221 0%, #0b0c10 80%) !important;
            color: #ffffff !important;
        }
        
        [data-testid="stHeader"] {
            background-color: rgba(11, 12, 16, 0.8) !important;
            backdrop-filter: blur(8px);
        }
        
        * {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        .main-header {
            text-align: center;
            padding: 2rem 0 0.5rem 0;
            background: linear-gradient(135deg, #a881af 0%, #6c529a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        
        .sub-header {
            text-align: center;
            font-size: 1.15rem;
            color: #8f92a1;
            margin-bottom: 2.5rem;
            font-weight: 400;
        }
        
        /* Grid container */
        .deals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        /* Glassmorphic card styling */
        .deal-card {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            backdrop-filter: blur(12px) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            min-height: 420px !important;
        }
        
        .deal-card:hover {
            transform: translateY(-5px) !important;
            border-color: rgba(168, 129, 175, 0.45) !important;
            box-shadow: 0 10px 25px rgba(168, 129, 175, 0.15) !important;
            background: rgba(255, 255, 255, 0.04) !important;
        }
        
        /* Cheapest Deal styling */
        .cheapest-card {
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.03) 0%, rgba(46, 213, 115, 0.08) 100%) !important;
            border: 1px solid rgba(46, 213, 115, 0.4) !important;
            box-shadow: 0 8px 32px rgba(46, 213, 115, 0.12) !important;
        }
        
        .cheapest-card:hover {
            border-color: rgba(46, 213, 115, 0.7) !important;
            box-shadow: 0 12px 35px rgba(46, 213, 115, 0.22) !important;
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.05) 0%, rgba(46, 213, 115, 0.12) 100%) !important;
        }
        
        /* Product Image Layout */
        .product-image-container {
            width: 100% !important;
            height: 180px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            background: rgba(0, 0, 0, 0.3) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-bottom: 1.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        .product-image {
            max-width: 100% !important;
            max-height: 100% !important;
            object-fit: contain !important;
            transition: transform 0.5s ease !important;
            padding: 8px !important;
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
            background-color: #2ed573 !important;
            color: #0c0d14 !important;
            box-shadow: 0 2px 10px rgba(46, 213, 115, 0.3) !important;
        }
        
        .simulated-badge {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: #b3b5b8 !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
        }
        
        .real-badge {
            background-color: rgba(168, 129, 175, 0.18) !important;
            color: #c79fd4 !important;
            border: 1px solid rgba(168, 129, 175, 0.25) !important;
        }
        
        /* Card Content */
        .retailer-name {
            font-size: 0.85rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            color: #a8aab5 !important;
            font-weight: 700 !important;
            margin-bottom: 0.4rem !important;
        }
        
        .product-title {
            font-size: 1.12rem !important;
            font-weight: 600 !important;
            color: #ffffff !important;
            margin-bottom: 1.25rem !important;
            line-height: 1.4 !important;
            display: -webkit-box !important;
            -webkit-line-clamp: 2 !important;
            -webkit-box-orient: vertical !important;
            overflow: hidden !important;
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
            color: #2ed573 !important;
        }
        
        /* Direct Action Button */
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
            background: #2ed573 !important;
            color: #0c0d14 !important;
            border-color: #2ed573 !important;
            box-shadow: 0 4px 15px rgba(46, 213, 115, 0.25) !important;
        }
        
        .cheapest-card .action-link:hover {
            background: #26b260 !important;
            border-color: #26b260 !important;
            color: #ffffff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown('<div class="main-header">✨ Perfume Scanner</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Find the best deal for your favorite fragrance across 5 popular online retailers</div>',
    unsafe_allow_html=True,
)

# Main search area in a centered container layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.form("search_form", clear_on_submit=False):
        perfume_query = st.text_input(
            label="Search Perfume",
            placeholder="Type perfume name (e.g. Dior Sauvage, Bleu de Chanel, Creed Aventus, YSL Libre)...",
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
        # Resolve the dynamic image asset matching this perfume (used as simulated fallback)
        fallback_img_base64 = get_perfume_image(perfume_query)

        # Beautiful loading spinner
        with st.spinner(f"Scanning retailers for '{perfume_query}'... Please wait."):
            time.sleep(1.2)
            raw_deals = scrape_all_retailers(perfume_query)
            processed_data = process_and_compare_deals(raw_deals)

        sorted_deals = processed_data["sorted_deals"]

        if not sorted_deals:
            st.error("No pricing information could be scraped or generated for that search query.")
        else:
            # Unified grid sorted from cheapest to expensive
            st.subheader("⚖️ All Platform Pricing (Sorted from Cheapest to Expensive)")
            
            deals_html = '<div class="deals-grid">'
            for deal in sorted_deals:
                is_cheapest = deal.get("is_cheapest", False)
                card_class = "deal-card cheapest-card" if is_cheapest else "deal-card"
                badge_html = ""
                
                # Resolve product image: use real scraped image_url if present, else fallback to high-quality base64 asset
                scraped_img = deal.get("image_url", "")
                if scraped_img and not deal.get("is_simulated"):
                    product_img_src = scraped_img
                else:
                    product_img_src = fallback_img_base64

                if is_cheapest:
                    badge_html = '<span class="badge cheapest-badge">🥇 CHEAPEST DEAL</span>'
                elif deal.get("is_simulated"):
                    badge_html = '<span class="badge simulated-badge">MOCK</span>'
                else:
                    badge_html = '<span class="badge real-badge">LIVE</span>'

                deals_html += f"""
                <div class="{card_class}">
                    {badge_html}
                    <div>
                        <div class="product-image-container">
                            <img class="product-image" src="{product_img_src}" />
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
            
            # Collapse whitespace to prevent the markdown parser from printing raw HTML strings on screen
            st.markdown(sanitize_html(deals_html), unsafe_allow_html=True)

            # Graphical Comparison
            st.subheader("📊 Price Comparison Chart")
            
            chart_data = []
            for deal in sorted_deals:
                if deal["price_val"] != float("inf"):
                    chart_data.append({
                        "Retailer": deal["retailer"],
                        "Price ($)": deal["price_val"],
                    })
                    
            if chart_data:
                df = pd.DataFrame(chart_data)
                df = df.set_index("Retailer")
                st.bar_chart(df)
            else:
                st.info("No numerical prices available to display chart comparison.")
else:
    # Landing page layout with instructions/intro cards and preview images
    sauvage_preview = get_image_base64("sauvage.png")
    bleu_preview = get_image_base64("bleu_de_chanel.png")
    libre_preview = get_image_base64("libre.png")

    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="color: #8f92a1; font-size: 1.1rem;">Search for top brands to compare deals instantly:</p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <img src="{sauvage_preview}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,0.1); margin-bottom: 0.5rem;" />
                    <div style="font-size: 0.85rem; font-weight: 600; color: #ffffff;">Sauvage</div>
                </div>
                <div style="text-align: center;">
                    <img src="{bleu_preview}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,0.1); margin-bottom: 0.5rem;" />
                    <div style="font-size: 0.85rem; font-weight: 600; color: #ffffff;">Bleu de Chanel</div>
                </div>
                <div style="text-align: center;">
                    <img src="{libre_preview}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(255,255,255,0.1); margin-bottom: 0.5rem;" />
                    <div style="font-size: 0.85rem; font-weight: 600; color: #ffffff;">Libre</div>
                </div>
            </div>
        </div>

        <div class="deals-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Smart Search</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Type any fragrance name. Our search engine will query the store's backend queries to pull down the matching product listings.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚀</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">5 Retailers Compared</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        We analyze prices from FragranceNet, FragranceX, Perfume.com, Jomashop, and MaxAroma in one unified comparison panel.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">💡</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Deterministic Fallbacks</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Includes smart simulation mechanics ensuring you always get comparative data even if store servers block requests due to rate limits.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
