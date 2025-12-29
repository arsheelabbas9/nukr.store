"""
NUKR.STORE - MAIN APPLICATION KERNEL (ENTERPRISE EDITION)
=========================================================
Description:
    The central entry point for the Nukr Marketplace. 
    This file orchestrates the interaction between the Data Layer (Phase 1),
    Vendor Portal (Phase 2), Buyer Interface (Phase 3), and Payment Gateway (Phase 4).

    Architecture:
    - Modular Routing: Dynamically loads views based on session state.
    - Global Error Boundary: Catches crashes to prevent "White Screen of Death".
    - Design System 2.0: Injects a complete CSS framework for UI consistency.
    - Security: Session state validation and sanitization.

Author: Batman
Version: 5.0 (Final Release)
"""

import streamlit as st
import time
import sys
import traceback
from datetime import datetime

# --- IMPORT ENTERPRISE MODULES ---
try:
    import phase1  # Core Engine (Database & Config)
    import phase2  # Seller Command Center
    import phase3  # Discovery Engine
    import phase4  # Secure Checkout
except ImportError as e:
    st.error(f"CRITICAL SYSTEM ERROR: Missing modules. {e}")
    st.stop()

# ==============================================================================
# 1. SYSTEM INITIALIZATION & PERFORMANCE TRACKING
# ==============================================================================

# Start timer to measure page load performance
START_TIME = time.time()

# Initialize Database & Config (Phase 1)
# This must run before any other logic to ensure DB integrity
phase1.init_app()

# Load Data into Memory
try:
    data = phase1.load_data()
except Exception as e:
    st.error("FATAL ERROR: Could not load database.")
    st.error(str(e))
    st.stop()

# ==============================================================================
# 2. DESIGN SYSTEM & UI FRAMEWORK
# ==============================================================================

