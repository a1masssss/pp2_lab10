#!/usr/bin/env python3

import psycopg2
import psycopg2.extras
import sys
import pandas as pd
import re
sys.path.append("..")
from config import DB_CONFIG

class AdvancedPhoneBook:
    def __init__(self):
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Connect to the PostgreSQL database server"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print("Connected to the database")
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to the database: {error}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.cur is not None:
            self.cur.close()
        if self.conn is not None:
            self.conn.close()
            print("Database connection closed.")
            
    def search_by_pattern(self, pattern):
        """Search contacts based on a pattern using the database function"""
        try:
            self.cur.callproc('search_contacts_by_pattern', [pattern])
            rows = self.cur.fetchall()
            return rows
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error searching contacts: {error}")
            return []
            
    def upsert_contact(self, first_name, last_name, phone, email=None):
        """Insert a new contact or update if exists using the stored procedure"""
        try:
            # Call the stored procedure
            self.cur.execute(
                "CALL upsert_contact(%s, %s, %s, %s)",
                (first_name, last_name, phone, email)
            )
            self.conn.commit()
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error upserting contact: {error}")
            return False
            
    def is_valid_phone(self, phone):
        """Validate phone number format using regex"""
        # Phone should start with optional + and have 10-15 digits
        pattern = r'^\+?[0-9]{10,15}$'
        return bool(re.match(pattern, phone))
            
    def insert_multiple_contacts(self, contact_list):
        """Insert multiple contacts with validation
        
        Args:
            contact_list: List of tuples (first_name, last_name, phone, email)
        
        Returns:
            List of dictionaries with results
        """
        # Extract data into separate lists
        first_names = []
        last_names = []
        phones = []
        emails = []
        
        for contact in contact_list:
            first_name, last_name, phone = contact[0], contact[1], contact[2]
            email = contact[3] if len(contact) > 3 else None
            
            first_names.append(first_name)
            last_names.append(last_name)
            phones.append(phone)
            if email:
                emails.append(email)
                
        results = []
        
        # Validate locally first
        validation_results = []
        for i, phone in enumerate(phones):
            result = {
                'first_name': first_names[i],
                'last_name': last_names[i],
                'phone': phone
            }
            
            if not self.is_valid_phone(phone):
                result['status'] = 'Invalid phone number'
                validation_results.append(result)
                
        if validation_results:
            print("Found invalid phone numbers:")
            for result in validation_results:
                print(f"  {result['first_name']} {result['last_name']}: {result['phone']} - {result['status']}")
            return validation_results
            
        # All phones are valid, proceed with database insertion
        try:
            # Use batch processing
            for i in range(len(first_names)):
                first_name, last_name, phone = first_names[i], last_names[i], phones[i]
                email = emails[i] if i < len(emails) else None
                
                # Check if contact exists
                self.cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM contacts WHERE first_name = %s AND last_name = %s)",
                    (first_name, last_name)
                )
                exists = self.cur.fetchone()[0]
                
                if exists:
                    # Update
                    self.cur.execute(
                        "UPDATE contacts SET phone = %s, email = COALESCE(%s, email) WHERE first_name = %s AND last_name = %s",
                        (phone, email, first_name, last_name)
                    )
                    status = "Updated"
                else:
                    # Insert
                    self.cur.execute(
                        "INSERT INTO contacts (first_name, last_name, phone, email) VALUES (%s, %s, %s, %s)",
                        (first_name, last_name, phone, email)
                    )
                    status = "Inserted"
                    
                results.append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'status': status
                })
                
            self.conn.commit()
            return results
            
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error inserting multiple contacts: {error}")
            return []
            
    def get_contacts_paginated(self, limit=10, offset=0):
        """Get contacts with pagination using the database function"""
        try:
            self.cur.callproc('get_contacts_paginated', [limit, offset])
            rows = self.cur.fetchall()
            return rows
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error getting paginated contacts: {error}")
            return []
            
    def delete_contact_by_identifier(self, identifier):
        """Delete contact by username or phone using the stored procedure"""
        try:
            self.cur.execute("CALL delete_contact_by_identifier(%s)", (identifier,))
            self.conn.commit()
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error deleting contact: {error}")
            return False
            
    def print_contacts(self, contacts):
        """Pretty print contacts list"""
        if not contacts:
            print("No contacts found.")
            return
            
        print("\nContact List:")
        print("{:<5} {:<15} {:<15} {:<20} {:<30} {:<20}".format(
            "ID", "First Name", "Last Name", "Phone", "Email", "Created At"))
        print("-" * 100)
        
        for contact in contacts:
            print("{:<5} {:<15} {:<15} {:<20} {:<30} {:<20}".format(
                contact['id'], 
                contact['first_name'], 
                contact['last_name'], 
                contact['phone'], 
                contact['email'] or '', 
                contact['created_at'].strftime('%Y-%m-%d %H:%M:%S') if contact['created_at'] else ''))

def main():
    phonebook = AdvancedPhoneBook()
    if not phonebook.connect():
        return
    
    while True:
        print("\nAdvanced PhoneBook Application")
        print("1. Search contacts by pattern")
        print("2. Add or update a contact")
        print("3. Add multiple contacts")
        print("4. List contacts (paginated)")
        print("5. Delete contact by identifier")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ")
        
        if choice == '1':
            pattern = input("Enter search pattern (part of name, phone, etc.): ")
            contacts = phonebook.search_by_pattern(pattern)
            phonebook.print_contacts(contacts)
            
        elif choice == '2':
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            phone = input("Enter phone number: ")
            email = input("Enter email (optional, press Enter to skip): ") or None
            
            if phonebook.is_valid_phone(phone):
                result = phonebook.upsert_contact(first_name, last_name, phone, email)
                if result:
                    print("Contact added or updated successfully!")
            else:
                print("Invalid phone number format! Please use format: +XXXXXXXXXXX (10-15 digits).")
                
        elif choice == '3':
            try:
                contact_list = []
                count = int(input("How many contacts do you want to add? "))
                
                print("Enter contact details (first name, last name, phone, email):")
                for i in range(count):
                    print(f"\nContact {i+1}:")
                    first_name = input("First name: ")
                    last_name = input("Last name: ")
                    phone = input("Phone: ")
                    email = input("Email (optional): ") or None
                    
                    contact_list.append((first_name, last_name, phone, email))
                
                results = phonebook.insert_multiple_contacts(contact_list)
                
                print("\nResults:")
                for result in results:
                    print(f"{result['first_name']} {result['last_name']}: {result['status']}")
                    
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                
        elif choice == '4':
            try:
                limit = int(input("Enter number of records per page (default 10): ") or 10)
                page = int(input("Enter page number (starting from 1): ") or 1)
                
                offset = (page - 1) * limit
                contacts = phonebook.get_contacts_paginated(limit, offset)
                
                phonebook.print_contacts(contacts)
                print(f"\nShowing page {page} with {limit} records per page.")
                
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
                
        elif choice == '5':
            identifier = input("Enter first name or phone number to delete: ")
            if phonebook.delete_contact_by_identifier(identifier):
                print(f"Contacts with identifier '{identifier}' deleted.")
                
        elif choice == '0':
            break
            
        else:
            print("Invalid choice. Please try again.")
    
    phonebook.disconnect()

if __name__ == "__main__":
    main() 