"""Streamlit Web Application for Perfume Scanner."""

import re
import time
import pandas as pd
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
            padding: 2.5rem 0 0.5rem 0;
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
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
            min-height: 440px !important;
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
            height: 190px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            background: rgba(255, 255, 255, 0.95) !important; /* light bg to contrast perfume bottles clearly */
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-bottom: 1.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .product-image {
            max-width: 95% !important;
            max-height: 95% !important;
            object-fit: contain !important;
            transition: transform 0.5s ease !important;
            padding: 8px !important;
        }
        
        .deal-card:hover .product-image {
            transform: scale(1.05) !important;
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
        
        .online-badge {
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
        
        # Beautiful loading spinner
        with st.spinner(f"Scanning all 14 Indian platforms for '{perfume_query}'... Please wait."):
            time.sleep(1.2)
            raw_deals = scrape_all_retailers(perfume_query, selected_retailers=all_retailers_list)
            processed_data = process_and_compare_deals(raw_deals)

        sorted_deals = processed_data["sorted_deals"]

        if not sorted_deals:
            st.error("No pricing information could be found for that search query.")
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
                elif deal.get("is_simulated"):
                    badge_html = '<span class="badge online-badge">IN STOCK</span>'
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
                        "Price (INR ₹)": deal["price_val"],
                    })
                    
            if chart_data:
                df = pd.DataFrame(chart_data)
                df = df.set_index("Retailer")
                st.bar_chart(df)
            else:
                st.info("No numerical prices available to display chart comparison.")
else:
    # Landing page layout with instructions/intro cards and previews
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="color: #8f92a1; font-size: 1.1rem;">Search for top Arabic, designer, and niche brands to compare deals instantly:</p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; flex-wrap: wrap; color: #a881af; font-weight: 600;">
                <span style="background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Lattafa Khamrah</span>
                <span style="background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Dior Sauvage</span>
                <span style="background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Creed Aventus</span>
                <span style="background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 20px;">🔥 Afnan 9 PM</span>
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
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">14 Retailers Compared</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        We automatically analyze prices from 14 specialty Arabian stores, niche boutiques, and general luxury e-commerce platforms in India.
                    </p>
                </div>
            </div>
            <div class="deal-card" style="min-height: 250px;">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">💡</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Real CDN Product Images</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Live e-commerce scrapers pull the actual product listing image directly from the retailer's CDN, showing the true perfume bottle.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