def inject_design_system():
    """
    Injects the comprehensive CSS framework.
    This overrides Streamlit's defaults to create a custom 'Nukr' brand identity.
    """
    st.markdown("""
        <style>
        /* --- 1. FONT STACK --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap');

        /* --- 2. CSS VARIABLES (THEME CONFIG) --- */
        :root {
            /* Colors */
            --primary-black: #0F172A;
            --primary-white: #FFFFFF;
            --secondary-gray: #F8FAFC;
            --text-main: #1E293B;
            --text-muted: #64748B;
            --accent-gold: #D4AF37;
            --border-color: #E2E8F0;
            --success-green: #10B981;
            
            /* Spacing & Layout */
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 24px;
            --radius-full: 9999px;
            
            /* Shadows */
            --shadow-subtle: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-float: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        /* --- 3. GLOBAL RESET --- */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-main);
            background-color: var(--primary-white);
            -webkit-font-smoothing: antialiased;
        }

        /* --- 4. TYPOGRAPHY --- */
        h1, h2, h3, h4 {
            font-family: 'Playfair Display', serif;
            color: var(--primary-black);
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        
        code { font-family: 'JetBrains Mono', monospace; }

        /* --- 5. COMPONENT OVERRIDES --- */
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: var(--secondary-gray);
            border-right: 1px solid var(--border-color);
        }
        
        /* Buttons (The "Nukr Pill") */
        div.stButton > button {
            background-color: var(--primary-black);
            color: var(--primary-white);
            border: 1px solid transparent;
            border-radius: var(--radius-full);
            padding: 0.5rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-subtle);
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-float);
            background-color: #334155;
            border-color: #334155;
            color: var(--primary-white);
        }
        
        div.stButton > button:active {
            transform: translateY(0);
        }
        
        /* Input Fields */
        input[type="text"], input[type="number"], textarea, select {
            border: 1px solid var(--border-color) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.75rem !important;
            background-color: var(--primary-white) !important;
            transition: border-color 0.2s ease;
        }
        
        input:focus, textarea:focus {
            border-color: var(--primary-black) !important;
            box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.1) !important;
        }

        /* Cards & Containers */
        div[data-testid="stVerticalBlock"] > div {
            /* border-radius: var(--radius-md); */
        }
        
        /* Images */
        img {
            border-radius: var(--radius-md);
            transition: opacity 0.3s ease;
        }
        
        /* Hide Streamlit Chrome */
        #MainMenu, footer, header { visibility: hidden; }
        div[data-testid="stDecoration"] { display: none; }
        
        /* Utility Classes */
        .nukr-badge {
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

# Inject the Design System
inject_design_system()

# ==============================================================================
# 3. GLOBAL ERROR BOUNDARY
# ==============================================================================

def error_boundary(func):
    """
    Decorator to wrap main execution. 
    Prevents the app from showing raw Python tracebacks to users.
    """
    def wrapper():
        try:
            func()
        except Exception as e:
            st.error("⚠️ An unexpected error occurred.")
            with st.expander("Developer Details"):
                st.code(traceback.format_exc())
            
            st.markdown("---")
            if st.button("♻️ Restart Application"):
                st.rerun()
    return wrapper

# ==============================================================================
# 4. NAVIGATION COMPONENT (SIDEBAR)
# ==============================================================================

def render_sidebar():
    """Renders the persistent navigation sidebar."""
    with st.sidebar:
        # Branding
        st.markdown("""
            <div style="margin-bottom: 2rem;">
                <h2 style="font-size: 1.8rem; margin:0; line-height: 1;">Nukr<span style="color:#D4AF37">.</span></h2>
                <p style="font-size: 0.75rem; color: #64748B; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase;">Hyperlocal Marketplace</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Navigation Menu
        # We use a radio button styled as a menu list
        selection = st.radio(
            "Main Menu",
            ["Explore Market", "Seller Dashboard", "My Account", "Help Center"],
            label_visibility="collapsed",
            index=0
        )
        
        st.markdown("---")
        
        # Context-Aware Widgets
        if selection == "Explore Market":
            # Show Cart Summary if items exist (Future feature)
            # if st.session_state.get('cart'): 
            #    st.metric("My Cart", f"{len(st.session_state['cart'])} Items")
            
            st.caption("🔥 **Trending in Karachi**")
            st.markdown("""
            - Vintage Watches
            - Crochet Tops
            - Silver Jewelry
            """)
            
        elif selection == "Seller Dashboard":
            st.info("💡 **Pro Tip:** \nUpdate your stock daily to appear at the top of search results.")
            
        st.markdown("---")
        st.caption(f"v{phase1.Config.VERSION} • {datetime.now().year}")

    return selection

# ==============================================================================
# 5. MAIN APPLICATION LOGIC
# ==============================================================================

@error_boundary
def main():
    """
    The Main Event Loop.
    Determines which 'Phase' to load based on user interaction.
    """
    
    # -------------------------------------------
    # A. GLOBAL OVERRIDE: CHECKOUT FLOW
    # -------------------------------------------
    # If the user has clicked "Buy" on any product, we override the entire UI
    # to show the Secure Checkout Wizard (Phase 4).
    # This ensures the checkout feels like a distinct, focused process.
    
    if st.session_state.get("selected_product"):
        # Wrap in container for layout control
        with st.container():
            phase4.render_checkout(data, phase1.save_data)
        return  # EXIT main() to prevent other views from loading

    # -------------------------------------------
    # B. STANDARD NAVIGATION
    # -------------------------------------------
    nav_selection = render_sidebar()

    # -------------------------------------------
    # C. ROUTING LOGIC
    # -------------------------------------------
    
    if nav_selection == "Explore Market":
        # Load Phase 3: The Buyer Discovery Engine
        # Handles Search, Feed, PDP, and Vendor Stores
        phase3.render_buyer_feed(data)
        
    elif nav_selection == "Seller Dashboard":
        # Load Phase 2: The Vendor Command Center
        # Handles Inventory, Orders, and Settings
        phase2.render_seller_dashboard(data, phase1.save_data)
        
    elif nav_selection == "My Account":
        # Placeholder for User Profile System
        st.title("My Account")
        st.markdown("""
            <div style="background-color: #F8FAFC; padding: 2rem; border-radius: 12px; border: 1px solid #E2E8F0;">
                <h3>User Profiles</h3>
                <p>Track your orders, manage your wishlist, and save addresses.</p>
                <br>
                <button style="background: #E2E8F0; color: #94A3B8; border: none; padding: 8px 16px; border-radius: 20px;">Coming Soon</button>
            </div>
        """, unsafe_allow_html=True)
        
    elif nav_selection == "Help Center":
        st.title("Help Center")
        with st.expander("How do I sell on Nukr?", expanded=True):
            st.write("Go to 'Seller Dashboard', register your shop name, and start uploading items!")
        with st.expander("Is payment secure?"):
            st.write("Yes. We support Cash on Delivery (COD) and direct Bank Transfers verified by sellers.")
        with st.expander("How do returns work?"):
            st.write("Each seller has their own return policy. Check the 'Sold by' section on the product page.")

    # -------------------------------------------
    # D. PERFORMANCE FOOTER
    # -------------------------------------------
    # Useful for debugging slow loads in production
    execution_time = time.time() - START_TIME
    # st.caption(f"Server processing time: {execution_time:.4f}s") 
    # (Uncomment above line if you want to see speed stats)

# ==============================================================================
# 6. EXECUTION ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()
