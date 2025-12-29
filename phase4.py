import streamlit as st
from datetime import datetime
import phase1  # Helper functions

def render_checkout(data, save_callback):
    """
    Handles the Checkout Process.
    1. Shows Order Summary.
    2. Collects Customer Info.
    3. Handles Payment Logic (COD vs Transfer).
    4. Simulates Email Notification.
    """
    
    # 1. GET SELECTED PRODUCT
    product = st.session_state.get("selected_product")
    
    # Safety check: If page reloads and loses state, go back
    if not product:
        st.error("No product selected.")
        if st.button("Return to Shop"):
            st.session_state["selected_product"] = None
            st.rerun()
        return

    # Find the specific vendor data (to get their bank details)
    vendor_data = phase1.get_vendor_by_name(data, product["vendor"])

    # --- TOP NAVIGATION ---
    if st.button("← Cancel & Go Back"):
        st.session_state["selected_product"] = None
        st.rerun()

    st.title("Checkout 🛒")

    # --- LAYOUT: 2 Columns (Summary vs Form) ---
    col1, col2 = st.columns([1, 2])

    # 2. ORDER SUMMARY (Left Column)
    with col1:
        st.subheader("Order Summary")
        # Product Image
        img = product["image"] if product["image"] else "https://via.placeholder.com/300"
        st.image(img, use_column_width=True)
        
        st.markdown(f"### {product['name']}")
        st.caption(f"Sold by: **{product['vendor']}**")
        st.markdown("---")
        st.markdown(f"**Price:** {phase1.format_currency(product['price'])}")
        st.markdown(f"**Delivery:** Rs. 200") # Flat rate for MVP
        st.markdown("---")
        total = product["price"] + 200
        st.metric("Total to Pay", f"Rs. {total:,}")

    # 3. CHECKOUT FORM (Right Column)
    with col2:
        st.subheader("Shipping Details")
        
        with st.form("checkout_form"):
            # A. Customer Info
            c_name = st.text_input("Full Name")
            c_phone = st.text_input("Phone Number (Required)", help="So the rider can call you.")
            c_address = st.text_area("Full Delivery Address")
            
            st.markdown("---")
            st.subheader("Payment Method")
            
            # B. Payment Logic
            payment_method = st.radio(
                "Select how you want to pay:", 
                ["Cash on Delivery (COD)", "Bank Transfer (Upload Proof)"]
            )
            
            # C. The "Bridge" Logic (Conditional Display)
            uploaded_file = None
            if payment_method == "Bank Transfer (Upload Proof)":
                st.info("ℹ️ You are paying directly to the seller.")
                
                if vendor_data and vendor_data.get("bank"):
                    st.success(f"**Please Transfer Rs. {total:,} to:**\n\n{vendor_data['bank']}")
                    # SCREENSHOT UPLOAD
                    uploaded_file = st.file_uploader("📸 Upload Payment Screenshot", type=['png', 'jpg', 'jpeg'])
                else:
                    st.warning("⚠️ This seller has not set up their bank details yet. Please select COD.")

            # D. Submit Button
            submit_order = st.form_submit_button("✅ Confirm Order")

            if submit_order:
                # Validation
                if not c_name or not c_phone or not c_address:
                    st.error("Please fill in your Name, Phone, and Address.")
                elif payment_method == "Bank Transfer (Upload Proof)" and not uploaded_file:
                    st.error("Please upload the payment screenshot for verification.")
                else:
                    # SUCCESS! CREATE ORDER
                    
                    # 1. Handle Screenshot (For MVP/Cloud, we just save the filename)
                    # In a real app, you would upload this to AWS S3 or Cloudinary.
                    proof_status = "No Proof"
                    if uploaded_file:
                        proof_status = f"Attached: {uploaded_file.name}"
                    
                    # 2. Build Order Object
                    new_order = {
                        "id": len(data["orders"]) + 1,
                        "date": str(datetime.now().strftime("%Y-%m-%d %H:%M")),
                        
                        # Product Info
                        "product": product["name"],
                        "price": total,
                        "vendor": product["vendor"],
                        
                        # Customer Info
                        "customer": c_name,
                        "phone": c_phone,
                        "address": c_address,
                        
                        # Payment Info
                        "method": payment_method,
                        "proof": proof_status,
                        
                        # Internal Status
                        "status": "Pending" # Default status
                    }
                    
                    # 3. Save to Database
                    data["orders"].append(new_order)
                    save_callback(data)
                    
                    # 4. Simulate Email Notification
                    st.balloons()
                    st.success("🎉 Order Placed Successfully!")
                    
                    st.markdown(f"""
                        <div style="padding: 15px; border-radius: 5px; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;">
                            <strong>📧 Email Sent to Seller:</strong><br>
                            An order notification has been sent to <b>{product['vendor']}</b>.<br>
                            They will contact you at <b>{c_phone}</b> to confirm delivery.
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Clear Cart/Selection Logic
                    if st.button("Continue Shopping"):
                        st.session_state["selected_product"] = None
                        st.rerun()