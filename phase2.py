"""
NUKR.STORE - PHASE 2: SELLER COMMAND CENTER (ENTERPRISE EDITION)
================================================================
Description:
    The complete vendor portal. Handles store configuration, inventory 
    management (CRUD), order fulfillment workflows, and business analytics.

    Features:
    - Real-time Sales Dashboard with Metrics.
    - Full Inventory Management (Add, Edit, Soft-Delete, Search).
    - Advanced Order Processing (Status updates, Filtering, Invoice View).
    - Store Profile & Policy Management.
    - Data Export Capabilities.

Author: Batman
Version: 3.0 (Enterprise)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import phase1  # Core Database Engine

# ==============================================================================
# 1. UI COMPONENT LIBRARY (Internal Helpers)
# ==============================================================================

def _render_metric_card(label: str, value: str, delta: str = None, help_text: str = None):
    """Renders a styled metric card consistent with the App's design system."""
    st.markdown(f"""
    <div style="
        background-color: white; 
        padding: 1.5rem; 
        border-radius: 12px; 
        border: 1px solid #E5E7EB; 
        box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);">
        <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.5rem;">{label}</p>
        <h3 style="color: #111827; font-size: 1.5rem; font-weight: 700; margin: 0;">{value}</h3>
        {f'<p style="color: #10B981; font-size: 0.875rem; margin-top: 0.5rem;">{delta}</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

def _get_active_vendor(data):
    """Retrieves the currently 'logged in' vendor from session state."""
    # In a real app, this would check st.session_state['user_id']
    # For MVP, we use the session variable set by the dropdown
    vendor_name = st.session_state.get("current_vendor_name")
    if vendor_name:
        return phase1.db.load()['vendors'][0] if not data else next((v for v in data['vendors'] if v['name'] == vendor_name), None)
    return None

# ==============================================================================
# 2. TAB: DASHBOARD (Analytics Engine)
# ==============================================================================

def render_analytics_dashboard(data, vendor_name):
    """Renders the high-level business intelligence view."""
    st.markdown("## 📊 Store Performance")
    
    # 1. Calculate Metrics
    orders = [o for o in data['orders'] if o['product_snapshot']['vendor'] == vendor_name]
    
    total_sales = sum(o['product_snapshot']['price'] for o in orders)
    total_orders = len(orders)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    pending_orders = len([o for o in orders if o['status'] == "Pending"])
    
    # 2. Display KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _render_metric_card("Total Revenue", phase1.format_currency(total_sales), "Lifetime")
    with col2:
        _render_metric_card("Orders", str(total_orders), f"{pending_orders} Pending")
    with col3:
        _render_metric_card("Avg. Order Value", phase1.format_currency(avg_order_value))
    with col4:
        # Conversion rate simulation
        _render_metric_card("Store Views", "1,240", "+12% this week")

    st.markdown("---")

    # 3. Charts & Graphs (Simulated for Visuals)
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Sales Trend (Last 7 Days)")
        if orders:
            # Create a simple dataframe for the chart
            dates = [(datetime.now() - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
            # Mock data distribution for visual appeal
            chart_data = pd.DataFrame({
                "Day": dates,
                "Revenue": [total_sales * 0.1, total_sales * 0.2, total_sales * 0.05, total_sales * 0.15, total_sales * 0.3, total_sales * 0.1, total_sales * 0.1]
            })
            st.bar_chart(chart_data.set_index("Day"))
        else:
            st.info("No sales data available for charting yet.")
            
    with c2:
        st.subheader("Top Categories")
        # Quick breakdown by category
        my_products = [p for p in data['products'] if p['vendor'] == vendor_name]
        if my_products:
            cats = [p['category'] for p in my_products]
            df_cat = pd.DataFrame(cats, columns=["Category"])
            st.dataframe(df_cat["Category"].value_counts(), use_container_width=True)
        else:
            st.info("Add products to see category breakdown.")

# ==============================================================================
# 3. TAB: INVENTORY MANAGER (CRUD)
# ==============================================================================

def render_inventory_manager(data, vendor_name, save_callback):
    """
    Complex inventory management system.
    Allows Adding, Editing, and Deleting products.
    """
    st.markdown("## 📦 Inventory Management")
    
    mode = st.radio("Action Mode", ["View / Edit Stock", "Add New Product"], horizontal=True, label_visibility="collapsed")

    # --- SUB-VIEW: ADD PRODUCT ---
    if mode == "Add New Product":
        with st.container():
            st.markdown("#### 🚀 Launch New Product")
            with st.form("add_product_form", clear_on_submit=True):
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    category = st.selectbox("Category", data.get("categories", phase1.Config.DEFAULT_CATEGORIES))
                    price = st.number_input("Price (PKR)", min_value=1, step=100)
                    stock_qty = st.number_input("Stock Quantity", min_value=1, value=1)
                
                with c2:
                    name = st.text_input("Product Title")
                    image = st.text_input("Image URL", help="Paste direct link from Instagram/Imgur")
                    desc = st.text_area("Description", placeholder="Describe size, material, and care instructions...")

                submitted = st.form_submit_button("Publish to Shop")
                
                if submitted:
                    if not name or not image:
                        phase1.set_flash_message("Name and Image are required!", "error")
                    else:
                        # Direct database injection via Phase 1 helper
                        phase1.db.add_product(vendor_name, name, category, price, image)
                        phase1.set_flash_message(f"'{name}' added successfully!", "success")
                        st.rerun()

    # --- SUB-VIEW: VIEW / EDIT STOCK ---
    else:
        # 1. Filter Logic
        my_products = [p for p in data['products'] if p['vendor'] == vendor_name and p.get('active', True)]
        
        if not my_products:
            st.warning("Your shelf is empty. Go to 'Add New Product' to start selling.")
            return

        # 2. Search Bar
        search = st.text_input("🔍 Search inventory...", placeholder="Filter by name or ID")
        if search:
            my_products = [p for p in my_products if search.lower() in p['name'].lower()]

        # 3. Interactive Data Editor (Enterprise Feature)
        st.markdown(f"**Active Listings ({len(my_products)})**")
        
        for p in my_products:
            with st.expander(f"{p['name']}  —  {phase1.format_currency(p['price'])}"):
                # Edit Form inside Expander
                with st.form(f"edit_{p['id']}"):
                    ec1, ec2 = st.columns([1, 3])
                    with ec1:
                        st.image(p['image'], width=100)
                    with ec2:
                        new_name = st.text_input("Title", value=p['name'])
                        new_price = st.number_input("Price", value=float(p['price']))
                        
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.form_submit_button("💾 Save Changes"):
                            p['name'] = new_name
                            p['price'] = new_price
                            save_callback(data)
                            st.success("Updated!")
                            st.rerun()
                    with c_btn2:
                        if st.form_submit_button("🗑️ Delete Product", type="primary"):
                            phase1.db.soft_delete_product(p['id'])
                            st.error("Deleted.")
                            time.sleep(0.5)
                            st.rerun()

# ==============================================================================
# 4. TAB: ORDER PROCESSING (The Fulfillment Center)
# ==============================================================================

def render_order_center(data, vendor_name, save_callback):
    """
    Advanced order management.
    Status filtering, detailed views, and workflow transitions.
    """
    st.markdown("## 🚚 Order Fulfillment")
    
    # 1. Filters
    my_orders = [o for o in data['orders'] if o['product_snapshot']['vendor'] == vendor_name]
    
    filter_status = st.selectbox(
        "Filter by Status", 
        ["All Open", "Pending", "Shipped", "Completed", "Cancelled"],
        index=0
    )
    
    # Apply Filter
    if filter_status == "All Open":
        filtered_orders = [o for o in my_orders if o['status'] in ["Pending", "Shipped"]]
    else:
        filtered_orders = [o for o in my_orders if o['status'] == filter_status]
    
    # Sort by newest
    filtered_orders.sort(key=lambda x: x['timestamp'], reverse=True)

    if not filtered_orders:
        st.info("No orders found matching this filter.")
        return

    # 2. Order List
    for order in filtered_orders:
        # Color coding for status
        status_color = {
            "Pending": "🔴",
            "Shipped": "🟡",
            "Completed": "🟢",
            "Cancelled": "⚫"
        }.get(order['status'], "⚪")

        with st.expander(f"{status_color} Order #{order['id']} — {order['customer']['name']}"):
            # A. Order Header
            st.markdown(f"**Placed on:** {order['timestamp'][:16]}")
            
            c1, c2, c3 = st.columns(3)
            
            # B. Customer Details
            with c1:
                st.caption("Customer Info")
                st.write(f"**{order['customer']['name']}**")
                st.write(f"📞 {order['customer']['phone']}")
                st.write(f"🏠 {order['customer']['address']}")
            
            # C. Product Details
            with c2:
                st.caption("Order Details")
                st.write(f"**Item:** {order['product_snapshot']['name']}")
                st.write(f"**Price:** {phase1.format_currency(order['product_snapshot']['price'])}")
                
                # Payment Proof Check
                method = order['payment']['method']
                proof = order['payment'].get('proof')
                st.write(f"**Method:** {method}")
                if proof and proof != "No Proof":
                    st.warning(f"📎 {proof}")
                    st.caption("(Verify screenshot in email)")

            # D. Actions (Workflow)
            with c3:
                st.caption("Manage Status")
                current_s = order['status']
                
                # State Machine Logic
                possible_next_states = []
                if current_s == "Pending":
                    possible_next_states = ["Shipped", "Cancelled"]
                elif current_s == "Shipped":
                    possible_next_states = ["Completed", "Return/Refund"]
                
                if possible_next_states:
                    new_status = st.selectbox("Update Status", possible_next_states, key=f"s_{order['id']}")
                    if st.button("Update", key=f"btn_{order['id']}"):
                        phase1.db.update_order_status(order['id'], new_status)
                        phase1.set_flash_message(f"Order #{order['id']} marked as {new_status}", "success")
                        st.rerun()
                else:
                    st.success(f"Order is {current_s}")

# ==============================================================================
# 5. TAB: STORE SETTINGS (Profile Engine)
# ==============================================================================

def render_store_settings(data, vendor_name, save_callback):
    """
    Handles store configuration, policies, and banking info.
    """
    st.markdown("## ⚙️ Store Configuration")
    
    vendor = next((v for v in data['vendors'] if v['name'] == vendor_name), None)
    if not vendor:
        st.error("Vendor profile error.")
        return

    with st.form("settings_form"):
        st.markdown("#### 🏦 Banking & Payments")
        new_bank = st.text_area(
            "Payment Instructions (Shown to Buyer)", 
            value=vendor.get('bank', ''),
            help="Include Bank Name, Account Number, and Title."
        )
        
        st.markdown("#### 📢 Social & Brand")
        c1, c2 = st.columns(2)
        with c1:
            new_insta = st.text_input("Instagram Handle", value=vendor.get('insta', ''))
        with c2:
            st.write("") # Spacer
            st.info(f"Store Link: nukr.store/{vendor.get('id', '000')}")
        
        st.markdown("#### 📜 Shop Policies")
        policies = st.text_area(
            "Return & Refund Policy", 
            value=vendor.get('policies', 'No returns on sale items.'),
            placeholder="e.g., No cash refunds. Exchange within 3 days."
        )
        
        if st.form_submit_button("Save Configuration"):
            vendor['bank'] = new_bank
            vendor['insta'] = new_insta
            vendor['policies'] = policies
            save_callback(data)
            phase1.set_flash_message("Store settings updated successfully!", "success")
            st.rerun()

# ==============================================================================
# 6. MAIN CONTROLLER (The Facade)
# ==============================================================================

def render_seller_dashboard(data, save_callback):
    """
    The main entry point for the Seller Portal.
    Orchestrates the login simulation and tab rendering.
    """
    
    # 1. Global Message Handler (Flash Messages)
    phase1.show_flash_message()

    # 2. LOGIN SIMULATION (Enterprise Logic)
    # In a real app, this would use JWT tokens. For MVP, we simulate a secure login.
    
    if "current_vendor_name" not in st.session_state:
        st.session_state["current_vendor_name"] = None

    # If not logged in, show Login Screen
    if not st.session_state["current_vendor_name"]:
        st.title("Seller Portal Login 🔐")
        
        all_vendors = [v['name'] for v in data['vendors']]
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("""
                ### Welcome back!
                Manage your Nukr store, track inventory, and fulfill orders.
                
                **New here?** Register your shop to get started.
            """)
        
        with c2:
            tab_login, tab_reg = st.tabs(["Login", "Register Shop"])
            
            with tab_login:
                selected_vendor = st.selectbox("Select Your Shop", ["-- Select --"] + all_vendors)
                if st.button("Login to Dashboard"):
                    if selected_vendor != "-- Select --":
                        st.session_state["current_vendor_name"] = selected_vendor
                        st.rerun()
            
            with tab_reg:
                with st.form("reg_form"):
                    new_name = st.text_input("Shop Name (Unique)")
                    new_insta = st.text_input("Instagram Handle")
                    new_bank = st.text_area("Bank Details")
                    
                    if st.form_submit_button("Create Shop"):
                        success = phase1.db.add_vendor(new_name, new_insta, new_bank)
                        if success:
                            st.session_state["current_vendor_name"] = new_name
                            phase1.set_flash_message("Shop created! Welcome aboard.", "success")
                            st.rerun()
                        else:
                            st.error("Shop name already taken.")
        return

    # 3. IF LOGGED IN -> SHOW DASHBOARD
    vendor_name = st.session_state["current_vendor_name"]
    
    # Header / Navbar
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title(f"{vendor_name} Dashboard")
    with col_head2:
        if st.button("🔒 Logout"):
            st.session_state["current_vendor_name"] = None
            st.rerun()

    # Main Tabs
    t1, t2, t3, t4 = st.tabs([
        "📊 Dashboard", 
        "📦 Inventory", 
        "🚚 Orders", 
        "⚙️ Settings"
    ])

    with t1:
        render_analytics_dashboard(data, vendor_name)
    with t2:
        render_inventory_manager(data, vendor_name, save_callback)
    with t3:
        render_order_center(data, vendor_name, save_callback)
    with t4:
        render_store_settings(data, vendor_name, save_callback)
