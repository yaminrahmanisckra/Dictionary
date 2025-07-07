#!/usr/bin/env python3

from app import app, db, User
from sqlalchemy import text

with app.app_context():
    print("Testing database connection...")
    
    # Check if we can connect to the database
    try:
        db.session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        exit(1)
    
    # Check user table schema
    try:
        result = db.session.execute(text("PRAGMA table_info(user)"))
        columns = [row[1] for row in result]
        print(f"✓ User table columns: {columns}")
        
        if 'email' in columns:
            print("✓ Email column exists in user table")
        else:
            print("✗ Email column missing from user table")
    except Exception as e:
        print(f"✗ Error checking user table schema: {e}")
    
    # Try to load a user using SQLAlchemy 2.0 style
    try:
        user = db.session.get(User, 2)
        if user:
            print(f"✓ Successfully loaded user: {user.username} (email: {user.email})")
        else:
            print("✗ User with ID 2 not found")
    except Exception as e:
        print(f"✗ Error loading user: {e}")
    
    # Check all users
    try:
        users = User.query.all()
        print(f"✓ Found {len(users)} users in database")
        for user in users:
            print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    except Exception as e:
        print(f"✗ Error querying all users: {e}")

print("Test completed.") 