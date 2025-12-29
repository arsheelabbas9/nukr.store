"""
NUKR.STORE - MAIN APPLICATION ENTRY POINT
=========================================
Author: Batman
Version: 2.0 (The "Beautiful" Update)
Description:
    This file acts as the primary GUI controller. It injects a highly 
    customized CSS design system to override Streamlit's default look 
    and feel, transforming it into a modern, high-end marketplace.
"""

import streamlit as st
import time
import phase1  # Config & Data Engine
import phase2  # Seller Dashboard Logic
import phase3  # Buyer Feed Logic
import phase4  # Checkout Logic

# ==============================================================================
# 1. SYSTEM CONFIGURATION
# ==============================================================================

# Must be the very first command
phase1.init_app()
data = phase1.load_data()

# ==============================================================================
# 2. THE DESIGN ENGINE (CSS & ASSETS)
# ==============================================================================

def inject_custom_css():
    """
    Injects ~200 lines of high-performance CSS to completely transform 
    the application's visual hierarchy.
    """
    st.markdown("""
        <style>
        /* --- IMPORT PREMIUM FONTS --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@600;700&display=swap');

        /* --- ROOT VARIABLES (The Color Palette) --- */
        :root {
            --primary-black: #111827;
            --secondary-gray: #4B5563;
            --bg-white: #ffffff;
            --bg-off-white: #F9FAFB;
            --accent-gold: #D4AF37;
            --success-green: #10B981;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --radius-md: 12px;
            --radius-lg: 20px;
        }

        /* --- GLOBAL RESET & TYPOGRAPHY --- */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-white);
            color: var(--primary-black);
            font-size: 16px;
        }

        h1, h2, h3, h4 {
            font-family: 'Playfair Display', serif; /* Editorial feel for headings */
            color: var(--primary-black);
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        /* --- HIDE DEFAULT STREAMLIT ELEMENTS --- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;} /* Hides the top colored bar */

        /* --- SIDEBAR STYLING --- */
        section[data-testid="stSidebar"] {
            background-color: var(--bg-off-white);
            border-right: 1px solid #E5E7EB;
            padding-top: 2rem;
        }

        /* --- COMPONENT: BUTTONS (The "Pill" Look) --- */
        div.stButton > button {
            background-color: var(--primary-black);
            color: white;
            border: 1px solid transparent;
            border-radius: 50px;
            padding: 0.6rem 1.5rem;
            font-weight: 500;
            font-size: 0.95rem;
            letter-spacing: 0.02em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-md);
            width: 100%;
        }

        div.stButton > button:hover {
            background-color: white;
            color: var(--primary-black);
            border: 1px solid var(--primary-black);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        div.stButton > button:active {
            transform: translateY(0);
        }

        /* --- COMPONENT: INPUT FIELDS (Soft & Clean) --- */
        input[type="text"], textarea, input[type="number"] {
            background-color: var(--bg-white) !important;
            border: 1px solid #E5E7EB !important;
            border-radius: var(--radius-md) !important;
            padding: 10px 12px !important;
            color: var(--primary-black) !important;
            transition: border 0.2s ease;
        }

        input:focus {
            border-color: var(--primary-black) !important;
            box-shadow: 0 0 0 2px rgba(0,0,0,0.05) !important;
        }

        /* --- COMPONENT: IMAGES & CARDS --- */
        img {
            border-radius: var(--radius-md);
            transition: transform 0.3s ease;
        }
        
        /* Container for product cards */
        div[data-testid="stVerticalBlock"] > div {
            border-radius: var(--radius-md);
        }

        /* --- UTILITY CLASSES --- */
        .big-font { font-size: 3rem !important; font-weight: 800; line-height: 1.1; }
        .sub-font { font-size: 1.2rem !important; color: var(--secondary-gray); }
        .highlight { color: var(--accent-gold); }
        
        /* --- ANIMATIONS --- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-enter {
            animation: fadeIn 0.5s ease-out forwards;
        }
        
        /* --- RADIO BUTTONS AS CARDS --- */
        div[role="radiogroup"] {
            background: transparent;
        }
        
        </style>
    """, unsafe_allow_html=True)

# Inject the Design System
inject_custom_css()


