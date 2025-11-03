#!/usr/bin/env python3
"""
Initialize database tables for CivicSightAI
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=Config.DATABASE_CONFIG['host'],
            database=Config.DATABASE_CONFIG['dbname'],
            user=Config.DATABASE_CONFIG['user'],
            password=Config.DATABASE_CONFIG['password'],
            port=Config.DATABASE_CONFIG['port']
        )
        
        cursor = conn.cursor()
        
        print("Creating complaints table...")
        # Create complaints table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id VARCHAR(255) PRIMARY KEY,
                description TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'pothole',
                location TEXT,
                longitude DECIMAL(10, 8),
                latitude DECIMAL(10, 8),
                photo_path VARCHAR(500),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                citizen_name VARCHAR(255),
                citizen_phone VARCHAR(20),
                citizen_email VARCHAR(255)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    init_database()