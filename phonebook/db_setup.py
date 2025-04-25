#!/usr/bin/env python3

import psycopg2
import sys
sys.path.append("..")
from config import DB_CONFIG

def create_tables():
    """Create tables in PostgreSQL database"""
    commands = (
        """
        DROP TABLE IF EXISTS contacts CASCADE
        """,
        """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50),
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Create tables
        for command in commands:
            cur.execute(command)
        
        # Close communication with the PostgreSQL database
        cur.close()
        
        # Commit the changes
        conn.commit()
        print("Tables created successfully")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables() 