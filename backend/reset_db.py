#!/usr/bin/env python
"""
Script to reset database and migrations for NeuroData project.
"""
import os
import sys
import sqlite3
from pathlib import Path

def reset_database():
    """Reset the SQLite database and migration files."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Database file path
    db_path = project_root / "db.sqlite3"
    
    # Remove database file if it exists
    if db_path.exists():
        print(f"Removing database file: {db_path}")
        db_path.unlink()
    
    # Remove migration files from all apps
    apps_to_reset = ['apps/authentication', 'apps/datasets']
    
    for app_path in apps_to_reset:
        migrations_dir = project_root / app_path / "migrations"
        if migrations_dir.exists():
            print(f"Cleaning migrations in {app_path}")
            
            # Keep __init__.py but remove other migration files
            for migration_file in migrations_dir.glob("*.py"):
                if migration_file.name != "__init__.py":
                    print(f"  Removing {migration_file.name}")
                    migration_file.unlink()
            
            # Remove __pycache__ directory
            pycache_dir = migrations_dir / "__pycache__"
            if pycache_dir.exists():
                import shutil
                shutil.rmtree(pycache_dir)
    
    print("\nDatabase and migrations reset complete!")
    print("Next steps:")
    print("1. Run: python manage.py makemigrations")
    print("2. Run: python manage.py migrate")
    print("3. Run: python manage.py createsuperuser")

if __name__ == "__main__":
    reset_database()
