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


# URL of the image you want to use as the page icon
icon_url = "https://i.postimg.cc/yx4SVyNZ/OB-Logomark-Primary-Colors-3.png"

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
    st.sidebar.image("https://i.postimg.cc/G2syP8W6/OB-Primary-Logo-01-Full-Color.png", use_column_width=True)
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
    
    log_file = "login_log.json"
    
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
    
    log_file = "login_log.json"
    
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
            <img src='https://i.postimg.cc/xd8mgd7c/OB-Primary-Logo-01-Full-Color-2.png' width='400'>
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


def display_log(s3_bucket, aws_access_key, aws_secret_key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    log_file = "update_log.json"
    
    # Fetch log from S3
    try:
        obj = s3.get_object(Bucket=s3_bucket, Key=log_file)
        log_data = json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        log_data = []
    
    log_data.reverse()

    st.sidebar.markdown("## Update Log")
    for entry in log_data:
        st.sidebar.markdown(
            f'<span style="color:orange; font-weight:bold;">{entry["user"]}</span> updated '
            f'<span style="color:#e73213; font-weight:bold;">{entry["file"]}</span> on '
            f'<span style="color:#41A592; font-weight:bold;">{entry["timestamp"]}</span>',
            unsafe_allow_html=True
        )

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

        display_log(st.secrets["aws"]["bucket_name"], st.secrets["aws"]["aws_access_key"], st.secrets["aws"]["aws_secret_key"])


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

    log_file = "login_log.json"

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

# Function to upload a file to S3
def upload_file_to_s3(file_content, bucket_name, object_name, aws_access_key, aws_secret_key):
    # Define the specific sheets to check
    target_sheets = ["Product & Pricing Pivot Data", "Product Details"]
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    
    try:
        # Upload the original Excel file
        s3.put_object(Bucket=bucket_name, Key=object_name, Body=file_content)
        
        # Load workbook and check for target sheets
        workbook = pd.ExcelFile(io.BytesIO(file_content))
        results = []
        for sheet_name in workbook.sheet_names:
            if sheet_name in target_sheets:
                df = pd.read_excel(workbook, sheet_name=sheet_name)
                results.append(f"Successfully uploaded {tsv_object_name}")

        if not results:
            return False, "None of the target sheets found in the file."

        return True, "Uploaded files: " + ", ".join(results)
    except Exception as e:
        return False, f"Error uploading to S3: {str(e)}"

def call_lambda_merge(input_bucket, pivot_file_key, report_file_key, output_bucket, output_file_key, aws_access_key, aws_secret_key):
    lambda_client = boto3.client(
        'lambda',
        region_name='us-east-2',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    payload = {
        "input_bucket": input_bucket,
        "pivot_file_key": pivot_file_key,
        "report_file_key": report_file_key,
        "output_bucket": output_bucket,
        "output_file_key": output_file_key
    }
    response = lambda_client.invoke(
        FunctionName='Consolidator',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    response_from_lambda = json.load(response['Payload'])
    return response_from_lambda


def call_lambda_merge_dcr(input_bucket, pivot_file_key, report_file_key, output_bucket, output_file_key, aws_access_key, aws_secret_key):
    lambda_client = boto3.client(
        'lambda',
        region_name='us-east-2',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )
    payload = {
        "input_bucket": input_bucket,
        "pivot_file_key": pivot_file_key,
        "report_file_key": report_file_key,
        "output_bucket": output_bucket,
        "output_file_key": output_file_key
    }
    response = lambda_client.invoke(
        FunctionName='DCR-Consolidator',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    response_from_lambda = json.load(response['Payload'])
    return response_from_lambda


def pp_report():
    st.subheader("Update P&P Quicksight 📝")

    file1 = st.file_uploader("Upload the MFP Pivot Table", type=["xlsx"])
    file2 = st.file_uploader("Upload the MFP Copier Report", type=["xlsx"])
    

    if st.button("Process and Upload to S3", disabled=not (file1 and file2)):
        aws_access_key = st.secrets["aws"]["aws_access_key"]
        aws_secret_key = st.secrets["aws"]["aws_secret_key"]
        aws_region = st.secrets["aws"]["aws_region"]
        bucket_name = st.secrets["aws"]["bucket_name"]

        file_pivot = file1 if "PivotTable" in file1.name else file2
        file_report = file1 if file_pivot != file1 else file2
        pivot_key = "pivot_data.xlsx"
        report_key = "report_data.xlsx"
        output_key = "merged_data.xlsx"
        
        progress_bar = st.progress(0)

        # Upload files with progress bar
        with st.spinner('Uploading files to S3...'):
            upload_file_to_s3(file_pivot.getvalue(), bucket_name, pivot_key, aws_access_key, aws_secret_key)
            progress_bar.progress(50)  # Update progress bar to 50%

            upload_file_to_s3(file_report.getvalue(), bucket_name, report_key, aws_access_key, aws_secret_key)
            progress_bar.progress(100)  # Update progress bar to 100%

        log_update(st.session_state['username'], "US P&P")
        st.success("✅**Files Uploaded to S3!**")

        # Call Lambda without spinner
        response = call_lambda_merge(
            bucket_name,
            pivot_key,
            report_key,
            bucket_name,
            output_key,
            aws_access_key,  # Pass credentials
            aws_secret_key
        )


def dcr_report():
    st.subheader("Update DCR Quicksight 🌎")

    # Dropdown menu for selecting a country with a unique key
    country = st.selectbox(
        "Select Your Country",
        ["US", "AUS", "BR", "CA", "DE", "ES", "FR", "IT", "MX", "UK"],
        key='country_select'
    )

    # Conditional display of upload boxes based on country selection
    if country in ["AUS", "MX", "BR"]:
        file1 = st.file_uploader("Upload the file", type=["xlsx"], key='single_file_uploader')
        process_button = st.button("Process and Upload to S3", key='key2', disabled=file1 is None)
    else:
        file3 = st.file_uploader("Upload A DCR File", type=["xlsx"], key='first_file_uploader')
        file2 = st.file_uploader("Upload Specs; EU TCO or US P&P ", type=["xlsx"], key='second_file_uploader')
        # Using HTML to change the color of the text
        # Using HTML to change only the "UID Mapping File" text to purple without margin or padding
        file4 = st.file_uploader("Upload the UID Mapping File", type=["xlsx"])
        process_button = st.button("Process and Upload to S3", key='key1', disabled=not (file3 and file2))

    if process_button:
        bucket_name = st.secrets["aws"]["bucket_name"]
        aws_access_key = st.secrets["aws"]["aws_access_key"]
        aws_secret_key = st.secrets["aws"]["aws_secret_key"]
        aws_access_key2 = st.secrets["aws"]["aws_access_key2"]
        aws_secret_key2 = st.secrets["aws"]["aws_secret_key2"]

        if country in ["AUS", "MX", "BR"]:
            if file1:
                if country == "AUS":
                    # AUS: Header is on the 4th row, adjust indexing accordingly.
                    df = pd.read_excel(file1, sheet_name='Pivot Table Data', header=3)
                    df_opt = pd.read_excel(file1, sheet_name='Options Pricing', header=5, skiprows=[6])
                    df_con = pd.read_excel(file1, sheet_name='Consumables Database', header=5, skiprows=[6])

                if country == "MX":
                    # AUS: Header is on the 4th row, adjust indexing accordingly.
                    df = pd.read_excel(file1, sheet_name='Product & Pricing Pivot Data', header=3)
                    df_opt = pd.read_excel(file1, sheet_name='Options Pricing', header=5, skiprows=[6])
                    df_con = pd.read_excel(file1, sheet_name='Consumables Database', header=5, skiprows=[6])

                if country == "BR":
                    # AUS: Header is on the 4th row, adjust indexing accordingly.
                    df = pd.read_excel(file1, sheet_name='Hardware Pricing', header=7, skiprows=[8])
                    df_opt = pd.read_excel(file1, sheet_name='Options Pricing', header=5, skiprows=[6])
                    df_con = pd.read_excel(file1, sheet_name='Consumables Database', header=5, skiprows=[6])
                    df = df.drop(df.index[0])
                
                # Save the dataframes as CSV files
                df.to_csv(f"{country.lower()}_processed.csv", index=False)
                df_opt.to_csv(f"{country.lower()}_options_pricing.csv", index=False)
                df_con.to_csv(f"{country.lower()}_consumables_database.csv", index=False)

                 # Upload the modified files to S3
                with st.spinner('Uploading modified files to S3...'):
                    for csv_file in [f"{country.lower()}_processed.csv", f"{country.lower()}_options_pricing.csv", f"{country.lower()}_consumables_database.csv"]:
                        file_key = csv_file
                        with open(csv_file, "rb") as f:
                            upload_file_to_s3(f, bucket_name, file_key, aws_access_key2, aws_secret_key2)
                
                log_update(st.session_state['username'], f"{country} DCR")
                st.success(f"✅**Files Uploaded to S3!**")
        
        elif country in ["US"]:
            file_report = file3 if "MFP_Copier_Report" in file3.name else file2
            file_pivot = file3 if file_report != file3 else file2
            file_mapping = file4 if "Mapping" in file4.name else None

            # Ensure all necessary files are mapped
            if not file_mapping:
                st.error("UID Mapping File is not correctly uploaded or named.")
            else:
                # Load the data from the uploaded files
                try:
                    df_pivot = pd.read_excel(file_pivot, sheet_name="Product & Pricing Pivot Data", header=3)
                    df_report = pd.read_excel(file_report, sheet_name="Product Details", header=5)
                    df_opt = pd.read_excel(file_pivot, sheet_name='Options Pricing', header=4, skiprows=[5])
                    df_con = pd.read_excel(file_pivot, sheet_name='Consumables Database', header=3, skiprows=[4])
                    df_matrix = pd.read_excel(file_pivot, sheet_name='Dealer Program Matrix', header=3, skiprows=[4])
                    df_report = df_report.iloc[1:].reset_index(drop=True)

                except:
                    pass

                df_mapping = pd.read_excel(file_mapping)
                
                
                # Merge file_mapping into file_pivot on the 'Product' column
                df_pivot = pd.merge(df_pivot, df_mapping, on='Product', how='left')
                df_report = pd.merge(df_report, df_mapping, on='Product', how='left')
                merged_file = "merged_pivot.xlsx"
                with pd.ExcelWriter(merged_file) as writer:
                    df_pivot.to_excel(writer, sheet_name="Product & Pricing Pivot Data", index=False)

                merged_file2 = "merged_report.xlsx"
                with pd.ExcelWriter(merged_file2) as writer:
                    df_report.to_excel(writer, sheet_name="Product Details", index=False)

                con_filename = f"{country.lower()}_con.csv"
                opt_filename = f"{country.lower()}_opt.csv"
                matrix_filename = f"{country.lower()}_matrix.csv"
                
                df_con.to_csv(con_filename, index=False)
                df_opt.to_csv(opt_filename, index=False)
                df_matrix.to_csv(matrix_filename, index=False)

            file_key = f"{country.lower()}_pivot.xlsx"
            file_key2 = f"{country.lower()}_report.xlsx"
            progress_bar = st.progress(0)
            # Dynamically set keys based on the selected country
            pivot_key = "us_pivot.xlsx"
            report_key = "us_report.xlsx"
            output_key = "us_merged.xlsx"
           
            with st.spinner('Uploading files to S3...'):
                with open(merged_file, "rb") as f:
                    upload_file_to_s3(f, bucket_name, file_key, aws_access_key, aws_secret_key)
                progress_bar.progress(50)
                with open(merged_file2, "rb") as f:
                    upload_file_to_s3(f, bucket_name, file_key2, aws_access_key, aws_secret_key)
                #upload_file_to_s3(file_pivot.getvalue(), bucket_name, pivot_key, aws_access_key, aws_secret_key)
                progress_bar.progress(100)
            
                # Upload CSV files to S3 with dynamic names
                with open(con_filename, "rb") as f:
                    upload_file_to_s3(f, bucket_name, con_filename, aws_access_key2, aws_secret_key2)
                with open(opt_filename, "rb") as f:
                    upload_file_to_s3(f, bucket_name, opt_filename, aws_access_key2, aws_secret_key2)
                with open(matrix_filename, "rb") as f:
                    upload_file_to_s3(f, bucket_name, matrix_filename, aws_access_key2, aws_secret_key2)
            log_update(st.session_state['username'], f"{country} DCR")
            st.success("✅**Files Uploaded to S3!**")
            
            # Call Lambda without spinner
            response = call_lambda_merge_dcr(
                bucket_name,
                pivot_key,
                report_key,
                bucket_name,
                output_key,
                aws_access_key,  # Pass credentials
                aws_secret_key
            )

        else:
            # Determine which file is pivot and which is report based on a condition in their names
            file_report = file3 if "MFP_Copier_Report" in file3.name or "EU MFP" in file3.name else file2
            file_pivot = file3 if file_report != file3 else file2
            file_mapping = file4 if "Mapping" in file4.name else None

            # Ensure all necessary files are mapped
            if not file_mapping:
                st.error("UID Mapping File is not correctly uploaded or named.")
            else:
                # Load the data from the uploaded files
                try:
                    df_pivot = pd.read_excel(file_pivot, sheet_name="Product & Pricing Pivot Data", header=3)
                except:
                    df_pivot = pd.read_excel(file_pivot, sheet_name="Pivot Table Data", header=3)

                df_mapping = pd.read_excel(file_mapping)
                
                #st.write(df_pivot)
                # Merge file_mapping into file_pivot on the 'Product' column
                df_pivot = pd.merge(df_pivot, df_mapping, on='Product', how='left')

                merged_file = "merged_pivot.xlsx"
                with pd.ExcelWriter(merged_file) as writer:
                    df_pivot.to_excel(writer, sheet_name="Pivot Table Data", index=False)

            file_key = f"{country.lower()}_pivot.xlsx"
            progress_bar = st.progress(0)
            # Dynamically set keys based on the selected country
            pivot_key = f"{country.lower()}_pivot.xlsx"
            report_key = f"{country.lower()}_report.xlsx"
            output_key = f"{country.lower()}_merged.xlsx"
           
            with st.spinner('Uploading files to S3...'):
                with open(merged_file, "rb") as f:
                    upload_file_to_s3(f, bucket_name, file_key, aws_access_key, aws_secret_key)
                #upload_file_to_s3(file_pivot.getvalue(), bucket_name, pivot_key, aws_access_key, aws_secret_key)
                progress_bar.progress(50)
                upload_file_to_s3(file_report.getvalue(), bucket_name, report_key, aws_access_key, aws_secret_key)
                progress_bar.progress(100)
            st.success("✅**Files Uploaded to S3!**")
            # Call Lambda without spinner
            response = call_lambda_merge_dcr(
                bucket_name,
                pivot_key,
                report_key,
                bucket_name,
                output_key,
                aws_access_key,  # Pass credentials
                aws_secret_key
            )
        
def display_dashboard():
    st.header("Update Copiers Quicksight Data 🔄")
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

    st.info("⚠️ Quicksight Refreshes Automatically Every Monday at 1pm. To Force an Immediate Refresh, go to Quicksights>Datasets>MFP-Copier-Quicksight-Data>Refresh>Refresh Now")
    pp_report()  # Call the first section
    dcr_report()  # Call the second, currently blank section

if __name__ == "__main__":
    main()