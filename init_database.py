import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ✅ USERS TABLE (Added last_login for Dashboard metrics)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    status TEXT DEFAULT 'active',
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ✅ ADMINS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'admin'
)
""")

# ✅ ATS TABLE (Added user_id to link scans to specific users)
cursor.execute("""
CREATE TABLE IF NOT EXISTS ats_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, 
    filename TEXT,
    score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# ✅ PREDICTIONS TABLE (Linked via user_id instead of just email)
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# ✅ RESET TOKENS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------------------------------------------------
# ✅ DATABASE UPDATES (Column maintenance)
# ---------------------------------------------------------

# Adding status if missing
try:
    cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
except sqlite3.OperationalError:
    pass

# IMPORTANT: Adding last_login to make "Active Today" work!
try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError:
    pass

# Adding user_id to logs for relationship mapping
try:
    cursor.execute("ALTER TABLE ats_logs ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE predictions ADD COLUMN user_id INTEGER")
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()

print("Database initialized with relationships and activity tracking ✅")