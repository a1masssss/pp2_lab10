#!/usr/bin/env python3

import pandas as pd
import psycopg2
import psycopg2.extras
import sys
sys.path.append("..")
from config import DB_CONFIG

def import_from_csv(file_path):
    """Import contacts from CSV using stored procedures"""
    conn = None
    try:
        # Read the CSV file
        print(f"Reading contacts from {file_path}...")
        df = pd.read_csv(file_path)
        print(f"Found {len(df)} contacts in CSV file.")
        
        # Connect to the database
        print("Connecting to the database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Validate phone numbers
        print("Validating phone numbers...")
        invalid_records = []
        valid_records = []
        
        for index, row in df.iterrows():
            first_name = row['first_name']
            last_name = row['last_name']
            phone = row['phone']
            email = row['email'] if 'email' in row and pd.notna(row['email']) else None
            
            # Check if phone number is valid using the database function
            cur.execute("SELECT is_valid_phone(%s) AS is_valid", (phone,))
            is_valid = cur.fetchone()['is_valid']
            
            if is_valid:
                valid_records.append((first_name, last_name, phone, email))
            else:
                invalid_records.append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'email': email,
                    'reason': 'Invalid phone number format'
                })
        
        # Print invalid records
        if invalid_records:
            print("\nInvalid Records:")
            print("{:<15} {:<15} {:<20} {:<30} {:<30}".format(
                "First Name", "Last Name", "Phone", "Email", "Reason"))
            print("-" * 110)
            
            for record in invalid_records:
                print("{:<15} {:<15} {:<20} {:<30} {:<30}".format(
                    record['first_name'], 
                    record['last_name'], 
                    record['phone'], 
                    record['email'] or '', 
                    record['reason']))
        
        # Insert valid records
        if valid_records:
            print(f"\nInserting {len(valid_records)} valid contacts...")
            
            for record in valid_records:
                first_name, last_name, phone, email = record
                
                cur.execute(
                    "CALL upsert_contact(%s, %s, %s, %s)",
                    (first_name, last_name, phone, email)
                )
                
            conn.commit()
            print("Contacts imported successfully!")
        else:
            print("No valid contacts to import.")
        
        # Summary
        print("\nImport Summary:")
        print(f"Total records: {len(df)}")
        print(f"Valid records: {len(valid_records)}")
        print(f"Invalid records: {len(invalid_records)}")
        
    except Exception as error:
        print(f"Error: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            if cur:
                cur.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "data/contacts_batch.csv"
        
    import_from_csv(file_path) 