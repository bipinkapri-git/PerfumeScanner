"""Streamlit Web Application for Perfume Scanner."""

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

# Custom Premium Styling
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        /* Base styles */
        * {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        .main-header {
            text-align: center;
            padding: 2rem 0 1rem 0;
            background: linear-gradient(135deg, #a881af 0%, #6c529a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
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
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        /* Glassmorphic card styling */
        .deal-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 250px;
        }
        
        .deal-card:hover {
            transform: translateY(-5px);
            border-color: rgba(168, 129, 175, 0.4);
            box-shadow: 0 10px 25px rgba(168, 129, 175, 0.1);
            background: rgba(255, 255, 255, 0.04);
        }
        
        /* Cheapest Deal styling */
        .cheapest-card {
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.03) 0%, rgba(46, 213, 115, 0.08) 100%);
            border: 1px solid rgba(46, 213, 115, 0.35);
            box-shadow: 0 8px 32px rgba(46, 213, 115, 0.1);
        }
        
        .cheapest-card:hover {
            border-color: rgba(46, 213, 115, 0.6);
            box-shadow: 0 12px 35px rgba(46, 213, 115, 0.2);
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.05) 0%, rgba(46, 213, 115, 0.12) 100%);
        }
        
        /* Badges */
        .badge {
            position: absolute;
            top: 1rem;
            right: 1rem;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.65rem;
            border-radius: 20px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        
        .cheapest-badge {
            background-color: #2ed573;
            color: #0c0d14;
            box-shadow: 0 2px 10px rgba(46, 213, 115, 0.3);
        }
        
        .simulated-badge {
            background-color: rgba(255, 255, 255, 0.1);
            color: #cfd2d6;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        
        .real-badge {
            background-color: rgba(168, 129, 175, 0.2);
            color: #a881af;
            border: 1px solid rgba(168, 129, 175, 0.3);
        }
        
        /* Card Content */
        .retailer-name {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #8f92a1;
            font-weight: 700;
            margin-bottom: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .product-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 1.5rem;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3.2rem;
        }
        
        .price-section {
            margin-bottom: 1.5rem;
        }
        
        .price-label {
            font-size: 0.8rem;
            color: #8f92a1;
        }
        
        .price-value {
            font-size: 2rem;
            font-weight: 800;
            color: #ffffff;
        }
        
        .cheapest-card .price-value {
            color: #2ed573;
        }
        
        /* Direct Action Button */
        .action-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 0.75rem 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            text-align: center;
        }
        
        .action-link:hover {
            background: #ffffff;
            color: #0c0d14;
            border-color: #ffffff;
        }
        
        .cheapest-card .action-link {
            background: #2ed573;
            color: #0c0d14;
            border-color: #2ed573;
            box-shadow: 0 4px 15px rgba(46, 213, 115, 0.25);
        }
        
        .cheapest-card .action-link:hover {
            background: #26b260;
            border-color: #26b260;
            color: #ffffff;
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
    # Use standard Streamlit form to prevent query trigger on every letter typed
    with st.form("search_form", clear_on_submit=False):
        perfume_query = st.text_input(
            label="Search Perfume",
            placeholder="Type perfume name (e.g. Dior Sauvage, Creed Aventus, YSL Libre)...",
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
        # Beautiful loading spinner
        with st.spinner(f"Scanning retailers for '{perfume_query}'... Please wait."):
            # Sleep slightly to make scanning feel highly robust and realistic
            time.sleep(1.2)
            raw_deals = scrape_all_retailers(perfume_query)
            processed_data = process_and_compare_deals(raw_deals)

        sorted_deals = processed_data["sorted_deals"]
        cheapest_deal = processed_data["cheapest_deal"]

        if not sorted_deals:
            st.error("No pricing information could be scraped or generated for that search query.")
        else:
            # Highlight Cheapest Option
            if cheapest_deal:
                st.subheader("🔥 Best Deal Found")
                
                # Render absolute cheapest as a big banner card
                badge_type = (
                    "simulated" if cheapest_deal.get("is_simulated") else "real"
                )
                badge_label = "MOCK DEAL" if badge_type == "simulated" else "LIVE"
                
                st.markdown(
                    f"""
                    <div class="deal-card cheapest-card" style="min-height: auto; padding: 2rem; margin-bottom: 2rem;">
                        <span class="badge cheapest-badge">🥇 Cheapest Deal</span>
                        <div class="retailer-name">{cheapest_deal['retailer']} ({badge_label})</div>
                        <div class="product-title" style="font-size: 1.5rem; height: auto; display: block; margin-bottom: 1rem;">
                            {cheapest_deal['product_name']}
                        </div>
                        <div class="price-section" style="display: flex; align-items: baseline; gap: 1rem; margin-bottom: 1.5rem;">
                            <div class="price-value" style="font-size: 3rem;">{cheapest_deal['price_str']}</div>
                            <div class="price-label">cheapest absolute price</div>
                        </div>
                        <a href="{cheapest_deal['link']}" target="_blank" class="action-link" style="max-width: 300px;">
                            Grab This Deal ↗
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Compare All Retailers
            st.subheader("⚖️ All Scraped Deals")
            
            deals_html = '<div class="deals-grid">'
            for deal in sorted_deals:
                is_cheapest = deal.get("is_cheapest", False)
                card_class = "deal-card cheapest-card" if is_cheapest else "deal-card"
                badge_html = ""
                
                if is_cheapest:
                    badge_html = '<span class="badge cheapest-badge">🥇 CHEAPEST</span>'
                elif deal.get("is_simulated"):
                    badge_html = '<span class="badge simulated-badge">MOCK</span>'
                else:
                    badge_html = '<span class="badge real-badge">LIVE</span>'

                deals_html += f"""
                <div class="{card_class}">
                    {badge_html}
                    <div>
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
            st.markdown(deals_html, unsafe_allow_html=True)

            # Graphical Comparison
            st.subheader("📊 Price Comparison Chart")
            
            # Prepare data frame for charting
            chart_data = []
            for deal in sorted_deals:
                # Filter out failures with inf price values
                if deal["price_val"] != float("inf"):
                    chart_data.append({
                        "Retailer": deal["retailer"],
                        "Price ($)": deal["price_val"],
                    })
                    
            if chart_data:
                df = pd.DataFrame(chart_data)
                # Set index to Retailer so it labels the bar chart nicely
                df = df.set_index("Retailer")
                
                st.bar_chart(df)
            else:
                st.info("No numerical prices available to display chart comparison.")
else:
    # Landing page layout with instructions/intro cards
    st.markdown(
        """
        <div class="deals-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
            <div class="deal-card">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔍</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">Smart Search</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Type any fragrance name. Our search engine will query the store's backend queries to pull down the matching product listings.
                    </p>
                </div>
            </div>
            <div class="deal-card">
                <div>
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🚀</div>
                    <div class="product-title" style="height: auto; font-size: 1.25rem;">5 Retailers Compared</div>
                    <p style="color: #8f92a1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        We analyze prices from FragranceNet, FragranceX, Perfume.com, Jomashop, and MaxAroma in one unified comparison panel.
                    </p>
                </div>
            </div>
            <div class="deal-card">
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
