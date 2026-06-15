import sqlite3
import os

DB_PATH = "billing_system.db"


def _sync_products_excel_safe():
    """Best-effort sync of products.xlsx; never crashes the calling operation."""
    try:
        from modules.excel_sync import sync_products_excel
        sync_products_excel()
    except Exception:
        pass


def _sync_khata_excel_safe():
    """Best-effort sync of khata.xlsx; never crashes the calling operation."""
    try:
        from modules.excel_sync import sync_khata_excel
        sync_khata_excel()
    except Exception:
        pass


def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """System ke saare professional tables ko enterprise rules ke mutabiq initialize karna"""
    # Ensure the 'database' folder exists (for pos_system.db used by the ledger tables)
    os.makedirs("database", exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Secure Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        security_question TEXT NOT NULL,
                        security_answer TEXT NOT NULL)''')
    
    # 2. Upgraded Inventory Table (Chaudhary Setup: Unit, Cost, and Sale Configuration)
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        barcode TEXT,
                        unit TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        cost_price REAL NOT NULL,
                        sale_price REAL NOT NULL)''')

    # 3. Invoices Table (Billing Engine Core)
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT,
                        total_amount REAL,
                        discount REAL,
                        net_amount REAL,
                        date TEXT,
                        payment_mode TEXT)''')

    # 4. Invoice Items Table (Profit Tracking)
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_items (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_id INTEGER NOT NULL,
                        product_id INTEGER,
                        product_name TEXT,
                        quantity INTEGER,
                        cost_price REAL,
                        sale_price REAL,
                        line_total REAL,
                        FOREIGN KEY(invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE)''')

    # 5. Khata Ledger Table (Corporate Accounts)
    cursor.execute('''CREATE TABLE IF NOT EXISTS khata (
                        khata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT NOT NULL,
                        customer_phone TEXT,
                        total_udhar REAL DEFAULT 0,
                        paid_amount REAL DEFAULT 0,
                        remaining_balance REAL DEFAULT 0)''')

    # 6. Shop / System Settings Table (Key-Value Configuration Store)
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        setting_key TEXT PRIMARY KEY,
                        setting_value TEXT)''')

    # 7. Stock Adjustments Log (manual quantity edits for product reports)
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_adjustments (
                        adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        product_name TEXT NOT NULL,
                        quantity_change INTEGER NOT NULL,
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(product_id) REFERENCES inventory(product_id) ON DELETE CASCADE)''')

    conn.commit()
    conn.close()
    print("All enterprise tables verified and locked successfully.")


# =================================================================
# ⚙️ SYSTEM CONFIGURATION / SHOP SETTINGS QUERY ENGINE
# =================================================================

DEFAULT_SETTINGS = {
    "shop_name": "Afzal Petrol Agency",
    "logo_path": "",
    "footer_note": "System generated invoice. Thank you for your business!",
    "printer_name": "",
    "printer_paper_size": "80mm"
}

def get_setting(key, default=""):
    """Single setting value fetch karo, agar nahi mila to default return karo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row is not None and row[0] is not None:
        return row[0]
    return DEFAULT_SETTINGS.get(key, default)

def get_all_settings():
    """Saari settings ek dictionary mein return karo (defaults ke saath merged)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM settings")
    rows = cursor.fetchall()
    conn.close()

    result = dict(DEFAULT_SETTINGS)
    for key, value in rows:
        if value is not None:
            result[key] = value
    return result

def set_setting(key, value):
    """Ek setting ko insert ya update karo (UPSERT)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
                          ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value""",
                       (key, str(value)))
        conn.commit()
        conn.close()
        return True, "Setting updated successfully."
    except Exception as e:
        return False, f"Settings Write Error: {str(e)}"

def set_settings_bulk(settings_dict):
    """Multiple settings ek transaction mein save karo."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for key, value in settings_dict.items():
            cursor.execute("""INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
                              ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value""",
                           (key, str(value)))
        conn.commit()
        conn.close()
        return True, "Configuration saved successfully."
    except Exception as e:
        return False, f"Settings Bulk Write Error: {str(e)}"


# =================================================================
# 👤 USER ACCOUNT MANAGEMENT (Username / Password Change)
# =================================================================

def update_username(old_username, new_username):
    """Username change karo (unique check ke saath)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        conn.commit()
        conn.close()
        return True, "Username updated successfully."
    except sqlite3.IntegrityError:
        return False, "This username is already taken!"
    except Exception as e:
        return False, f"Database Error: {str(e)}"

