import sqlite3

# Connect to your database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

print("--- Admin Password Recovery ---")
old_email = input("Enter your OLD admin email (the one you are locked out of): ")
new_email = input("Enter your NEW admin email (the one you just created): ")

# Fetch the working password hash from the new account
cursor.execute("SELECT password FROM admins WHERE email = ?", (new_email,))
result = cursor.fetchone()

if result:
    new_password_hash = result[0]
    
    # Overwrite the old account's password with the working one
    cursor.execute("UPDATE admins SET password = ? WHERE email = ?", (new_password_hash, old_email))
    conn.commit()
    print(f"\n✅ SUCCESS! The password for '{old_email}' has been reset.")
    print("You can now log in using your old email and your new password.")
else:
    print(f"\n❌ ERROR: Could not find an admin with the email '{new_email}'.")

conn.close()