import streamlit as st
import phase1  # Config & Data Engine
import phase2  # Seller Dashboard Logic
import phase3  # Buyer Feed Logic
import phase4  # Checkout Logic

# --- 1. SYSTEM CONFIGURATION ---
phase1.init_app()
data = phase1.load_data()

# --- 2. THE DESIGN ENGINE (CSS) ---
def inject_custom_css():
    st.markdown("""
        <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@700&display=swap');

        /* RESET & BASICS */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #111827;
        }

        /* HEADER & TITLES */
        h1, h2, h3 {
            font-family: 'Playfair Display', serif;
            color: #000000;
            margin-bottom: 0.5rem;
        }
        
        /* HIDE STREAMLIT ELEMENTS */
        #MainMenu, footer, header, div[data-testid="stDecoration"] {visibility: hidden;}

        /* SIDEBAR POLISH */
        section[data-testid="stSidebar"] {
            background-color: #FAFAFA; /* Very light grey */
            border-right: 1px solid #E5E7EB;
            padding-top: 1rem;
        }

        /* BUTTONS (Black Pills) */
        div.stButton > button {
            background-color: #000000;
            color: white;
            border-radius: 50px;
            padding: 0.4rem 1.2rem;
            border: 1px solid transparent;
            transition: transform 0.2s;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #333333;
            color: white;
            transform: scale(1.02);
        }

        /* INPUTS (Cleaner Borders) */
        input, textarea, select {
            border-radius: 8px !important;
            border: 1px solid #E5E7EB !important;
        }

        /* REDUCE WHITESPACE AT TOP */
        .block-container {
            padding-top: 2rem !important;
        }
        
        /* HERO SECTION STYLING */
        .hero-box {
            background: linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%);
            padding: 2rem 1rem;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 2rem;
            border: 1px solid #F3F4F6;
        }
        .hero-title { font-size: 2.5rem; font-weight: 700; color: #111827; }
        .hero-sub { color: #6B7280; font-size: 1rem; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. HELPER COMPONENTS ---

def render_compact_hero():
    """A smaller, cleaner welcome banner"""
    st.markdown("""
        <div class="hero-box">
            <div class="hero-title">Nukr<span style="color:#D4AF37">.</span> Store</div>
            <div class="hero-sub">Local Treasures. Verified Sellers. Delivered to You.</div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN APP CONTROLLER ---

def main():
    # A. CHECKOUT OVERRIDE (If buying, hide everything else)
    if st.session_state.get("selected_product"):
        with st.container():
            phase4.render_checkout(data, phase1.save_data)
        return

    # B. SIDEBAR NAVIGATION
    with st.sidebar:
        # 1. Logo Area
        st.markdown("### 🛍️ Menu")
        
        # 2. Navigation (Clean Radio Buttons)
        nav = st.radio(
            "Navigate",
            ["Explore Market", "Seller Dashboard", "My Account"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 3. USEFUL INFO (Filling the empty space)
        if nav == "Explore Market":
            st.caption("🔥 **Popular Categories**")
            st.info("Jewelry\n\nCrochet\n\nVintage Watches")
        elif nav == "Seller Dashboard":
            st.caption("📊 **Your Quick Stats**")
            st.success("Platform Fees: 0%\n\nActive Buyers: High")
            
        st.markdown("---")
        st.caption("© 2025 Nukr Inc.\nKarachi, PK")

    # C. PAGE ROUTING
    if nav == "Explore Market":
        render_compact_hero()
        phase3.render_buyer_feed(data)
    
    elif nav == "Seller Dashboard":
        st.title("Seller Dashboard")
        phase2.render_seller_dashboard(data, phase1.save_data)
        
    elif nav == "My Account":
        st.title("My Profile")
        st.write("Order tracking coming soon!")

if __name__ == "__main__":
    main()
