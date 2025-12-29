import streamlit as st
import phase1  # Helper functions

# --- HELPER: PRODUCT CARD UI ---
def _render_product_card(product, col):
    """
    Renders a single product card inside a column.
    """
    with col:
        # 1. Image Handling (with fallback)
        image_url = product["image"] if product["image"] else "https://via.placeholder.com/300x300?text=No+Image"
        st.image(image_url, use_column_width=True)
        
        # 2. Details
        st.markdown(f"**{product['name']}**")
        st.caption(f"Shop: {product['vendor']}")
        st.markdown(f"**{phase1.format_currency(product['price'])}**")
        
        # 3. Action Buttons
        # We use columns inside the card for small buttons
        b1, b2 = st.columns(2)
        with b1:
            # The BUY trigger
            if st.button("Buy Now", key=f"buy_{product['id']}"):
                st.session_state["selected_product"] = product
                st.rerun() # Forces app.py to reload and see the Checkout state
        with b2:
            # The "Visit Store" trigger
            if st.button("Visit Shop", key=f"visit_{product['id']}"):
                st.session_state["view_vendor"] = product["vendor"]
                st.rerun()

def render_buyer_feed(data):
    """
    Main Buyer Interface.
    Handles Search, Filtering, and Store Directory.
    """
    st.title("Find Local Treasures 💎")
    
    # --- NAVIGATION STATE MANAGEMENT ---
    # If the user clicked "Visit Shop", we default the search to that shop
    default_search = ""
    if "view_vendor" in st.session_state and st.session_state["view_vendor"]:
        st.info(f"Viewing Store: {st.session_state['view_vendor']}")
        if st.button("← Clear Filter (Show All)"):
            del st.session_state["view_vendor"]
            st.rerun()
        # We filter the logic below using this state

    # --- TABS FOR BROWSING ---
    tab_items, tab_stores = st.tabs(["🛍️ Browse Items", "🏪 Find Stores"])

    # ==========================================
    # TAB 1: BROWSE ITEMS (The Feed)
    # ==========================================
    with tab_items:
        # 1. SEARCH & FILTER BAR
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search_query = st.text_input("Search items...", placeholder="e.g. Handmade Scarf")
        with col2:
            category_filter = st.selectbox("Category", ["All"] + data["categories"])
        with col3:
            sort_option = st.selectbox("Sort By", ["Newest", "Price: Low to High", "Price: High to Low"])

        st.markdown("---")

        # 2. FILTERING LOGIC
        # Start with all active products
        active_products = [p for p in data["products"] if p.get("active", True)]
        
        # A. Filter by specific Vendor (if "Visit Shop" was clicked)
        if "view_vendor" in st.session_state:
            active_products = [p for p in active_products if p["vendor"] == st.session_state["view_vendor"]]
            st.caption(f"Showing {len(active_products)} items from **{st.session_state['view_vendor']}**")

        # B. Filter by Search Text
        if search_query:
            q = search_query.lower()
            active_products = [
                p for p in active_products 
                if q in p["name"].lower() or q in p["vendor"].lower()
            ]
        
        # C. Filter by Category
        if category_filter != "All":
            active_products = [p for p in active_products if p["category"] == category_filter]

        # D. Sorting Logic
        if sort_option == "Price: Low to High":
            active_products.sort(key=lambda x: x["price"])
        elif sort_option == "Price: High to Low":
            active_products.sort(key=lambda x: x["price"], reverse=True)
        else: # Newest (Assuming higher IDs are newer)
            active_products.sort(key=lambda x: x["id"], reverse=True)

        # 3. GRID DISPLAY
        if not active_products:
            st.warning("No items found matching your search.")
            st.image("https://via.placeholder.com/400x200?text=Try+Different+Filters", width=400)
        else:
            # Create a 3-column grid
            cols = st.columns(3)
            for idx, product in enumerate(active_products):
                # Cycle through columns 0, 1, 2
                _render_product_card(product, cols[idx % 3])

    # ==========================================
    # TAB 2: FIND STORES (The Directory)
    # ==========================================
    with tab_stores:
        st.subheader("Local Sellers Near You")
        
        search_store = st.text_input("Search for a store...", placeholder="e.g. Crochet Queen")
        
        vendors = data["vendors"]
        
        # Filter Vendors
        if search_store:
            vendors = [v for v in vendors if search_store.lower() in v["name"].lower()]
        
        if not vendors:
            st.info("No stores found.")
        else:
            for v in vendors:
                with st.expander(f"🏪 {v['name']}", expanded=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        if v["insta"]:
                            st.markdown(f"📸 **Instagram:** [{v['insta']}](https://instagram.com/{v['insta']})")
                        st.caption(f"Member since: {v.get('joined_date', 'Recently')[:10]}")
                        
                        # Count items
                        item_count = len([p for p in data["products"] if p["vendor"] == v["name"] and p.get("active", True)])
                        st.write(f"📦 **{item_count}** items available")
                        
                    with c2:
                        if st.button("View Stock", key=f"v_store_{v['id']}"):
                            st.session_state["view_vendor"] = v["name"]
                            st.rerun() # Reloads the page, which switches back to Tab 1 filtered by this vendor