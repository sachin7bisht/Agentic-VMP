-- ==========================================
-- File: data/sql/schema.sql
-- ==========================================
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Table: vendors
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id_str TEXT UNIQUE,           -- Matches 'vendor_id' in CSV (e.g., V7755)
    name TEXT NOT NULL,                  -- Matches 'company' in CSV (e.g., Brown Inc)
    contact_name TEXT,                   -- Matches 'name' in CSV (e.g., Aaron Roberts)
    email TEXT NOT NULL UNIQUE,          -- Matches 'email'
    phone TEXT,                          -- Matches 'phone'
    address TEXT,                        -- Matches 'address'
    category TEXT DEFAULT 'General',     -- Matches 'role' or generic
    status TEXT DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- Table: invoices
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,          -- FK to vendors.id (internal int ID)
    invoice_number TEXT NOT NULL UNIQUE, -- Matches 'invoice_id' (e.g., INV-1638)
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'Pending',       -- Matches 'status'
    issue_date DATE,                     -- Matches 'invoice_date'
    due_date DATE,                       -- Matches 'due_date'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- Table: conversation_history
-- Purpose: Active session memory (not the RAG archive)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_vendors_email ON vendors(email);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_vendors_str_id ON vendors(vendor_id_str);