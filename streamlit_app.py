import streamlit as st
import datetime
import numpy as np
import pandas as pd
import altair as alt
from st_files_connection import FilesConnection
import hashlib
from io import BytesIO
import io
import json
from PIL import Image
import requests
import pytz
import openpyxl
import boto3
import warnings
import json

# URL of the image you want to use as the page icon
icon_url = "https://i.postimg.cc/s2mzdzrz/newsicon.png"

# Download the image
response = requests.get(icon_url)
image = Image.open(BytesIO(response.content))


# Set the Streamlit page configuration with the custom icon
st.set_page_config(
    page_title="Upload",
    page_icon=image,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sidebar button font size
st.markdown(
    """
    <style>
    /* Increase the font size of p tags within specific div in the sidebar */
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        font-size: 20px;  /* Adjust this value as needed */
    }
    </style>
    """,
    unsafe_allow_html=True
)


def toggle_mode():
    if 'mode' not in st.session_state:
        st.session_state['mode'] = 'default'
    if st.session_state['mode'] == 'default':
        st.session_state['mode'] = 'red'
    else:
        st.session_state['mode'] = 'default'
    st.experimental_rerun()

def sidebar():
    st.sidebar.image("https://i.postimg.cc/HxTLX3pY/News-Hub.png", use_column_width=True)
    st.sidebar.markdown("---")
    # Add a button to toggle between dark mode and light mode
    # Add a button to toggle between default mode and red mode

#    st.sidebar.markdown(
#    """
#    <div style="text-align: center;">
#        <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHF1bDFraGpsbmt1YWFxMXB0dG9jOXpnaW1xY3ZhM3kwY2NsZThodCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/rBszdmXbzglQUX7N4j/giphy.gif" alt="Alt Text" style="width:100%; max-width:300px;">
#    </div>
#    """,
#    unsafe_allow_html=True
#)


def login(username, password):
    try:
        # Access the dictionary of usernames and hashed passwords directly
        user_passwords = st.secrets["credentials"]
        user_emojis = st.secrets["emojis"]
        # Convert the input password to its hashed version
        input_hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # Check if the username exists and if the hashed password matches
        if user_passwords.get(username) == input_hashed_password:
            last_login = get_last_login(username)  # Fetch the last login time
            st.session_state['username'] = username  # Set the username in session state
            st.session_state['logged_in'] = True  # Ensure logged_in is also set
            st.session_state['emoji'] = user_emojis.get(username, "")  # Set the emoji in session state
            st.session_state['last_login'] = last_login  # Set the last login time in session state
            with st.spinner('Logging in...'):
                update_login_log(username)  # Update the login log
            return True
    except KeyError as e:
        st.error(f"KeyError: {e} - Check your secrets.toml configuration.")
        return False
    return False
    

def update_login_log(username):
    aws_access_key = st.secrets["aws"]["aws_access_key2"]
    aws_secret_key = st.secrets["aws"]["aws_secret_key2"]
    log_bucket = st.secrets["aws"]["bucket_name"]
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    log_file = "login_log_news.json"
    
    # Fetch existing log from S3
    try:
        obj = s3.get_object(Bucket=log_bucket, Key=log_file)
        log_data = json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        log_data = {}

    # Ensure the username has an entry
    if username not in log_data:
        log_data[username] = []

    # Append new login time for the username
    pst_tz = pytz.timezone('US/Pacific')
    timestamp = datetime.datetime.now(pytz.utc).astimezone(pst_tz).strftime('%-m/%-d/%y, %-I:%M%p')
    log_data[username].append(timestamp)

    # Save log back to S3
    s3.put_object(Bucket=log_bucket, Key=log_file, Body=json.dumps(log_data))

def get_last_login(username):
    aws_access_key = st.secrets["aws"]["aws_access_key"]
    aws_secret_key = st.secrets["aws"]["aws_secret_key"]
    log_bucket = st.secrets["aws"]["bucket_name"]
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    log_file = "login_log_news.json"
    
    # Fetch existing log from S3
    try:
        obj = s3.get_object(Bucket=log_bucket, Key=log_file)
        log_data = json.loads(obj['Body'].read().decode('utf-8'))
        if username in log_data and log_data[username]:
            return log_data[username][-1]
        else:
            return "Never"
    except s3.exceptions.NoSuchKey:
        return "Never"


def display_login_form():
    # Create three columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:  # Middle column for the form
        st.markdown("""
        <center>
            <img src='https://i.postimg.cc/HxTLX3pY/News-Hub.png' width='400'>
        </center>
        """, unsafe_allow_html=True)
        with st.form(key='login_form'):
            # Input fields for username and password
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                if login(username, password):  # Assume login is a function defined to check credentials
                    st.session_state['logged_in'] = True  # Update session state
                    st.rerun()
                else:
                    st.error("Invalid username or password")



def log_update(username, file_name):
    if username == "admin":
        return
    
    aws_access_key2 = st.secrets["aws"]["aws_access_key2"]
    aws_secret_key2 = st.secrets["aws"]["aws_secret_key2"]
    log_bucket = st.secrets["aws"]["bucket_name"]
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key2,
        aws_secret_access_key=aws_secret_key2
    )
    
    log_file = "update_log.json"
    username = st.session_state.get('username', 'unknown')
    # Fetch existing log from S3
    try:
        obj = s3.get_object(Bucket=log_bucket, Key=log_file)
        log_data = json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        log_data = []

    # Append new log entry
    pst_tz = pytz.timezone('US/Pacific')
    timestamp = datetime.datetime.now(pytz.utc).astimezone(pst_tz).strftime('%-m/%-d/%y, %-I:%M%p')
    log_entry = {
        "user": username,
        "file": file_name,
        "timestamp": timestamp
    }
    log_data.append(log_entry)

    # Save log back to S3
    s3.put_object(Bucket=log_bucket, Key=log_file, Body=json.dumps(log_data))


