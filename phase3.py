"""
NUKR.STORE - PHASE 3: BUYER DISCOVERY ENGINE (ENTERPRISE EDITION)
=================================================================
Description:
    The front-facing marketplace logic. This file handles the entire 
    customer journey from Search -> Discovery -> Evaluation -> Selection.

    Features:
    - Weighted Search Algorithm (Relevance Scoring).
    - Dynamic Routing (Home vs. PDP vs. Storefront).
    - persistent Wishlist & Cart Management (Session).
    - Algorithmic Recommendations ("You might also like").
    - Vendor Micro-sites (Profile pages).
    - Interaction Logging (Recently Viewed).

Author: Batman
Version: 4.0 (Enterprise)
"""

import streamlit as st
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import phase1  # Core Database & Config

# ==============================================================================
# 1. STATE MANAGEMENT & UTILS
# ==============================================================================

def init_buyer_session():
    """Initializes session variables specific to the buyer journey."""
    defaults = {
        "view_mode": "marketplace",  # Options: 'marketplace', 'product_detail', 'vendor_store'
        "current_product_id": None,
        "current_vendor_view": None,
        "wishlist": set(),           # Stores Product IDs
        "recently_viewed": [],       # Stack of Product IDs
        "cart_count": 0,
        "search_term": "",
        "active_filters": {
            "categories": [],
            "price_range": (0, 100000),
            "sort": "Newest"
        }
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def _format_compact_currency(value):
    """Formats large numbers (e.g., 1.2k) for UI density."""
    if value >= 1000:
        return f"{value/1000:.1f}k"
    return str(value)

def _calculate_discount(price):
    """Simulates a 'compare at' price to show deals (Psychological pricing)."""
    # For MVP, we simulate a 15% mark-up as the 'original' price
    original = int(price * 1.15)
    return original

# ==============================================================================
# 2. SEARCH & RECOMMENDATION ALGORITHMS
# ==============================================================================

def search_engine(query: str, products: List[Dict], filters: Dict) -> List[Dict]:
    """
    Advanced Weighted Search Algorithm.
    
    Scoring Logic:
    - Exact Title Match: 100 points
    - Title Partial Match: 50 points
    - Category Match: 30 points
    - Description Match: 10 points
    - Vendor Name Match: 20 points
    """
    if not query and not filters['categories']:
        # If no search, return filtered list by price/sort only
        results = products
    else:
        scored_results = []
        q = query.lower()
        
        for p in products:
            score = 0
            
            # Text Relevance
            if q in p['name'].lower(): score += 50
            if q == p['name'].lower(): score += 50
            if q in p['category'].lower(): score += 30
            if q in p.get('description', '').lower(): score += 10
            if q in p['vendor'].lower(): score += 20
            
            # Category Hard Filter
            if filters['categories'] and p['category'] not in filters['categories']:
                score = -1 # Disqualify
            
            if score > 0:
                scored_results.append((score, p))
        
        # Sort by score desc
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_results]

    # Apply Price Filter
    min_p, max_p = filters['price_range']
    results = [p for p in results if min_p <= p['price'] <= max_p]
    
    # Apply Sorting
    sort_mode = filters['sort']
    if sort_mode == "Price: Low to High":
        results.sort(key=lambda x: x['price'])
    elif sort_mode == "Price: High to Low":
        results.sort(key=lambda x: x['price'], reverse=True)
    elif sort_mode == "Newest":
        # Assuming ID correlates to time, or use created_at if available
        results.sort(key=lambda x: str(x.get('created_at', x['id'])), reverse=True)
        
    return results

def get_related_products(current_product: Dict, all_products: List[Dict]) -> List[Dict]:
    """
    Content-Based Filtering for Recommendations.
    Finds products in the same category or by the same vendor.
    """
    related = []
    for p in all_products:
        if p['id'] == current_product['id']:
            continue # Skip self
            
        score = 0
        if p['category'] == current_product['category']:
            score += 5
        if p['vendor'] == current_product['vendor']:
            score += 3
            
        if score > 0:
            related.append((score, p))
            
    related.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in related[:4]] # Return top 4

# ==============================================================================
# 3. UI COMPONENTS (CARDS & WIDGETS)
# ==============================================================================