# ==============================================================================
# 3. UI HELPER COMPONENTS
# ==============================================================================

def render_hero_section():
    """
    Displays a massive, beautiful 'Hero' banner on the home page.
    """
    st.markdown("""
        <div class="animate-enter" style="text-align: center; padding: 4rem 0 2rem 0;">
            <h1 class="big-font">
                Discover Local <br>
                <span class="highlight">Treasures</span>.
            </h1>
            <p class="sub-font" style="max-width: 600px; margin: 1rem auto;">
                Nukr connects you with the finest home-based artisans and resellers 
                in your neighborhood. Hand-picked, verified, and delivered with love.
            </p>
        </div>
        <hr style="margin: 3rem 0; border: 0; border-top: 1px solid #E5E7EB;">
    """, unsafe_allow_html=True)

def render_sidebar_header():
    """
    Renders the brand logo area in the sidebar.
    """
    with st.sidebar:
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <h2 style="font-size: 1.8rem; margin:0;">Nukr<span style="color:#D4AF37">.</span></h2>
                <p style="font-size: 0.8rem; color: #6B7280; margin:0;">The Local Marketplace</p>
            </div>
        """, unsafe_allow_html=True)

def render_footer():
    """
    Renders a professional footer.
    """
    st.markdown("""
        <div style="margin-top: 5rem; padding-top: 2rem; border-top: 1px solid #E5E7EB; text-align: center;">
            <p style="color: #9CA3AF; font-size: 0.9rem;">
                © 2025 Nukr.store Inc. • Built for Karachi • 
                <a href="#" style="color: #4B5563; text-decoration: none;">Terms</a> • 
                <a href="#" style="color: #4B5563; text-decoration: none;">Privacy</a>
            </p>
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 4. MAIN APPLICATION LOGIC
# ==============================================================================

def main():
    """
    The central controller logic. Switches between phases based on user interaction.
    """
    
    # --- 4.1 CHECK FOR CHECKOUT STATE ---
    # If a user clicked "Buy" on any previous screen, we hijack the flow 
    # to show the Checkout screen immediately (Phase 4).
    if st.session_state.get("selected_product"):
        # We wrap it in a container to give it margins
        with st.container():
            phase4.render_checkout(data, phase1.save_data)
        
        # Add footer even on checkout
        render_footer()
        return  # Stop executing the rest of the script

    # --- 4.2 NAVIGATION SETUP ---
    render_sidebar_header()
    
    # Custom Sidebar Menu
    with st.sidebar:
        # We use a radio button but style it to look like a navigation menu
        nav_selection = st.radio(
            "Go to:",
            ["✨ Explore Market", "🏪 Seller Dashboard", "👤 My Account"],
            index=0,
            label_visibility="collapsed"
        )
        
        # Contextual Sidebar Widgets
        st.markdown("---")
        if "Explore" in nav_selection:
            st.caption("🔍 **Trending Now**")
            st.markdown("- Crochet Tops")
            st.markdown("- Vintage Watches")
            st.markdown("- Silver Jewelry")
        elif "Seller" in nav_selection:
            st.info("💡 **Seller Tip:** \nHigh-quality photos increase sales by 40%.")

    # --- 4.3 ROUTING ---
    
    # ROUTE A: THE MARKETPLACE (Buyer)
    if "Explore Market" in nav_selection:
        render_hero_section()
        phase3.render_buyer_feed(data)
    
    # ROUTE B: THE DASHBOARD (Seller)
    elif "Seller Dashboard" in nav_selection:
        # Add a little spacing
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        phase2.render_seller_dashboard(data, phase1.save_data)
    
    # ROUTE C: ACCOUNT (Placeholder)
    elif "My Account" in nav_selection:
        st.title("My Account")
        st.markdown("""
            <div style="background-color: #F3F4F6; padding: 2rem; border-radius: 12px; text-align: center;">
                <h3>User Profiles Coming Soon</h3>
                <p>We are building a way for you to track your order history and favorite stores.</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 4.4 FOOTER ---
    render_footer()

# ==============================================================================
# 5. EXECUTION
# ==============================================================================

if __name__ == "__main__":
    # Run the app
    main()