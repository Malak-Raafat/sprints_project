import sqlite3
import os
from datetime import datetime

DB_PATH = "data.db"

def init_db():
    """Initialize the database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User authentication table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Agent operations logging
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        data TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Research proposals storage
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        keywords TEXT NOT NULL,
        proposal_text TEXT NOT NULL,
        rating INTEGER,
        feedback TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # Chat message history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_user BOOLEAN NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # Agent communication bus
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message_type TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT 0
    )
    """)
    
    # Research papers cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        published TEXT NOT NULL,
        link TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dictionary-style access
    return conn

def log_agent_action(agent_name: str, action_type: str, data: dict):
    """Log agent activities to database"""
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO agent_logs (agent_name, action_type, data) VALUES (?, ?, ?)",
            (agent_name, action_type, json.dumps(data))
        )
        conn.commit()
    finally:
        conn.close()

def get_user_id(username: str) -> int:
    """Get user ID from username"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        return result['id'] if result else None
    finally:
        conn.close()
def migrate_existing_data():
    """Migration function for existing users"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in columns:
            # First add the column without default value
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
            
            # Then update existing rows with current timestamp
            cursor.execute("UPDATE users SET created_at = datetime('now')")
            
            # Finally modify the table to add the default for future inserts
            # Note: SQLite doesn't support modifying column defaults directly,
            # so we'll need to recreate the table
            cursor.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO users_new (id, username, password, created_at)
                SELECT id, username, password, created_at FROM users
            """)
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            
        conn.commit()
    finally:
        conn.close()

# Initialize database and run migrations when module loads
if not os.path.exists(DB_PATH):
    init_db()
else:
    migrate_existing_data()