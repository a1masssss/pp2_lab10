#!/usr/bin/env python3

import psycopg2
import sys
sys.path.append("..")
from config import DB_CONFIG

def create_tables():
    """Create tables in PostgreSQL database for Snake Game"""
    commands = (
        """
        DROP TABLE IF EXISTS user_score CASCADE
        """,
        """
        DROP TABLE IF EXISTS users CASCADE
        """,
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE user_score (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            score INTEGER NOT NULL,
            snake_x_positions TEXT,
            snake_y_positions TEXT,
            food_x INTEGER,
            food_y INTEGER,
            direction VARCHAR(10),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users (id)
                ON UPDATE CASCADE ON DELETE CASCADE
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
        print("Snake Game tables created successfully")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_tables() 