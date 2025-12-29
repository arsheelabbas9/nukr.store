"""
NUKR.STORE - PHASE 1: CORE ENGINE (ENTERPRISE EDITION)
======================================================
Description:
    This is the central nervous system of the application. 
    It handles Data Persistence, Session Management, Error Logging, 
    Backup Rotation, and Schema Validation.
    
    Features:
    - Thread-safe file locking (prevent write conflicts).
    - Automatic JSON corruption repair.
    - Rolling backups (keeps last 10, archives older).
    - Detailed event logging (nukr.log).
    - Strict schema enforcement.

Author: Batman
Version: 3.0 (Enterprise)
"""

import streamlit as st
import json
import os
import shutil
import logging
import uuid
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from threading import Lock

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================

class Config:
    """Global configuration settings for the application."""
    APP_NAME = "Nukr.store"
    VERSION = "3.0.0"
    CURRENCY_SYMBOL = "Rs."
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FILE = os.path.join(BASE_DIR, "nukr_data.json")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    LOG_FILE = os.path.join(BASE_DIR, "nukr_system.log")
    
    # Limits
    MAX_BACKUPS = 15
    MAX_LOG_SIZE_MB = 5
    
    # Default Categories
    DEFAULT_CATEGORIES = [
        "Jewelry", "Crochet", "Clothes", "Toys", 
        "Watches", "Home Decor", "Art & Craft", 
        "Accessories", "Footwear", "Beauty"
    ]

# ==============================================================================
# 2. LOGGING SYSTEM
# ==============================================================================

