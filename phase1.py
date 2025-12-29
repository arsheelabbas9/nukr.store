import streamlit as st
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Union, Any

# --- CONSTANTS & CONFIGURATION ---
DATA_FILE = "nukr_data.json"
BACKUP_DIR = "backups"
APP_NAME = "Nukr.store"
APP_ICON = "🛍️"

# Default schema structure to ensure data integrity
DEFAULT_SCHEMA = {
    "system_info": {
        "created_at": str(datetime.now()),
        "version": "1.0",
        "last_backup": None
    },
    "vendors": [],      # List of vendor profiles
    "products": [],     # List of all inventory items
    "orders": [],       # List of all transaction records
    "categories": [     # extensible category list
        "Jewelry", 
        "Crochet", 
        "Clothes", 
        "Toys", 
        "Watches", 
        "Home Decor", 
        "Art & Craft", 
        "Accessories"
    ]
}

def init_app():
    """
    Initializes the Streamlit page configuration and global session states.
    This must be called at the very top of app.py.
    """
    # 1. Page Config
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'mailto:support@nukr.store',
            'Report a bug': "mailto:bugs@nukr.store",
            'About': "# Nukr.store\nLocal Marketplace for Local People."
        }
    )

    # 2. CSS Injection for better UI (Hiding default Streamlit clutter)
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem;}
        /* Custom Button Styling */
        div.stButton > button:first-child {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
        }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # 3. Session State Initialization
    # We use session_state to track where the user is (navigation) and what they are doing.
    if "selected_product" not in st.session_state:
        st.session_state["selected_product"] = None
    
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "Buyer"  # Default view
        
    if "cart" not in st.session_state:
        st.session_state["cart"] = [] # Future proofing for multi-item cart

def _validate_schema(data: Dict) -> Dict:
    """
    Internal function to ensure loaded data has all required keys.
    If keys are missing (due to app updates), it patches them without deleting old data.
    """
    was_modified = False
    
    # 1. Check top-level keys
    for key, default_value in DEFAULT_SCHEMA.items():
        if key not in data:
            data[key] = default_value
            was_modified = True
    
    # 2. Check vendor structure integrity (simple patch)
    if "vendors" in data:
        for vendor in data["vendors"]:
            if "total_sales" not in vendor:
                vendor["total_sales"] = 0
                was_modified = True
            if "joined_date" not in vendor:
                vendor["joined_date"] = str(datetime.now())
                was_modified = True

    # Save immediately if we patched the schema
    if was_modified:
        save_data(data)
        
    return data

def create_backup():
    """
    Creates a timestamped backup of the database to prevent data loss.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    if os.path.exists(DATA_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"nukr_data_{timestamp}.json")
        try:
            shutil.copy2(DATA_FILE, backup_path)
            # Optional: Clean up old backups (keep last 5)
            backups = sorted(os.listdir(BACKUP_DIR))
            if len(backups) > 5:
                os.remove(os.path.join(BACKUP_DIR, backups[0]))
        except Exception as e:
            st.error(f"Backup failed: {e}")

def load_data() -> Dict[str, Any]:
    """
    Robust data loader.
    1. Checks if file exists.
    2. If not, creates it with DEFAULT_SCHEMA.
    3. If exists, loads JSON.
    4. Handles JSONDecodeError (corrupt file) by attempting to restore backup.
    5. Validates schema integrity.
    """
    # Case 1: File doesn't exist (First run)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(DEFAULT_SCHEMA, f, indent=4)
        return DEFAULT_SCHEMA

    # Case 2: File exists, try to read
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return _validate_schema(data)
            
    except json.JSONDecodeError:
        # Case 3: File is corrupt/empty. Try to restore backup.
        st.error("⚠️ Data file corrupted! Attempting to restore from backup...")
        
        if os.path.exists(BACKUP_DIR) and os.listdir(BACKUP_DIR):
            latest_backup = sorted(os.listdir(BACKUP_DIR))[-1]
            shutil.copy2(os.path.join(BACKUP_DIR, latest_backup), DATA_FILE)
            st.warning(f"Restored from backup: {latest_backup}")
            return load_data() # Retry load
        else:
            # Case 4: Corrupt and no backups. Critical Reset.
            st.error("CRITICAL: No backups found. Resetting database to factory defaults.")
            with open(DATA_FILE, "w") as f:
                json.dump(DEFAULT_SCHEMA, f, indent=4)
            return DEFAULT_SCHEMA

def save_data(data: Dict[str, Any]):
    """
    Saves data to JSON with atomic write safety and backup trigger.
    1. Creates a backup first.
    2. Writes data.
    """
    # 1. Trigger Backup (Maybe restrict this to once per hour in production, but okay for now)
    # create_backup() 
    
    # 2. Write Data
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Failed to save data: {e}")

# --- HELPER UTILITIES ---
# These are global utility functions used across phases

def format_currency(amount: Union[int, float]) -> str:
    """Standardizes currency display across the app."""
    return f"Rs. {int(amount):,}"

def get_vendor_by_name(data, vendor_name):
    """Helper to find a vendor object by name."""
    return next((v for v in data["vendors"] if v["name"] == vendor_name), None)

def get_product_by_id(data, product_id):
    """Helper to find a product object by ID."""
    return next((p for p in data["products"] if p["id"] == product_id), None)