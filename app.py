import streamlit as st
import logging
import zipfile
import pandas as pd
import base64
import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
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
                journal_df, image_data_list = read_pdf(jf)
                logging.info(f"Journal DF Shape: {client_df.shape}")
                logging.info(f"Image Data List: {len(image_data_list)}")
                empty_df, result_df = generate_result(client_df, journal_df)
                logging.info(f"Empty DF Shape: {empty_df.shape}")
                logging.info(f"Result DF Shape: {result_df.shape}")
                # Link Creation for Downloading the Excel Files
                def to_excel(df):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine = 'openpyxl') as writer:
                        df.to_excel(writer, index = False)
                    return output.getvalue()
                def create_pdf_with_images(image_data_list, output_path):
                    c = canvas.Canvas(output_path, pagesize = letter)
                    page_width, page_height = letter
                    images_per_page = 4
                    images_in_current_page = 0
                    margin = 50
                    spacing = 20
                    available_width = (page_width - 2 * margin - spacing) / 2  
                    available_height = (page_height - 2 * margin - spacing) / 2
                    for i, (filename, image_bytes) in enumerate(image_data_list):
                        image = Image.open(io.BytesIO(image_bytes))
                        img_width, img_height = image.size
                        aspect_ratio = img_width / img_height                        
                        if img_width > img_height:
                            new_width = min(available_width, img_width)
                            new_height = new_width / aspect_ratio
                            if new_height > available_height:
                                new_height = available_height
                                new_width = new_height * aspect_ratio
                        else:
                            new_height = min(available_height, img_height)
                            new_width = new_height * aspect_ratio
                            if new_width > available_width:
                                new_width = available_width
                                new_height = new_width / aspect_ratio
                        col = images_in_current_page % 2
                        row = images_in_current_page // 2
                        x = margin + col * (available_width + spacing)
                        y = page_height - margin - (row + 1) * (available_height + spacing) + (available_height - new_height)
                        with io.BytesIO() as img_buffer:
                            image.save(img_buffer, format = "PNG")
                            img_buffer.seek(0)
                            image_reader = ImageReader(img_buffer)
                            c.drawImage(image_reader, x, y, new_width, new_height)
                        text_x = x + new_width / 2
                        text_y = y - 15
                        c.setFont("Courier-Bold", 14)
                        c.drawCentredString(text_x, text_y, filename)
                        images_in_current_page += 1
                        if images_in_current_page == images_per_page:
                            c.showPage()
                            images_in_current_page = 0
                    if images_in_current_page > 0:
                        c.showPage()
                    c.save()
                def create_zip(pdf_file, file_one, file_two):
                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        zip_file.writestr("result.pdf", pdf_file)
                        zip_file.writestr("empty_file.xlsx", file_one)
                        zip_file.writestr("result_file.xlsx", file_two)
                    return buffer.getvalue()
                pdf_output_path = "result.pdf"
                create_pdf_with_images(image_data_list, pdf_output_path)
                with open(pdf_output_path, "rb") as f:
                    pdf_file = f.read()
                empty_excel = to_excel(empty_df)
                result_excel = to_excel(result_df)
                zip_data = create_zip(pdf_file, empty_excel, result_excel)
                os.remove(pdf_output_path)
                st.download_button(
                    label = "Download",
                    data = zip_data,
                    file_name = "excel_files.zip",
                    mime = "application/zip"
                )