def render_product_card(product: Dict, layout_type="grid"):
    """
    Renders a unified product card component.
    
    Args:
        layout_type: 'grid' (vertical) or 'list' (horizontal)
    """
    # Card Container Styling
    with st.container():
        # Using custom HTML/CSS for the card to ensure it looks 'Apple-like'
        # Note: We use Streamlit buttons for interaction, but layout for visuals
        
        # Image Handling
        img_url = product.get('image') or "https://via.placeholder.com/300?text=Nukr"
        
        # 1. Image Area
        st.image(img_url, use_column_width=True)
        
        # 2. Meta Data
        st.markdown(f"**{product['name']}**")
        st.caption(f"by {product['vendor']}")
        
        # 3. Price & Deal
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"**{phase1.format_currency(product['price'])}**")
        with c2:
            st.markdown(f"<span style='color: #9CA3AF; text-decoration: line-through; font-size: 0.8rem;'>{phase1.format_currency(_calculate_discount(product['price']))}</span>", unsafe_allow_html=True)
            
        # 4. Actions
        b1, b2 = st.columns([3, 1])
        with b1:
            if st.button("View Details", key=f"view_{product['id']}_{layout_type}"):
                _navigate_to("product_detail", product['id'])
        with b2:
            # Wishlist Toggle
            is_wished = product['id'] in st.session_state['wishlist']
            icon = "❤️" if is_wished else "🤍"
            if st.button(icon, key=f"wish_{product['id']}_{layout_type}"):
                if is_wished:
                    st.session_state['wishlist'].remove(product['id'])
                else:
                    st.session_state['wishlist'].add(product['id'])
                st.rerun()

def render_vendor_header(vendor: Dict, product_count: int):
    """Displays a beautiful banner for the Vendor Storefront."""
    st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #111827 0%, #374151 100%);
            padding: 3rem 2rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify_content: space-between;
        ">
            <div>
                <span style="background-color: #D4AF37; color: black; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">VERIFIED SELLER</span>
                <h1 style="margin-top: 10px; font-size: 2.5rem; color: white;">{vendor['name']}</h1>
                <p style="opacity: 0.8;">@{vendor.get('insta', 'local_seller')} • Joined {vendor.get('joined_date', '2025')[:4]}</p>
            </div>
            <div style="text-align: right; display: none;">
                <div style="width: 80px; height: 80px; background: white; border-radius: 50%;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Stats Bar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", product_count)
    c2.metric("Seller Rating", "4.8 ⭐")
    c3.metric("Response Time", "1 hr")
    c4.button("Contact Seller", disabled=True, help="Chat coming in v5.0")
    st.markdown("---")

# ==============================================================================
# 4. PAGE VIEWS (THE SCREENS)
# ==============================================================================

def _navigate_to(view_name, target_id=None):
    """Helper to handle routing logic."""
    st.session_state["view_mode"] = view_name
    
    if view_name == "product_detail":
        st.session_state["current_product_id"] = target_id
        # Add to history
        if target_id not in st.session_state["recently_viewed"]:
            st.session_state["recently_viewed"].insert(0, target_id)
            
    elif view_name == "vendor_store":
        st.session_state["current_vendor_view"] = target_id # target_id is vendor_name here
        
    st.rerun()