def update_user_password(username, old_password, new_password):
    """Current password verify karne ke baad naya password set karo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, old_password))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "Current password is incorrect!"

    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()
    return True, "Password changed successfully."

def get_dashboard_summary():
    """Dashboard ke liye summary stats: total revenue, total profit, total invoices, low stock count."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(net_amount), 0), COUNT(*) FROM invoices")
    total_revenue, total_invoices = cursor.fetchone()

    cursor.execute("SELECT COALESCE(SUM((sale_price - cost_price) * quantity), 0) FROM invoice_items")
    total_profit = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE quantity <= 5")
    low_stock_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory")
    total_products = cursor.fetchone()[0]

    conn.close()
    return {
        "total_revenue": total_revenue or 0.0,
        "total_profit": total_profit or 0.0,
        "total_invoices": total_invoices or 0,
        "low_stock_count": low_stock_count or 0,
        "total_products": total_products or 0
    }

def is_first_run():
    """Check if administrator table is vacant."""
    if not os.path.exists(DB_PATH):
        return True
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        row = cursor.fetchone()
        conn.close()
        if row is None or row[0] == 0:
            return True
        return False
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return True

def register_admin(username, password, question, answer):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO users (username, password, security_question, security_answer) 
                          VALUES (?, ?, ?, ?)""", (username, password, question, answer))
        conn.commit()
        conn.close()
        return True, "Administrator registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"

def verify_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return True, "Login Successful!"
    return False, "Invalid Username or Password!"

def reset_password(username, question, answer, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND security_question = ? AND security_answer = ?", 
                   (username, question, answer))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
        conn.commit()
        conn.close()
        return True, "Password Reset Successfully!"
    
    conn.close()
    return False, "Security details did not match!"


# =================================================================
# 📦 UPGRADED INVENTORY MODULE QUERY ENGINE (MODAL COMPATIBLE)
# =================================================================

def add_product(name, barcode, unit, qty, cost, sale):
    """Inserts a clean product entry with dynamic pricing matrix."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Handle optional barcode safely
        b_val = barcode.strip() if barcode and barcode.strip() else None
        
        cursor.execute("""INSERT INTO inventory (name, barcode, unit, quantity, cost_price, sale_price) 
                          VALUES (?, ?, ?, ?, ?, ?)""", (name, b_val, unit, int(qty), float(cost), float(sale)))
        conn.commit()
        conn.close()
        _sync_products_excel_safe()
        return True, "Product successfully registered in master ledger."
    except Exception as e:
        return False, f"Database Write Error: {str(e)}"

def get_all_products(search_query=""):
    """Fetches records using advanced wildcard matching for live filters."""
    conn = get_connection()
    cursor = conn.cursor()
    if search_query:
        cursor.execute("""SELECT * FROM inventory WHERE name LIKE ? OR barcode LIKE ?""", 
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM inventory")
    data = cursor.fetchall()
    conn.close()
    return data

def update_product(p_id, name, barcode, unit, qty, cost, sale):
    """Mutates existing asset specifications based on primary unique ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        b_val = barcode.strip() if barcode and barcode.strip() else None
        
        # Capture the old quantity first, to log any manual adjustment delta
        cursor.execute("SELECT quantity FROM inventory WHERE product_id=?", (int(p_id),))
        old_row = cursor.fetchone()
        old_qty = old_row[0] if old_row else None

        cursor.execute("""UPDATE inventory SET name=?, barcode=?, unit=?, quantity=?, cost_price=?, sale_price=? 
                          WHERE product_id=?""", (name, b_val, unit, int(qty), float(cost), float(sale), int(p_id)))

        # Log manual stock adjustment if quantity changed (for daily reports)
        if old_qty is not None and int(qty) != int(old_qty):
            delta = int(qty) - int(old_qty)
            cursor.execute("""INSERT INTO stock_adjustments (product_id, product_name, quantity_change, reason)
                              VALUES (?, ?, ?, ?)""", (int(p_id), name, delta, "Manual edit"))

        conn.commit()
        conn.close()
        _sync_products_excel_safe()
        return True, "Product data specifications updated successfully."
    except Exception as e:
        return False, f"Database Update Error: {str(e)}"

def delete_product(p_id):
    """Purges the structural target item record permanently from stock logs."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE product_id=?", (int(p_id),))
        conn.commit()
        conn.close()
        _sync_products_excel_safe()
        return True, "Product purged from database execution layer."
    except Exception as e:
        return False, f"Purge Execution Error: {str(e)}"

