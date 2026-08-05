import sqlite3

def setup_prediction_table():
    # Connect to your existing database file
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    print("Checking database...")

    # Create the table required for the "Self-Thinking" logic
    # This stores the input, the prediction, and the final corrected answer
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_skills TEXT,
            predicted_career TEXT,
            actual_career TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Success! 'prediction_history' table is now ready.")

if __name__ == "__main__":
    setup_prediction_table()