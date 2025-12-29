import streamlit as st
import pandas as pd
from datetime import datetime
import phase1  # Importing for helper functions

# --- HELPER FUNCTIONS FOR PHASE 2 ---

def _calculate_metrics(vendor_name, data):
    """Calculates total sales and order count for a specific vendor."""
    vendor_orders = [o for o in data["orders"] if o["vendor"] == vendor_name]
    total_sales = sum(o["price"] for o in vendor_orders)
    total_orders = len(vendor_orders)
    pending_orders = len([o for o in vendor_orders if o["status"] == "Pending"])
    return total_sales, total_orders, pending_orders

def render_seller_dashboard(data, save_callback):
    """
    The main view for Sellers.
    Handles Profile Creation, Inventory Management, and Order Processing.
    """
    st.title("Seller Dashboard 🏪")
    st.caption("Manage your store, track sales, and fulfill orders.")
    
    # --- STEP 1: LOGIN SIMULATION (MVP) ---
    # Since we don't have passwords yet, we use a dropdown to 'switch' accounts.
    all_vendor_names = [v["name"] for v in data["vendors"]]
    
    if not all_vendor_names:
        st.warning("No sellers found. Create your store profile below!")
        current_vendor = None
    else:
        # Allow user to select "New Store" or an existing one
        option = st.selectbox("Select Account / Action", ["➕ Register New Store"] + all_vendor_names)
        
        if option == "➕ Register New Store":
            current_vendor = None
        else:
            current_vendor = phase1.get_vendor_by_name(data, option)

    st.markdown("---")

    # --- MAIN TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "📦 Add Stock", "📋 Manage Inventory", "🚚 Orders & Sales"])

    # ==========================================
    # TAB 1: STORE PROFILE (Registration & Edit)
    # ==========================================
    with tab1:
        st.subheader("Store Settings")
        
        # Pre-fill form if editing existing vendor
        default_name = current_vendor["name"] if current_vendor else ""
        default_insta = current_vendor["insta"] if current_vendor else ""
        default_bank = current_vendor["bank"] if current_vendor else ""
        
        with st.form("vendor_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                store_name = st.text_input(
                    "Store Name", 
                    value=default_name, 
                    help="This will be unique to your shop.",
                    disabled=(current_vendor is not None) # Lock name after creation to prevent data issues
                )
                insta_handle = st.text_input("Instagram Handle", value=default_insta, help="e.g. crochet_queen (No @ symbol)")
            
            with col2:
                bank_details = st.text_area(
                    "Bank Details for Transfers", 
                    value=default_bank, 
                    height=100,
                    help="Enter your EasyPaisa/JazzCash/Bank info here. Customers will see this at checkout."
                )
            
            submitted = st.form_submit_button("Save Store Profile")
            
            if submitted:
                # VALIDATION 1: Empty Fields
                if not store_name or not bank_details:
                    st.error("Store Name and Bank Details are required!")
                
                # VALIDATION 2: Duplicate Name (Only if creating new)
                elif not current_vendor and any(v["name"].lower() == store_name.lower() for v in data["vendors"]):
                    st.error("This Store Name is already taken. Please choose another.")
                
                else:
                    if current_vendor:
                        # UPDATE existing
                        current_vendor["insta"] = insta_handle
                        current_vendor["bank"] = bank_details
                        st.success("Profile Updated Successfully!")
                    else:
                        # CREATE new
                        new_vendor = {
                            "id": len(data["vendors"]) + 1,
                            "name": store_name,
                            "insta": insta_handle,
                            "bank": bank_details,
                            "joined_date": str(datetime.now())
                        }
                        data["vendors"].append(new_vendor)
                        st.success(f"Welcome to Nukr, {store_name}! Go to 'Add Stock' to start selling.")
                    
                    save_callback(data)
                    st.rerun() # Refresh to update the dropdown

    # ==========================================
    # TAB 2: ADD STOCK (Upload)
    # ==========================================
    with tab2:
        if not current_vendor:
            st.info("Please register or select a store above to add products.")
        else:
            st.subheader(f"Add Product to {current_vendor['name']}")
            
            with st.form("add_product_form"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # CATEGORY SELECTION (Pulled from Phase 1 Config)
                    category = st.selectbox("Category", data["categories"])
                    price = st.number_input("Price (PKR)", min_value=1, step=50)
                
                with col2:
                    p_name = st.text_input("Product Title")
                    # MVP IMAGE TRICK: Using URLs because Streamlit Cloud can't store file uploads permanently without AWS S3.
                    img_url = st.text_input(
                        "Image URL", 
                        placeholder="https://...", 
                        help="Right-click an image on your Instagram/Facebook -> 'Copy Image Address' and paste it here."
                    )

                submit_product = st.form_submit_button("🚀 Launch Product")
                
                if submit_product:
                    if not p_name:
                        st.error("Product Title is required.")
                    else:
                        new_item = {
                            "id": len(data["products"]) + 1,
                            "vendor": current_vendor["name"],
                            "name": p_name,
                            "category": category,
                            "price": int(price),
                            "image": img_url if img_url else "",
                            "active": True,
                            "added_on": str(datetime.now())
                        }
                        data["products"].append(new_item)
                        save_callback(data)
                        st.success(f"'{p_name}' is now live!")

    # ==========================================
    # TAB 3: MANAGE INVENTORY (Delete/View)
    # ==========================================
    with tab3:
        if not current_vendor:
            st.info("Select a store to manage inventory.")
        else:
            st.subheader("Your Active Listings")
            
            # Filter products for this vendor
            my_products = [p for p in data["products"] if p["vendor"] == current_vendor["name"] and p.get("active", True)]
            
            if not my_products:
                st.warning("No active products found.")
            else:
                # Display as a table with Delete buttons
                for p in my_products:
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                    with col1:
                        if p["image"]:
                            st.image(p["image"], width=50)
                        else:
                            st.write("📷")
                    with col2:
                        st.write(f"**{p['name']}**")
                        st.caption(f"{p['category']} | {phase1.format_currency(p['price'])}")
                    with col3:
                        st.write("✅ Active")
                    with col4:
                        if st.button("🗑️ Delete", key=f"del_{p['id']}"):
                            # Soft Delete (We mark active=False instead of removing to keep order history)
                            p["active"] = False
                            save_callback(data)
                            st.rerun()
                    st.markdown("---")

    # ==========================================
    # TAB 4: ORDERS & SALES (The Business Logic)
    # ==========================================
    with tab4:
        if not current_vendor:
            st.info("Select a store to view orders.")
        else:
            # 1. METRICS AT A GLANCE
            sales, count, pending = _calculate_metrics(current_vendor["name"], data)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Sales", phase1.format_currency(sales))
            m2.metric("Total Orders", count)
            m3.metric("Pending Orders", pending, delta_color="inverse")
            
            st.markdown("---")
            st.subheader("Order History")
            
            # 2. ORDER LIST
            my_orders = [o for o in data["orders"] if o["vendor"] == current_vendor["name"]]
            
            if not my_orders:
                st.info("No orders yet. Share your store link!")
            else:
                # Sort by newest first (assuming IDs increase with time)
                for order in reversed(my_orders):
                    with st.expander(f"Order #{order['id']} - {order['product']} ({order['status']})"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Customer:** {order['customer']}")
                            st.write(f"**Phone:** {order['phone']}")
                            st.write(f"**Address:** {order['address']}")
                            st.caption(f"Date: {order['date']}")
                        with c2:
                            st.write(f"**Item:** {order['product']}")
                            st.write(f"**Price:** {phase1.format_currency(order['price'])}")
                            st.write(f"**Payment:** {order['method']}")
                            
                            # STATUS UPDATER
                            current_status = order.get("status", "Pending")
                            new_status = st.selectbox(
                                "Update Status", 
                                ["Pending", "Shipped", "Completed", "Cancelled"], 
                                index=["Pending", "Shipped", "Completed", "Cancelled"].index(current_status),
                                key=f"status_{order['id']}"
                            )
                            
                            if new_status != current_status:
                                order["status"] = new_status
                                save_callback(data)
                                st.success("Status Updated!")
                                st.rerun()