# --- BILLING ENGINE & INVOICE SYSTEMS ---

def create_invoice(customer_name, subtotal, tax_percent, total, payment_mode, cart_items):
    """Generates a unique invoice sequence and deducts stock inside a single secure database transaction."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        import datetime
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c_name = customer_name.strip() if customer_name.strip() else "Walk-in Customer"
        
        # 1. Insert Master Invoice Record
        cursor.execute("""INSERT INTO invoices (customer_name, total_amount, discount, net_amount, date, payment_mode) 
                          VALUES (?, ?, ?, ?, ?, ?)""", (c_name, float(subtotal), float(tax_percent), float(total), current_date, payment_mode))
        
        invoice_id = cursor.lastrowid # Unique Invoice Number
        
        # 2. Process Cart Items (Fixed Unpacking: Handled the 6 elements array structure)
        for item in cart_items:
            # item has 6 elements now: [p_id, name, qty, price, total_p, max_stock]
            p_id, item_name, item_qty, item_sale_price, item_total, _ = item
            
            # Fetch cost_price from inventory for profit tracking
            cursor.execute("SELECT cost_price FROM inventory WHERE product_id = ?", (int(p_id),))
            cost_row = cursor.fetchone()
            item_cost_price = cost_row[0] if cost_row else 0.0
            
            # Save item detail for profit analytics
            cursor.execute("""INSERT INTO invoice_items 
                              (invoice_id, product_id, product_name, quantity, cost_price, sale_price, line_total)
                              VALUES (?, ?, ?, ?, ?, ?, ?)""",
                           (invoice_id, int(p_id), item_name, int(item_qty),
                            float(item_cost_price), float(item_sale_price), float(item_total)))
            
            # Update real stock inventory status
            cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE product_id = ?", (int(item_qty), int(p_id)))
            
        conn.commit()
        conn.close()
        _sync_products_excel_safe()
        return True, invoice_id, current_date
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Transaction Halted: {str(e)}", None
# --- ADVANCED INVOICE HISTORY AUDIT QUERIES ---

def get_filtered_invoices(search_query="", start_date="", end_date=""):
    """Fetches invoices from the ledger matching search terms or structured date boundaries."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Base query logic block
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (invoice_id LIKE ? OR customer_name LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        
    if start_date and end_date:
        # SQLite text based date matching context logic standard (YYYY-MM-DD format expected)
        query += " AND date(date) BETWEEN date(?) AND date(?)"
        params.append(start_date)
        params.append(end_date)
        
    query += " ORDER BY invoice_id ASC"
    
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data

def get_invoice_profit(invoice_id):
    """Single invoice ka profit calculate karo: (sale_price - cost_price) * qty per item"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_name, quantity, cost_price, sale_price, line_total,
               (sale_price - cost_price) * quantity AS item_profit
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    items = cursor.fetchall()
    conn.close()
    return items  # list of (name, qty, cost, sale, line_total, item_profit)

def get_invoice_items_for_print(invoice_id):
    """
    Returns invoice line items in the [product_id, name, qty, sale_price, line_total, _]
    format expected by InvoicePrintWindow / PDF export.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, product_name, quantity, sale_price, line_total
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    rows = cursor.fetchall()
    conn.close()
    return [[r[0], r[1], r[2], r[3], r[4], None] for r in rows]

def get_invoices_with_profit(search_query="", start_date="", end_date=""):
    """Filtered invoices with total profit per invoice joined from invoice_items"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT i.invoice_id, i.customer_name, i.total_amount, i.discount, i.net_amount,
               i.date, i.payment_mode,
               COALESCE(SUM((ii.sale_price - ii.cost_price) * ii.quantity), NULL) AS profit
        FROM invoices i
        LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
        WHERE 1=1
    """
    params = []
    
    if search_query:
        query += " AND (i.invoice_id LIKE ? OR i.customer_name LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        
    if start_date and end_date:
        query += " AND date(i.date) BETWEEN date(?) AND date(?)"
        params.append(start_date)
        params.append(end_date)
        
    query += " GROUP BY i.invoice_id ORDER BY i.invoice_id ASC"
    
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data  # 8 columns: id, name, subtotal, tax%, net, date, mode, profit(or None)

# =================================================================
# 💎 ADVANCED WALLET & RUNNING LEDGER DATABASE ENGINE
# =================================================================

def CRITICAL_init_ledger_tables():
    """Run this to migrate/create the new advanced wallet tracking schema"""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()
    
    # 1. Advanced Customer Wallet Master Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger_customers (
            khata_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone_number TEXT UNIQUE, -- Optional. NULL allowed (multiple customers can have no phone); if provided, must be unique
            current_wallet_balance REAL DEFAULT 0.0, -- Positive means customer cash with us, Negative means credit/udhaar
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Daily Timeline Passbook Running Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger_transactions (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            khata_id INTEGER,
            action_type TEXT NOT NULL, -- 'ADVANCE_DEPOSIT', 'PURCHASE_DEBIT', 'CASH_WITHDRAWAL', 'OVERDRAFT_CREDIT'
            amount REAL NOT NULL,
            closing_balance REAL NOT NULL, -- Dynamic running statement trace
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(khata_id) REFERENCES ledger_customers(khata_id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    # --- Migration: older databases may have phone_number as NOT NULL UNIQUE,
    # which blocks customers without a phone number. Rebuild the table if so.
    cursor.execute("PRAGMA table_info(ledger_customers)")
    columns = cursor.fetchall()
    phone_col = next((c for c in columns if c[1] == "phone_number"), None)
    if phone_col and phone_col[3] == 1:  # notnull flag == 1 means old schema
        cursor.execute("""
            CREATE TABLE ledger_customers_new (
                khata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone_number TEXT UNIQUE,
                current_wallet_balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO ledger_customers_new (khata_id, customer_name, phone_number, current_wallet_balance, created_at)
            SELECT khata_id, customer_name, phone_number, current_wallet_balance, created_at FROM ledger_customers
        """)
        cursor.execute("DROP TABLE ledger_customers")
        cursor.execute("ALTER TABLE ledger_customers_new RENAME TO ledger_customers")
        conn.commit()

    conn.close()

def _normalize_khata_search(search_query):
    """If the query looks like a Khata Number (e.g. 'KH-0004', 'kh0004', '#4'),
    extract the numeric ID so it can also match khata_id directly."""
    import re
    q = search_query.strip()
    m = re.match(r'^\s*(?:kh|#)?[-\s#]*0*(\d+)\s*$', q, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def get_ledger_customers(search_query="", page=1, page_size=10):
    """Paginated khata directory. page=1-indexed. Returns list of (khata_id, name, phone, balance).
    Search matches customer name, phone number, or Khata Number (e.g. '4', 'KH-0004', 'kh4')."""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()
    offset = max(page - 1, 0) * page_size
    if search_query:
        khata_num = _normalize_khata_search(search_query)
        like_term = f"%{search_query}%"
        khata_term = khata_num if khata_num is not None else search_query
        cursor.execute("""
            SELECT khata_id, customer_name, phone_number, current_wallet_balance 
            FROM ledger_customers 
            WHERE customer_name LIKE ? OR phone_number LIKE ?
               OR CAST(khata_id AS TEXT) LIKE ?
               OR CAST(khata_id AS TEXT) = ?
            ORDER BY khata_id ASC
            LIMIT ? OFFSET ?
        """, (like_term, like_term, like_term, khata_term, page_size, offset))
    else:
        cursor.execute("""
            SELECT khata_id, customer_name, phone_number, current_wallet_balance 
            FROM ledger_customers ORDER BY khata_id ASC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
    res = cursor.fetchall()
    conn.close()
    return res

def get_ledger_customers_count(search_query=""):
    """Total number of khata customers matching the search (for pagination)."""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()
    if search_query:
        khata_num = _normalize_khata_search(search_query)
        like_term = f"%{search_query}%"
        khata_term = khata_num if khata_num is not None else search_query
        cursor.execute("""
            SELECT COUNT(*) FROM ledger_customers 
            WHERE customer_name LIKE ? OR phone_number LIKE ?
               OR CAST(khata_id AS TEXT) LIKE ?
               OR CAST(khata_id AS TEXT) = ?
        """, (like_term, like_term, like_term, khata_term))
    else:
        cursor.execute("SELECT COUNT(*) FROM ledger_customers")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def add_ledger_customer(name, phone, opening_balance=0.0):
    import sqlite3
    try:
        phone_val = phone.strip() if phone and phone.strip() else None
        conn = sqlite3.connect("database/pos_system.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ledger_customers (customer_name, phone_number, current_wallet_balance) VALUES (?, ?, ?)",
            (name, phone_val, float(opening_balance))
        )
        conn.commit()
        conn.close()
        _sync_khata_excel_safe()
        return True, "Account Opened Successfully"
    except sqlite3.IntegrityError:
        return False, "This Phone Number is already tied to another unique Khata ID!"
    except Exception as e:
        return False, str(e)

def update_ledger_customer(khata_id, name, phone):
    """Updates only the customer name and phone number for a khata account."""
    import sqlite3
    try:
        phone_val = phone.strip() if phone and phone.strip() else None
        conn = sqlite3.connect("database/pos_system.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ledger_customers SET customer_name=?, phone_number=? WHERE khata_id=?",
            (name, phone_val, int(khata_id))
        )
        conn.commit()
        conn.close()
        _sync_khata_excel_safe()
        return True, "Account details updated successfully."
    except sqlite3.IntegrityError:
        return False, "This Phone Number is already tied to another unique Khata ID!"
    except Exception as e:
        return False, str(e)

def delete_ledger_customer(khata_id):
    """Deletes a khata account and its transaction history."""
    import sqlite3
    try:
        conn = sqlite3.connect("database/pos_system.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ledger_transactions WHERE khata_id=?", (int(khata_id),))
        cursor.execute("DELETE FROM ledger_customers WHERE khata_id=?", (int(khata_id),))
        conn.commit()
        conn.close()
        _sync_khata_excel_safe()
        return True, "Account deleted successfully."
    except Exception as e:
        return False, str(e)

def process_wallet_transaction(khata_id, action_type, amount, desc):
    """Core Mathematical Matrix Engine for Running Balances"""
    import sqlite3
    try:
        conn = sqlite3.connect("database/pos_system.db")
        cursor = conn.cursor()
        
        # 1. Fetch current wallet standing balance node
        cursor.execute("SELECT current_wallet_balance FROM ledger_customers WHERE khata_id = ?", (khata_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Customer Profile Missing"
        
        old_balance = row[0]
        
        # 2. Parse Actions to update cash positioning balances
        if action_type in ['ADVANCE_DEPOSIT']:
            new_balance = old_balance + amount
        elif action_type in ['PURCHASE_DEBIT', 'CASH_WITHDRAWAL']:
            new_balance = old_balance - amount
            # System dynamically tags overdraft if account balance slides below zero
            if new_balance < 0 and old_balance >= 0:
                action_type = 'OVERDRAFT_CREDIT'
        else:
            new_balance = old_balance - amount
            
        # 3. Post into Timeline Log History
        cursor.execute("""
            INSERT INTO ledger_transactions (khata_id, action_type, amount, closing_balance, description)
            VALUES (?, ?, ?, ?, ?)
        """, (khata_id, action_type, amount, new_balance, desc))
        
        # 4. Sync State back inside master account profile node
        cursor.execute("UPDATE ledger_customers SET current_wallet_balance = ? WHERE khata_id = ?", (new_balance, khata_id))
        
        conn.commit()
        conn.close()
        _sync_khata_excel_safe()
        return True, "Balance System Committed"
    except Exception as e:
        return False, str(e)

def get_customer_passbook(khata_id, start_date="", end_date="", page=1, page_size=25):
    """Passbook timeline, optionally filtered by a date range (YYYY-MM-DD format, inclusive).
    Paginated (page=1-indexed) so very active accounts don't render thousands of rows at once."""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()

    query = """
        SELECT timestamp, action_type, description, amount, closing_balance 
        FROM ledger_transactions 
        WHERE khata_id = ?
    """
    params = [khata_id]

    if start_date and end_date:
        query += " AND date(timestamp) BETWEEN date(?) AND date(?)"
        params.append(start_date)
        params.append(end_date)

    query += " ORDER BY log_id DESC LIMIT ? OFFSET ?"
    offset = max(page - 1, 0) * page_size
    params.append(page_size)
    params.append(offset)

    cursor.execute(query, params)
    res = cursor.fetchall()
    conn.close()
    return res


def get_customer_passbook_count(khata_id, start_date="", end_date=""):
    """Total number of passbook entries for a customer matching the optional date range (for pagination)."""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM ledger_transactions WHERE khata_id = ?"
    params = [khata_id]

    if start_date and end_date:
        query += " AND date(timestamp) BETWEEN date(?) AND date(?)"
        params.append(start_date)
        params.append(end_date)

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()
    return total

def import_ledger_customers_bulk(rows):
    """
    Bulk import khata customers from a spreadsheet.
    rows: list of (name, phone, opening_balance) tuples.
    Skips duplicate phone numbers (already existing). Opening balance becomes the
    starting wallet balance plus an ADVANCE_DEPOSIT/initial log entry if non-zero.
    Returns (success_count, skipped_count, errors list).
    """
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()

    success_count = 0
    skipped_count = 0
    errors = []

    for row in rows:
        try:
            name, phone, opening_balance = row
            name = str(name).strip()
            phone = str(phone).strip() if phone is not None else ""

            if not name:
                skipped_count += 1
                continue

            # Phone is optional. Normalize blank phone to NULL so multiple
            # customers without a phone number don't collide on the UNIQUE constraint.
            phone_value = phone if phone else None

            try:
                opening_balance = float(opening_balance)
            except (ValueError, TypeError):
                opening_balance = 0.0

            if phone_value is not None:
                cursor.execute("SELECT khata_id FROM ledger_customers WHERE phone_number = ?", (phone_value,))
                existing = cursor.fetchone()
                if existing:
                    skipped_count += 1
                    continue

            cursor.execute(
                "INSERT INTO ledger_customers (customer_name, phone_number, current_wallet_balance) VALUES (?, ?, ?)",
                (name, phone_value, opening_balance)
            )
            khata_id = cursor.lastrowid

            if opening_balance != 0:
                action_type = "ADVANCE_DEPOSIT" if opening_balance > 0 else "OVERDRAFT_CREDIT"
                cursor.execute("""
                    INSERT INTO ledger_transactions (khata_id, action_type, amount, closing_balance, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (khata_id, action_type, abs(opening_balance), opening_balance, "Imported Opening Balance"))

            success_count += 1
        except Exception as e:
            skipped_count += 1
            errors.append(str(e))

    conn.commit()
    conn.close()
    _sync_khata_excel_safe()
    return success_count, skipped_count, errors

def get_all_ledger_customers_full():
    """Export ke liye sab customers list"""
    import sqlite3
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT khata_id, customer_name, phone_number, current_wallet_balance, created_at FROM ledger_customers ORDER BY khata_id ASC")
    res = cursor.fetchall()
    conn.close()
    return res

def get_customer_linked_invoices(customer_name):
    """Kisi customer ke sirf WALLET invoices (POS se linked) billing_system.db se"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.invoice_id, i.customer_name, i.total_amount, i.discount, i.net_amount, i.date, i.payment_mode,
               COALESCE(SUM((ii.sale_price - ii.cost_price) * ii.quantity), NULL) AS profit
        FROM invoices i
        LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
        WHERE i.customer_name = ? AND i.payment_mode = 'WALLET'
        GROUP BY i.invoice_id
        ORDER BY i.invoice_id ASC
    """, (customer_name,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_daily_cashflow_summary():
    import sqlite3
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect("database/pos_system.db")
    cursor = conn.cursor()
    
    # Calculate today's total deposits
    cursor.execute("SELECT SUM(amount) FROM ledger_transactions WHERE action_type='ADVANCE_DEPOSIT' AND timestamp LIKE ?", (f"{today}%",))
    total_in = cursor.fetchone()[0] or 0.0
    
    # Calculate today's total cash withdrawals
    cursor.execute("SELECT SUM(amount) FROM ledger_transactions WHERE action_type='CASH_WITHDRAWAL' AND timestamp LIKE ?", (f"{today}%",))
    total_out = cursor.fetchone()[0] or 0.0
    
    conn.close()
    return total_in, total_out

# Automatic operational execution schema block
init_db()