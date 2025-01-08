import streamlit as st
import sqlite3
from datetime import date
import re

# Database setup


# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect("petitions.db", check_same_thread=False)

# Create tables (run only once to initialize)
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS petitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            target TEXT,
            deadline DATE,
            signature_needed INTEGER,
            signature_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            petition_id INTEGER,
            email TEXT,
            FOREIGN KEY (petition_id) REFERENCES petitions (id)
        )
    """)
    conn.commit()

# Fetch petitions
def get_petitions_with_progress():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, signature_count, signature_needed 
        FROM petitions
    """)
    petitions = cursor.fetchall()
    return petitions

# Add a new petition
def add_petition(title, description, target, deadline, signature_needed):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO petitions (title, description, target, deadline, signature_needed)
        VALUES (?, ?, ?, ?, ?)
    """, (title, description, target, deadline, signature_needed))
    conn.commit()

# Add a signature to a petition
def add_signature(petition_id, email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO signatures (petition_id, email) VALUES (?, ?)
    """, (petition_id, email))
    cursor.execute("""
        UPDATE petitions SET signature_count = signature_count + 1 WHERE id = ?
    """, (petition_id,))
    conn.commit()

# Email verification
def verify_email(email):
    return ".edu.in" in email

# Display petitions with progress bars
def display_petitions():
    petitions = get_petitions_with_progress()
    
    if not petitions:
        st.write("No petitions available.")
        return
    
    for petition in petitions:
        petition_id, title, signature_count, signature_needed = petition
        progress = min((signature_count / signature_needed) * 100, 100) if signature_needed > 0 else 0
        
        st.write(f"**{title}**")
        st.progress(progress / 100)
        
        email = st.text_input(f"Enter your email to sign '{title}'", key=f"email_{petition_id}")
        if st.button(f"Sign Petition {petition_id}", key=f"sign_{petition_id}"):
            if verify_email(email):
                add_signature(petition_id, email)
                st.success(f"Signed '{title}' successfully!")
            else:
                st.error("Invalid email address. Please use a valid email.")

# Main app logic
create_tables()

# Initialize session state variables
if "is_creating_petition" not in st.session_state:
    st.session_state.is_creating_petition = True

# Toggle between modes
if st.button("Switch to Sign Petitions" if st.session_state.is_creating_petition else "Switch to Create Petition"):
    st.session_state.is_creating_petition = not st.session_state.is_creating_petition

# Display appropriate interface based on mode
if st.session_state.is_creating_petition:
    st.title("Create a New Petition")
    title = st.text_input("Petition Title")
    description = st.text_area("Petition Description")
    target = st.text_input("Petition Target")
    deadline = st.date_input("Petition Deadline")
    signature_needed = st.number_input("Number of Signatures Needed", min_value=1, step=1)
    
    if st.button("Create Petition"):
        if title and description and target and signature_needed:
            add_petition(title, description, target, deadline, signature_needed)
            st.success("Petition created successfully!")
        else:
            st.error("All fields are required.")
else:
    st.title("Sign Existing Petitions")
    display_petitions()