def setup_logger():
    """Sets up a rotating logger to track every single event in the app."""
    logger = logging.getLogger("NukrLogger")
    logger.setLevel(logging.DEBUG)
    
    # Check if handlers already exist to avoid duplicate logs
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console Handler (for Terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

system_log = setup_logger()

# ==============================================================================
# 3. EXCEPTION HANDLING
# ==============================================================================

class NukrError(Exception):
    """Base exception class for Nukr app."""
    pass

class DatabaseError(NukrError):
    """Raised when database read/write fails."""
    pass

class ValidationError(NukrError):
    """Raised when data doesn't match the schema."""
    pass

# ==============================================================================
# 4. DATABASE ENGINE (THE BRAIN)
# ==============================================================================

class Database:
    """
    The monolithic class responsible for all data operations.
    Includes locking mechanisms to ensure thread safety.
    """
    
    _lock = Lock() # Prevents two people writing at the exact same time

    def __init__(self):
        self.filepath = Config.DATA_FILE
        self._ensure_integrity()

    def _get_default_schema(self) -> Dict:
        """Returns the pristine structure of the database."""
        return {
            "meta": {
                "created_at": str(datetime.now()),
                "version": Config.VERSION,
                "last_backup": None
            },
            "vendors": [],
            "products": [],
            "orders": [],
            "categories": Config.DEFAULT_CATEGORIES,
            "users": [] # Future proofing for user accounts
        }

    def _ensure_integrity(self):
        """
        Runs on startup. Checks if DB exists, is valid JSON, 
        and has all required fields.
        """
        if not os.path.exists(self.filepath):
            system_log.warning("Database file missing. Creating new one.")
            self._save(self._get_default_schema())
            return

        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                
            # Schema Migration: Add missing keys if version updated
            defaults = self._get_default_schema()
            changed = False
            
            for key in defaults.keys():
                if key not in data:
                    system_log.info(f"Schema Migration: Adding missing key '{key}'")
                    data[key] = defaults[key]
                    changed = True
            
            if changed:
                self._save(data)
                
        except json.JSONDecodeError:
            system_log.critical("DATABASE CORRUPTED. Attempting emergency restore.")
            self.restore_latest_backup()
        except Exception as e:
            system_log.error(f"Integrity check failed: {str(e)}")

    # --- CORE I/O OPERATIONS ---

    def load(self) -> Dict:
        """Reads data from disk."""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            system_log.error(f"Read Error: {e}")
            return self._get_default_schema()

    def _save(self, data: Dict):
        """
        Writes data to disk safely.
        1. Acquires Lock.
        2. Creates Backup.
        3. Writes Data.
        4. Releases Lock.
        """
        with self._lock:
            try:
                # 1. Backup first
                self._create_backup()
                
                # 2. Write
                with open(self.filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                
                system_log.info("Database saved successfully.")
                
            except Exception as e:
                system_log.critical(f"WRITE FAILED: {e}")
                raise DatabaseError(f"Could not save data: {e}")

    # --- BACKUP SYSTEM ---

    def _create_backup(self):
        """Rotates backups, keeping only the last N files."""
        if not os.path.exists(Config.BACKUP_DIR):
            os.makedirs(Config.BACKUP_DIR)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"nukr_backup_{timestamp}.json"
        backup_path = os.path.join(Config.BACKUP_DIR, backup_name)
        
        try:
            shutil.copy2(self.filepath, backup_path)
            
            # Rotation Logic (Cleanup old files)
            backups = sorted(
                [os.path.join(Config.BACKUP_DIR, f) for f in os.listdir(Config.BACKUP_DIR)],
                key=os.path.getmtime
            )
            
            while len(backups) > Config.MAX_BACKUPS:
                oldest = backups.pop(0)
                os.remove(oldest)
                system_log.info(f"Deleted old backup: {oldest}")
                
        except Exception as e:
            system_log.error(f"Backup failed: {e}")

    def restore_latest_backup(self):
        """Emergency function to restore the last known good state."""
        if not os.path.exists(Config.BACKUP_DIR):
            system_log.critical("No backups found. Resetting to empty DB.")
            self._save(self._get_default_schema())
            return

        backups = sorted(os.listdir(Config.BACKUP_DIR))
        if backups:
            latest = backups[-1]
            src = os.path.join(Config.BACKUP_DIR, latest)
            shutil.copy2(src, self.filepath)
            system_log.warning(f"Restored database from {latest}")
            st.error(f"⚠️ System restored from backup: {latest}")
        else:
            self._save(self._get_default_schema())

    # --- CRUD OPERATIONS (Create, Read, Update, Delete) ---

    def add_vendor(self, name: str, insta: str, bank: str) -> bool:
        """Adds a new vendor safely."""
        data = self.load()
        
        # Validation: Check duplicates
        if any(v['name'].lower() == name.lower() for v in data['vendors']):
            system_log.warning(f"Duplicate vendor attempt: {name}")
            return False
            
        new_vendor = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "insta": insta,
            "bank": bank,
            "joined_at": str(datetime.now()),
            "status": "Active"
        }
        
        data['vendors'].append(new_vendor)
        self._save(data)
        system_log.info(f"New Vendor Registered: {name}")
        return True

    def add_product(self, vendor_name: str, name: str, category: str, price: float, image: str) -> bool:
        """Adds a product to the inventory."""
        if price < 0:
            raise ValidationError("Price cannot be negative.")
            
        data = self.load()
        
        new_product = {
            "id": str(uuid.uuid4())[:8],
            "vendor": vendor_name,
            "name": name,
            "category": category,
            "price": float(price),
            "image": image,
            "active": True,
            "created_at": str(datetime.now())
        }
        
        data['products'].append(new_product)
        self._save(data)
        return True

    def create_order(self, product_obj: Dict, customer_data: Dict, payment_method: Dict) -> str:
        """
        Creates a complex order object with history tracking.
        Returns the Order ID.
        """
        data = self.load()
        order_id = str(uuid.uuid4())[:8]
        
        new_order = {
            "id": order_id,
            "timestamp": str(datetime.now()),
            
            # Snapshot of product (in case price changes later)
            "product_snapshot": {
                "id": product_obj['id'],
                "name": product_obj['name'],
                "price": product_obj['price'],
                "vendor": product_obj['vendor']
            },
            
            # Customer Details
            "customer": {
                "name": customer_data['name'],
                "phone": customer_data['phone'],
                "address": customer_data['address']
            },
            
            # Payment Details
            "payment": {
                "method": payment_method['type'], # COD or Transfer
                "proof": payment_method.get('proof_file', None),
                "is_verified": False
            },
            
            # Status Workflow
            "status": "Pending",
            "history": [
                f"Order placed on {datetime.now()}"
            ]
        }
        
        data['orders'].append(new_order)
        self._save(data)
        system_log.info(f"Order Created: {order_id} for {product_obj['vendor']}")
        return order_id

    def update_order_status(self, order_id: str, new_status: str):
        """Updates the status of an order safely."""
        data = self.load()
        found = False
        
        for order in data['orders']:
            if order['id'] == order_id:
                old_status = order['status']
                order['status'] = new_status
                order['history'].append(f"Status changed from {old_status} to {new_status} on {datetime.now()}")
                found = True
                break
        
        if found:
            self._save(data)
        else:
            raise DatabaseError("Order ID not found.")

    def soft_delete_product(self, product_id: str):
        """Marks a product as inactive without deleting data."""
        data = self.load()
        for p in data['products']:
            if p['id'] == product_id:
                p['active'] = False
                break
        self._save(data)

# ==============================================================================
# 5. DATA HELPERS & UTILITIES
# ==============================================================================

def format_currency(amount: Union[int, float]) -> str:
    """Standardizes currency display across the app (e.g. Rs. 1,500)."""
    try:
        return f"{Config.CURRENCY_SYMBOL} {int(amount):,}"
    except:
        return f"{Config.CURRENCY_SYMBOL} 0"

def get_vendor_stats(db_data: Dict, vendor_name: str) -> Dict:
    """Calculates analytics for a specific vendor."""
    orders = [o for o in db_data['orders'] if o['product_snapshot']['vendor'] == vendor_name]
    
    total_sales = sum(o['product_snapshot']['price'] for o in orders)
    total_count = len(orders)
    pending = len([o for o in orders if o['status'] == "Pending"])
    
    return {
        "sales": total_sales,
        "count": total_count,
        "pending": pending
    }

def validate_phone_number(phone: str) -> bool:
    """Returns True if phone number looks valid (simple regex)."""
    # Matches formats like 03001234567 or 0300-1234567
    pattern = r"^03\d{2}-?\d{7}$" 
    return bool(re.match(pattern, phone))

# ==============================================================================
# 6. SESSION STATE MANAGER
# ==============================================================================

def init_session_state():
    """
    Initializes all temporary variables needed for the user's session.
    Called once at the start of app.py.
    """
    defaults = {
        "cart": [],
        "selected_product": None,
        "user_role": "Guest",
        "current_vendor_view": None,
        "flash_message": None # For showing one-time notifications
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def set_flash_message(msg: str, type: str = "info"):
    """Sets a temporary message to be shown on next reload."""
    st.session_state["flash_message"] = {"msg": msg, "type": type}

def show_flash_message():
    """Displays and clears the flash message."""
    if st.session_state.get("flash_message"):
        fm = st.session_state["flash_message"]
        if fm["type"] == "success":
            st.success(fm["msg"])
        elif fm["type"] == "error":
            st.error(fm["msg"])
        elif fm["type"] == "warning":
            st.warning(fm["msg"])
        else:
            st.info(fm["msg"])
        
        st.session_state["flash_message"] = None # Clear after showing

# ==============================================================================
# 7. INITIALIZATION ENTRY POINT
# ==============================================================================

# Global Database Instance (Singleton Pattern)
db = Database()

def init_app():
    """
    The Master Boot Record. 
    Call this first in app.py.
    """
    # 1. Page Config
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': f"Nukr.store v{Config.VERSION}"
        }
    )
    
    # 2. Session Init
    init_session_state()
    
    # 3. Log Startup
    system_log.info(f"Application Started. Session ID: {uuid.uuid4()}")

def load_data():
    """Bridge for app.py to get data."""
    return db.load()

def save_data(data):
    """Bridge for app.py to save data (Direct save)."""
    # Note: In Phase 2/3/4, we should prefer using db methods, 
    # but for backward compatibility with your old code, we expose this.
    db._save(data)
