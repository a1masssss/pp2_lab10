# Advanced PhoneBook with PostgreSQL Functions and Stored Procedures

This is an enhanced version of the PhoneBook application that uses PostgreSQL functions and stored procedures to perform database operations.

## Features

- **Search by Pattern**: Find contacts based on a pattern (part of name, phone, etc.)
- **Contact Upsert**: Add new contacts or update existing ones
- **Batch Contact Import**: Import multiple contacts with validation
- **Paginated Queries**: List contacts with pagination support
- **Contact Deletion**: Delete contacts by identifier (name or phone)

## Setup

1. First, make sure PostgreSQL is running and the database is created
2. Set up the basic PhoneBook database (if not already done):
   ```
   python db_setup.py
   ```
3. Set up the PostgreSQL functions and stored procedures:
   ```
   python setup_functions.py
   ```

## Running the Application

### Main Application

```
python advanced_phonebook.py
```

### Batch Import from CSV

```
python batch_import.py [csv_file_path]
```

If no CSV file path is provided, it will use the default `data/contacts_batch.csv`.

## Implementation Details

The application implements the following PostgreSQL functions and stored procedures:

1. **search_contacts_by_pattern(search_pattern TEXT)**: Function that returns all records based on a pattern
2. **upsert_contact(first_name, last_name, phone, email)**: Procedure to insert new user or update if exists
3. **insert_multiple_contacts(first_names[], last_names[], phones[], emails[])**: Procedure to insert many new users with validation
4. **get_contacts_paginated(limit, offset)**: Function to query data with pagination
5. **delete_contact_by_identifier(identifier)**: Procedure to delete data by identifier

## Phone Number Validation

Phone numbers are validated using the `is_valid_phone()` function:
- Must contain 10-15 digits
- Can optionally start with '+'
- Cannot contain letters or other characters

## Example Usage

### Search by Pattern

```sql
SELECT * FROM search_contacts_by_pattern('John');
```

### Insert or Update Contact

```sql
CALL upsert_contact('John', 'Doe', '+12223334444', 'john.doe@example.com');
```

### Paginated Query

```sql
SELECT * FROM get_contacts_paginated(10, 0);  -- First page, 10 records per page
```

### Delete Contact

```sql
CALL delete_contact_by_identifier('John');
``` 