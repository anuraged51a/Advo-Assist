import streamlit as st
import logging
import zipfile
import pandas as pd
import base64
import io
from utils.utils import (
    read_pdf,
    generate_result
)


# Page Header
st.set_page_config(page_title="Advo-Assist", page_icon="./img/crop_logo.png",)


# Logging Configuration
logging.basicConfig(
    format = '%(asctime)s - %(message)s',
    level = logging.INFO,
    handlers = [
        logging.StreamHandler()
    ]
)


# Custom CSS
custom_css = """
<style>
div[role="alert"] {
    background-color: #000000;
    color: #6C9BF3;
    text-align: center; 
    font-weight: bold;
    border: 2px solid #6C9BF3;
}
"""
st.markdown(custom_css, unsafe_allow_html=True)


# Page Content
st.image("./img/full_logo.png")
# st.header("Advo-Assist")
col1, col2, col3 = st.columns([1,3,1])
with col2:
    st.subheader("Hey! Good to see you back here!")
st.write("\n\n")
st.write("\n\n")


# User Validation
if 'credentials_verified' not in st.session_state:
    st.session_state.credentials_verified = False

def user_validation():
    if st.session_state.user_name == "demo_user" and st.session_state.user_password == "demo_password":
        st.session_state.credentials_verified = True
    else:
        st.error("INCORRECT CREDENTIALS")


# Conditional Check
if not st.session_state.credentials_verified:
    col4, col5, col6 = st.columns([1,2,1])
    with col5:
        st.text_input("Enter your User Name", key="user_name")
        st.write("\n\n")
        st.text_input("Enter your User Password", type="password" ,key="user_password")
        st.write("\n\n")
        col7, col8 = st.columns([1,2])
        with col8:
            st.button("Submit", on_click=user_validation)
else:
    # Client File Uploader
    cf = st.file_uploader("Upload Client Files (Max 1)", type = ['csv', 'xlsx'])
    # Journal File Uploader
    jf = st.file_uploader("Upload Journal Files (Max 1)", type = ['pdf'])
    # Button
    st.write("\n\n")
    st.write("\n\n")
    col4, col5, col6 = st.columns([1.5,1,1])
    with col5:
        if st.button("Generate"):
            if cf and jf:
                # Load the Dataframe
                if cf.name.endswith('.csv'):
                    client_df = pd.read_csv(cf)
                elif cf.name.endswith('.xlsx'):
                    client_df = pd.read_excel(cf)
                logging.info(f"Client DF Shape: {client_df.shape}")
                logging.info(f"Client DF Columns: {list(client_df.columns)}")
                # Load the PDF File and Run the Algorithm   
                journal_df = read_pdf(jf)
                logging.info(f"Journal DF Shape: {client_df.shape}")
                empty_df, result_df = generate_result(client_df, journal_df)
                logging.info(f"Empty DF Shape: {empty_df.shape}")
                logging.info(f"Result DF Shape: {result_df.shape}")
                # Link Creation for Downloading the Excel Files
                def to_excel(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    return output.getvalue()
                def create_zip(file_one, file_two):
                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        zip_file.writestr("empty_file.xlsx", file_one)
                        zip_file.writestr("result_file.xlsx", file_two)
                    return buffer.getvalue()
                empty_excel = to_excel(empty_df)
                result_excel = to_excel(result_df)
                zip_data = create_zip(empty_excel, result_excel)
                st.download_button(
                    label = "Download",
                    data = zip_data,
                    file_name = "excel_files.zip",
                    mime = "application/zip"
                )