-- Function to search contacts by pattern
CREATE OR REPLACE FUNCTION search_contacts_by_pattern(search_pattern TEXT)
RETURNS TABLE (
    id INTEGER,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.last_name, c.phone, c.email, c.created_at
    FROM contacts c
    WHERE 
        c.first_name ILIKE '%' || search_pattern || '%' OR
        c.last_name ILIKE '%' || search_pattern || '%' OR
        c.phone ILIKE '%' || search_pattern || '%' OR
        c.email ILIKE '%' || search_pattern || '%';
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert or update a contact
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name VARCHAR(50),
    p_last_name VARCHAR(50),
    p_phone VARCHAR(20),
    p_email VARCHAR(100) DEFAULT NULL
)
AS $$
DECLARE
    v_user_exists BOOLEAN;
BEGIN
    -- Check if user exists with the given first name
    SELECT EXISTS (
        SELECT 1 
        FROM contacts 
        WHERE first_name = p_first_name AND last_name = p_last_name
    ) INTO v_user_exists;
    
    IF v_user_exists THEN
        -- Update phone if user exists
        UPDATE contacts
        SET phone = p_phone,
            email = COALESCE(p_email, email)
        WHERE first_name = p_first_name AND last_name = p_last_name;
        
        RAISE NOTICE 'Contact updated: % %', p_first_name, p_last_name;
    ELSE
        -- Insert new contact
        INSERT INTO contacts (first_name, last_name, phone, email)
        VALUES (p_first_name, p_last_name, p_phone, p_email);
        
        RAISE NOTICE 'New contact added: % %', p_first_name, p_last_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to validate phone number
CREATE OR REPLACE FUNCTION is_valid_phone(phone_number VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if phone starts with + and has at least 10 digits
    RETURN phone_number ~ '^\+?[0-9]{10,15}$';
END;
$$ LANGUAGE plpgsql;

-- Table type for bulk insert results
CREATE TYPE contact_insert_result AS (
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    status VARCHAR(50)
);

-- Procedure to insert multiple contacts with validation
CREATE OR REPLACE PROCEDURE insert_multiple_contacts(
    p_first_names VARCHAR(50)[],
    p_last_names VARCHAR(50)[],
    p_phones VARCHAR(20)[],
    p_emails VARCHAR(100)[] DEFAULT NULL
)
RETURNS SETOF contact_insert_result AS $$
DECLARE
    v_count INTEGER;
    v_result contact_insert_result;
    v_email VARCHAR(100);
BEGIN
    -- Get the count of input arrays
    v_count := array_length(p_first_names, 1);
    
    -- Check if all arrays have the same length
    IF v_count != array_length(p_last_names, 1) OR v_count != array_length(p_phones, 1) THEN
        RAISE EXCEPTION 'Input arrays must have the same length';
    END IF;
    
    -- Process each contact
    FOR i IN 1..v_count LOOP
        v_result.first_name := p_first_names[i];
        v_result.last_name := p_last_names[i];
        v_result.phone := p_phones[i];
        
        -- Validate phone number
        IF NOT is_valid_phone(p_phones[i]) THEN
            v_result.status := 'Invalid phone number';
            RETURN NEXT v_result;
            CONTINUE;
        END IF;
        
        -- Get email if provided
        IF p_emails IS NOT NULL AND i <= array_length(p_emails, 1) THEN
            v_email := p_emails[i];
        ELSE
            v_email := NULL;
        END IF;
        
        -- Check if contact exists
        IF EXISTS (
            SELECT 1 
            FROM contacts 
            WHERE first_name = p_first_names[i] AND last_name = p_last_names[i]
        ) THEN
            -- Update existing contact
            UPDATE contacts
            SET phone = p_phones[i],
                email = COALESCE(v_email, email)
            WHERE first_name = p_first_names[i] AND last_name = p_last_names[i];
            
            v_result.status := 'Updated';
        ELSE
            -- Insert new contact
            INSERT INTO contacts (first_name, last_name, phone, email)
            VALUES (p_first_names[i], p_last_names[i], p_phones[i], v_email);
            
            v_result.status := 'Inserted';
        END IF;
        
        RETURN NEXT v_result;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to get contacts with pagination
CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit INTEGER DEFAULT 10,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id INTEGER,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.last_name, c.phone, c.email, c.created_at
    FROM contacts c
    ORDER BY c.id
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Procedure to delete contact by username or phone
CREATE OR REPLACE PROCEDURE delete_contact_by_identifier(p_identifier VARCHAR)
AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Delete by first name or phone
    WITH deleted AS (
        DELETE FROM contacts
        WHERE first_name = p_identifier OR phone = p_identifier
        RETURNING *
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    IF v_deleted_count > 0 THEN
        RAISE NOTICE 'Deleted % contact(s) with identifier: %', v_deleted_count, p_identifier;
    ELSE
        RAISE NOTICE 'No contacts found with identifier: %', p_identifier;
    END IF;
END;
$$ LANGUAGE plpgsql; 