def load_json_from_s3(bucket_name, file_name, aws_access_key, aws_secret_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_name)
        data = json.loads(obj['Body'].read().decode('utf-8'))
        return data
    except Exception as e:
        st.error(f"Error loading JSON data: {e}")
        return None

def display_json_data(data):
    for group in data:
        st.markdown(f"<h1 style='color:teal;'>{group['group_title']}</h1>", unsafe_allow_html=True)
        for article in group['articles']:
            st.markdown(f"<h2 style='color:blue;'>{article['title']}</h2>", unsafe_allow_html=True)
            st.write(f"**Date:** {article['date']}")
            st.write(f"**Description:** {article['description']}")
            st.markdown(f"**Source:** <span style='color:orange;'>{article['source_name']}</span>", unsafe_allow_html=True)
            if article['link'] != 'NA':
                st.write(f"[Link]({article['link']})")
            st.markdown("---")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if 'username' not in st.session_state:
        st.session_state['username'] = None

    if 'show_profile' not in st.session_state:
        st.session_state['show_profile'] = False

    if st.session_state['logged_in']:
        if 'page' not in st.session_state:
            st.session_state['page'] = 'home'
        
        sidebar()

        ## YOLO 
        # Display the profile button with username

        if st.sidebar.button(f"{st.session_state.get('emoji', '')} {st.session_state['username']}", use_container_width=True):
            st.session_state['show_modal'] = True
        
        # Show last login time
        last_login_time = st.session_state.get('last_login', "Never")
        st.sidebar.markdown(
            f"<p style='color:darkgrey; font-style:italic;'>Last Login: {last_login_time}</p>",
            unsafe_allow_html=True
        )

        # Add "View Logins" button for admin
        if st.session_state['username'] == 'admin':
            if st.sidebar.button("🔒 View Logins", use_container_width=True):
                st.session_state['page'] = 'view_logins'

        # Redirect based on the selected page
        if st.session_state['page'] == 'home':
            display_dashboard()
        elif st.session_state['page'] == 'view_logins':
            display_logins_page()
    else:
        display_login_form()


def display_logins_page():
    st.title("Login Information")
    aws_access_key = st.secrets["aws"]["aws_access_key"]
    aws_secret_key = st.secrets["aws"]["aws_secret_key"]
    log_bucket = st.secrets["aws"]["bucket_name"]
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )

    log_file = "login_log_news.json"

    # Fetch existing log from S3
    try:
        obj = s3.get_object(Bucket=log_bucket, Key=log_file)
        log_data = json.loads(obj['Body'].read().decode('utf-8'))

        # Organize the data into a table format
        users = list(log_data.keys())
        max_logins = max(len(logins) for logins in log_data.values())
        data = []

        for i in range(max_logins):
            row = []
            for user in users:
                if i < len(log_data[user]):
                    row.append(log_data[user][i])
                else:
                    row.append("")
            data.append(row)

        df = pd.DataFrame(data, columns=users)

        # Display the table using Streamlit without index
        st.write(df.to_html(index=False), unsafe_allow_html=True)

    except s3.exceptions.NoSuchKey:
        st.error("No login log found.")

    # Add a "Back" button
    if st.button("Back"):
        st.session_state['page'] = 'home'
        st.experimental_rerun()


def main_page():
    st.subheader("News")

def display_dashboard():
    st.header("NewsHub 📝")
    # Custom CSS to override the default info color
    css = """
    <style>
    div.stAlert {
        background-color: teal;
    }
    div.stAlert p {
        color: white;
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)  # Inject custom CSS

    # Display an info message with the new red background
    st.info("⚠️ News")
    main_page()  # Call the first section

    # Load and display JSON data
    aws_access_key = st.secrets["aws"]["aws_access_key"]
    aws_secret_key = st.secrets["aws"]["aws_secret_key"]
    bucket_name = st.secrets["aws"]["bucket_name"]
    file_name = "PAIN.json"

    data = load_json_from_s3(bucket_name, file_name, aws_access_key, aws_secret_key)
    if data:
        display_json_data(data)

if __name__ == "__main__":
    main()