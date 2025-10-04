#!/usr/bin/env python
"""
Script to fix migration dependency issues.
"""
import sqlite3
from datetime import datetime

def fix_migrations():
    """Fix the migration dependency issue."""
    try:
        # Connect to the database
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Check if the authentication migration is already there
        cursor.execute(
            "SELECT COUNT(*) FROM django_migrations WHERE app = 'authentication' AND name = '0001_initial'"
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert the authentication migration as applied
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
                ('authentication', '0001_initial', datetime.now())
            )
            conn.commit()
            print("✅ Authentication migration marked as applied")
        else:
            print("ℹ️  Authentication migration already exists")
        
        # Close connection
        conn.close()
        
        print("Migration fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing migrations: {str(e)}")

if __name__ == "__main__":
    fix_migrations()
