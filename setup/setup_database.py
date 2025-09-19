#!/usr/bin/env python3
"""
Setup script for CivicSightAI PostgreSQL/PostGIS database
Run this script to set up your PostgreSQL database with PostGIS extension
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from config import config

def create_database():
    """Create the civicsightai database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        db_config = config['default'].DATABASE_CONFIG.copy()
        db_name = db_config.pop('dbname')  # Remove database name for initial connection
        
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def setup_postgis():
    """Set up PostGIS extension in the database"""
    try:
        conn = psycopg2.connect(**config['default'].DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Create PostGIS extension
        print("Setting up PostGIS extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        
        # Verify PostGIS installation
        cursor.execute("SELECT PostGIS_Version()")
        version = cursor.fetchone()[0]
        print(f"PostGIS version: {version}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("PostGIS extension set up successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up PostGIS: {e}")
        return False

def create_tables():
    """Create the complaints table with spatial support"""
    try:
        conn = psycopg2.connect(**config['default'].DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("Creating complaints table...")
        
        # Create complaints table with PostGIS geometry column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id VARCHAR(8) PRIMARY KEY,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                location_text TEXT NOT NULL,
                location GEOMETRY(POINT, 4326),
                photo_path TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detection_info JSONB
            )
        ''')
        
        # Create spatial index for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_complaints_location 
            ON complaints USING GIST(location)
        ''')
        
        # Create additional useful indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_complaints_category 
            ON complaints (category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_complaints_status 
            ON complaints (status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_complaints_created_at 
            ON complaints (created_at)
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Complaints table created successfully with spatial indexes!")
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def verify_setup():
    """Verify that the database setup is working correctly"""
    try:
        conn = psycopg2.connect(**config['default'].DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Test spatial functions
        print("Testing PostGIS functionality...")
        cursor.execute("SELECT ST_SetSRID(ST_MakePoint(-74.5, 40.0), 4326)")
        result = cursor.fetchone()
        print("✓ PostGIS spatial functions working")
        
        # Test table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'complaints'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("✓ Complaints table structure:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        # Test indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'complaints'
        """)
        
        indexes = cursor.fetchall()
        print("✓ Database indexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database setup verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    print("=" * 60)
    print("CivicSightAI PostgreSQL/PostGIS Database Setup")
    print("=" * 60)
    
    # Check configuration
    db_config = config['default'].DATABASE_CONFIG
    print(f"Database: {db_config['dbname']}")
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print(f"User: {db_config['user']}")
    print()
    
    # Confirm before proceeding
    confirm = input("Proceed with database setup? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("Setup cancelled.")
        sys.exit(0)
    
    print("\n" + "=" * 60)
    
    # Step 1: Create database
    print("STEP 1: Creating database...")
    if not create_database():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    
    # Step 2: Set up PostGIS
    print("STEP 2: Setting up PostGIS extension...")
    if not setup_postgis():
        print("❌ Failed to set up PostGIS. Exiting.")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    
    # Step 3: Create tables
    print("STEP 3: Creating tables...")
    if not create_tables():
        print("❌ Failed to create tables. Exiting.")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    
    # Step 4: Verify setup
    print("STEP 4: Verifying setup...")
    if not verify_setup():
        print("❌ Setup verification failed.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Database setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update the DATABASE_CONFIG password in config.py")
    print("2. Run the Flask application: python app.py")
    print("3. If you have existing SQLite data, run: python migrate_to_postgres.py")
    print("4. Get a Mapbox token and update templates/heatmap.html")
    print()

if __name__ == "__main__":
    main()
