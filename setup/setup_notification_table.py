# Setup notification tracking table
import psycopg2
import sys
from config import Config

def setup_notification_table():
    """Create notification tracking table in the database"""
    print("Setting up notification tracking table...")
    
    try:
        # Get database configuration from Config class
        db_config = {
            'dbname': 'civicsightai',
            'user': 'postgres',
            'password': 'Radhakisan',
            'host': 'localhost',
            'port': 5432
        }
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Create notifications tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                complaint_id UUID,
                notification_type VARCHAR(20) NOT NULL,
                recipient VARCHAR(100) NOT NULL,
                message_id VARCHAR(100),
                status VARCHAR(20) DEFAULT 'sent',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS notification_complaint_idx 
            ON notification_logs(complaint_id)
        ''')
        
        conn.commit()
        print("Notification tracking table created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up notification table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_notification_table()
    sys.exit(0 if success else 1)
