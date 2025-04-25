#!/usr/bin/env python3

import psycopg2
import sys
sys.path.append("..")
from config import DB_CONFIG

def setup_db_functions():
    """Set up database functions and procedures"""
    conn = None
    try:
        # Connect to the PostgreSQL database
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Read SQL file content
        print("Reading SQL functions and procedures...")
        with open('db_functions.sql', 'r') as sql_file:
            sql_script = sql_file.read()
        
        # Execute SQL script
        print("Executing SQL functions and procedures...")
        cur.execute(sql_script)
        
        # Close cursor
        cur.close()
        
        # Commit the transaction
        conn.commit()
        
        print("Database functions and procedures set up successfully!")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    setup_db_functions() 