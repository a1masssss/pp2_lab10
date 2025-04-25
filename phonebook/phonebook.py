#!/usr/bin/env python3

import psycopg2
import sys
import pandas as pd
sys.path.append("..")
from config import DB_CONFIG

class PhoneBook:
    def __init__(self):
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Connect to the PostgreSQL database server"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
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

    def insert_contact(self, first_name, last_name, phone, email=None):
        """Insert a new contact into the contacts table"""
        sql = """
        INSERT INTO contacts(first_name, last_name, phone, email)
        VALUES(%s, %s, %s, %s)
        RETURNING id;
        """
        try:
            self.cur.execute(sql, (first_name, last_name, phone, email))
            contact_id = self.cur.fetchone()[0]
            self.conn.commit()
            print(f"Contact added with ID: {contact_id}")
            return contact_id
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error inserting contact: {error}")
            return None

    def import_from_csv(self, file_path):
        """Import contacts from a CSV file"""
        try:
            df = pd.read_csv(file_path)
            print(f"Importing {len(df)} contacts from {file_path}...")
            
            for index, row in df.iterrows():
                first_name = row['first_name']
                last_name = row['last_name']
                phone = row['phone']
                email = row['email'] if 'email' in row and pd.notna(row['email']) else None
                
                self.insert_contact(first_name, last_name, phone, email)
                
            print("CSV import completed.")
        except Exception as error:
            print(f"Error importing from CSV: {error}")

    def update_contact(self, identifier, field, value):
        """Update a contact's information
        
        Args:
            identifier: The username (first_name) or phone number to identify the contact
            field: The field to update (first_name, last_name, phone, email)
            value: The new value
        """
        # First, check if we're looking up by name or phone
        if identifier.startswith('+') or identifier.isdigit():
            lookup_field = "phone"
        else:
            lookup_field = "first_name"
            
        sql = f"""
        UPDATE contacts
        SET {field} = %s
        WHERE {lookup_field} = %s
        """
        try:
            self.cur.execute(sql, (value, identifier))
            count = self.cur.rowcount
            self.conn.commit()
            if count:
                print(f"Contact updated successfully. {count} record(s) modified.")
            else:
                print(f"No contact found with {lookup_field} = {identifier}")
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error updating contact: {error}")
    
    def query_contacts(self, filters=None):
        """Query contacts with optional filters
        
        Args:
            filters: Dictionary with field:value pairs to filter results
        """
        sql = "SELECT id, first_name, last_name, phone, email, created_at FROM contacts"
        
        if filters:
            conditions = []
            values = []
            
            for field, value in filters.items():
                if value:
                    conditions.append(f"{field} LIKE %s")
                    values.append(f"%{value}%")
                    
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
            try:
                self.cur.execute(sql, values)
            except (Exception, psycopg2.DatabaseError) as error:
                print(f"Error querying contacts: {error}")
                return []
        else:
            try:
                self.cur.execute(sql)
            except (Exception, psycopg2.DatabaseError) as error:
                print(f"Error querying contacts: {error}")
                return []
        
        rows = self.cur.fetchall()
        return rows
    
    def delete_contact(self, identifier):
        """Delete a contact by username or phone
        
        Args:
            identifier: The username (first_name) or phone number to identify the contact
        """
        # Determine if we're looking up by name or phone
        if identifier.startswith('+') or identifier.isdigit():
            lookup_field = "phone"
        else:
            lookup_field = "first_name"
            
        sql = f"""
        DELETE FROM contacts
        WHERE {lookup_field} = %s
        """
        try:
            self.cur.execute(sql, (identifier,))
            count = self.cur.rowcount
            self.conn.commit()
            if count:
                print(f"Contact deleted successfully. {count} record(s) removed.")
            else:
                print(f"No contact found with {lookup_field} = {identifier}")
        except (Exception, psycopg2.DatabaseError) as error:
            self.conn.rollback()
            print(f"Error deleting contact: {error}")
            
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
            id, first_name, last_name, phone, email, created_at = contact
            print("{:<5} {:<15} {:<15} {:<20} {:<30} {:<20}".format(
                id, first_name, last_name, phone, email or '', created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else ''))

def main():
    phonebook = PhoneBook()
    if not phonebook.connect():
        return
    
    while True:
        print("\nPhoneBook Application")
        print("1. Add new contact")
        print("2. Import contacts from CSV")
        print("3. Update contact")
        print("4. Search contacts")
        print("5. List all contacts")
        print("6. Delete contact")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            phone = input("Enter phone number: ")
            email = input("Enter email (optional, press Enter to skip): ") or None
            
            phonebook.insert_contact(first_name, last_name, phone, email)
            
        elif choice == '2':
            file_path = input("Enter the path to the CSV file: ")
            phonebook.import_from_csv(file_path)
            
        elif choice == '3':
            identifier = input("Enter first name or phone number of contact to update: ")
            print("What would you like to update?")
            print("1. First Name")
            print("2. Last Name")
            print("3. Phone Number")
            print("4. Email")
            update_choice = input("Enter your choice (1-4): ")
            
            field_map = {
                '1': 'first_name',
                '2': 'last_name',
                '3': 'phone',
                '4': 'email'
            }
            
            if update_choice in field_map:
                field = field_map[update_choice]
                value = input(f"Enter new {field.replace('_', ' ')}: ")
                phonebook.update_contact(identifier, field, value)
            else:
                print("Invalid choice.")
                
        elif choice == '4':
            print("Search contacts (leave fields empty to ignore):")
            first_name = input("First name: ")
            last_name = input("Last name: ")
            phone = input("Phone: ")
            
            filters = {}
            if first_name:
                filters['first_name'] = first_name
            if last_name:
                filters['last_name'] = last_name
            if phone:
                filters['phone'] = phone
                
            contacts = phonebook.query_contacts(filters)
            phonebook.print_contacts(contacts)
            
        elif choice == '5':
            contacts = phonebook.query_contacts()
            phonebook.print_contacts(contacts)
            
        elif choice == '6':
            identifier = input("Enter first name or phone number of contact to delete: ")
            phonebook.delete_contact(identifier)
            
        elif choice == '0':
            break
            
        else:
            print("Invalid choice. Please try again.")
    
    phonebook.disconnect()

if __name__ == "__main__":
    main() 