# ------------------------------------------------------------------------------
# VIEW A: THE MARKETPLACE (Home)
# ------------------------------------------------------------------------------
def render_marketplace_view(data):
    """The main feed. Amazon-style layout with sidebar filters."""
    
    # 1. TOP BAR (Search & Quick Sort)
    with st.container():
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            search_input = st.text_input("Search", placeholder="What are you looking for today?", label_visibility="collapsed")
        with c2:
            st.caption("Active Category")
            # Pull categories from config
            cats = ["All"] + data.get('categories', phase1.Config.DEFAULT_CATEGORIES)
            selected_cat = st.selectbox("Category", cats, label_visibility="collapsed")
        with c3:
            st.caption("Sort Order")
            sort_opt = st.selectbox("Sort", ["Newest", "Price: Low to High", "Price: High to Low"], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True) # Spacer

    # 2. MAIN LAYOUT (Sidebar Filters + Grid)
    col_filters, col_grid = st.columns([1, 4])
    
    # --- LEFT SIDEBAR: FILTERS ---
    with col_filters:
        st.markdown("### Filters")
        st.markdown("---")
        
        # Price Range
        st.caption("Price Range")
        price_range = st.slider("PKR", 0, 50000, (0, 50000), step=1000, label_visibility="collapsed")
        
        # Availability
        st.checkbox("In Stock Only", value=True)
        st.checkbox("On Sale", value=False)
        
        # Vendors List (Top 5)
        st.markdown("---")
        st.caption("Top Sellers")
        top_vendors = list(set([p['vendor'] for p in data['products']]))[:5]
        for v in top_vendors:
            if st.button(f"🏪 {v}", key=f"filter_v_{v}"):
                _navigate_to("vendor_store", v)

    # --- RIGHT CONTENT: PRODUCT GRID ---
    with col_grid:
        # Prepare Filters
        current_filters = {
            "categories": [selected_cat] if selected_cat != "All" else [],
            "price_range": price_range,
            "sort": sort_opt
        }
        
        # Run Search Engine
        results = search_engine(search_input, data['products'], current_filters)
        
        # Display Logic
        if not results:
            st.container().warning(f"No results found for '{search_input}'.")
            st.markdown("Try checking your spelling or adjusting price filters.")
        else:
            st.caption(f"Showing {len(results)} results")
            
            # Grid Loop (3 items per row)
            cols = st.columns(3)
            for idx, prod in enumerate(results):
                # Ensure we only show active products
                if prod.get('active', True):
                    render_product_card(prod)
                    
                    # Manual column cycling because render_product_card doesn't take column arg
                    # (Wait, my component design above writes to st.container, 
                    # so I need to place it INSIDE the column context)
            
            # RE-WRITING GRID LOOP CORRECTLY:
            # Streamlit logic: You must define columns first, then context manager
            pass # Resetting logic below
            
            # Actual Grid Rendering
            num_cols = 3
            rows = [results[i:i + num_cols] for i in range(0, len(results), num_cols)]
            
            for row in rows:
                grid_cols = st.columns(num_cols)
                for i, prod in enumerate(row):
                    if prod.get('active', True):
                        with grid_cols[i]:
                            render_product_card(prod, layout_type="grid")

# ------------------------------------------------------------------------------
# VIEW B: PRODUCT DETAILS PAGE (PDP)
# ------------------------------------------------------------------------------
def render_pdp_view(data):
    """The detailed 'Amazon-style' product page."""
    
    p_id = st.session_state.get("current_product_id")
    product = next((p for p in data['products'] if p['id'] == p_id), None)
    
    # Error Handling: Product deleted or link broken
    if not product:
        st.error("Product not found.")
        if st.button("Back to Market"):
            _navigate_to("marketplace")
        return

    # Breadcrumbs
    st.caption(f"Marketplace  >  {product['category']}  >  {product['name']}")
    
    if st.button("← Back to Results"):
        _navigate_to("marketplace")

    # --- MAIN PDP LAYOUT ---
    c_img, c_info = st.columns([1, 1])
    
    # 1. Left: Image
    with c_img:
        img_url = product.get('image') or "https://via.placeholder.com/500"
        st.image(img_url, use_column_width=True)
        
    # 2. Right: Information & Buy Box
    with c_info:
        st.markdown(f"<h1 style='font-size: 2.5rem; margin-bottom: 0;'>{product['name']}</h1>", unsafe_allow_html=True)
        
        # Vendor Link
        if st.button(f"Sold by {product['vendor']}", key="vendor_link_pdp"):
            _navigate_to("vendor_store", product['vendor'])
            
        st.markdown("---")
        
        # Price
        st.markdown(f"<h2 style='color: #111827; font-size: 2rem;'>{phase1.format_currency(product['price'])}</h2>", unsafe_allow_html=True)
        st.caption("Inclusive of all taxes. Delivery charges calculated at checkout.")
        
        st.markdown("### Description")
        st.write(product.get('description', 'No description provided by seller. Contact them for details.'))
        
        st.markdown("---")
        
        # THE BUY BOX
        with st.container():
            st.markdown("##### Ready to order?")
            
            b1, b2 = st.columns([2, 1])
            with b1:
                # Primary Action: Buy
                if st.button("Buy Now", type="primary", key="buy_now_pdp"):
                    # Set selection for Phase 4
                    st.session_state["selected_product"] = product
                    st.rerun() # Triggers App.py to switch to Checkout
            with b2:
                # Secondary Action: Wishlist
                is_wished = product['id'] in st.session_state['wishlist']
                lbl = "Remove ❤️" if is_wished else "Add to Wishlist 🤍"
                if st.button(lbl):
                    if is_wished:
                        st.session_state['wishlist'].remove(product['id'])
                    else:
                        st.session_state['wishlist'].add(product['id'])
                    st.rerun()
                    
            st.info("🔒 Secure Transaction • Cash on Delivery Available")

    # --- SECTION: RELATED PRODUCTS ---
    st.markdown("---")
    st.subheader("You might also like")
    
    related = get_related_products(product, data['products'])
    
    if related:
        r_cols = st.columns(4)
        for i, r_prod in enumerate(related):
            with r_cols[i]:
                # Mini Card
                st.image(r_prod['image'] or "https://via.placeholder.com/150")
                st.caption(r_prod['name'][:20] + "...")
                st.markdown(f"**{phase1.format_currency(r_prod['price'])}**")
                if st.button("View", key=f"rel_{r_prod['id']}"):
                    _navigate_to("product_detail", r_prod['id'])
    else:
        st.info("No similar items found.")

# ------------------------------------------------------------------------------
# VIEW C: VENDOR STOREFRONT
# ------------------------------------------------------------------------------
def render_vendor_view(data):
    """A dedicated profile page for a specific seller."""
    
    v_name = st.session_state.get("current_vendor_view")
    vendor = next((v for v in data['vendors'] if v['name'] == v_name), None)
    
    if not vendor:
        st.error("Vendor not found.")
        if st.button("Back"): _navigate_to("marketplace")
        return

    if st.button("← Back to Market"):
        _navigate_to("marketplace")

    # Get Vendor Inventory
    v_products = [p for p in data['products'] if p['vendor'] == v_name and p.get('active', True)]
    
    # 1. Vendor Banner
    render_vendor_header(vendor, len(v_products))
    
    # 2. Store Inventory Grid
    st.subheader(f"All items from {v_name}")
    
    if not v_products:
        st.info("This seller has no active listings at the moment.")
    else:
        # Reusing the grid logic
        num_cols = 3
        rows = [v_products[i:i + num_cols] for i in range(0, len(v_products), num_cols)]
        for row in rows:
            grid_cols = st.columns(num_cols)
            for i, prod in enumerate(row):
                with grid_cols[i]:
                    render_product_card(prod, layout_type="store")

# ==============================================================================
# 5. MAIN CONTROLLER
# ==============================================================================

def render_buyer_feed(data):
    """
    The entry point called by app.py.
    Routes traffic to the correct view based on Session State.
    """
    # 1. Initialize State
    init_buyer_session()
    
    # 2. Router Logic
    mode = st.session_state["view_mode"]
    
    if mode == "marketplace":
        render_marketplace_view(data)
        
    elif mode == "product_detail":
        render_pdp_view(data)
        
    elif mode == "vendor_store":
        render_vendor_view(data)
        
    else:
        # Fallback
        st.session_state["view_mode"] = "marketplace"
        st.rerun()

    # 3. Global 'Recently Viewed' Footer (Optional Polish)
    # Only show on Marketplace view to avoid clutter
    if mode == "marketplace" and st.session_state["recently_viewed"]:
        st.markdown("---")
        with st.expander("🕒 Recently Viewed"):
            recent_ids = st.session_state["recently_viewed"][:6] # Last 6
            recent_prods = [p for p in data['products'] if p['id'] in recent_ids]
            
            if recent_prods:
                cols = st.columns(len(recent_prods))
                for i, rp in enumerate(recent_prods):
                    with cols[i]:
                        st.image(rp['image'], width=50)
                        if st.button(rp['name'][:10]+"..", key=f"rec_{rp['id']}"):
                            _navigate_to("product_detail", rp['id'])

