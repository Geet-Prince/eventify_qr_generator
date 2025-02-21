import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import qrcode
import random
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_file("your-service-account.json", scopes=SCOPE)
client = gspread.authorize(CREDS)

# Open Google Sheet (Replace with your Sheet Name & Sheet ID)
SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"
SHEET_NAME = "Attendees"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Streamlit UI
st.title("Event Registration with QR Code")

# User Input
name = st.text_input("Enter Your Name")
mobile = st.text_input("Enter Your Mobile Number", max_chars=10)  # Limit input to 10 characters

# Function to Generate QR Code with Unique ID Text
def generate_qr_with_text(data, unique_id):
    qr = qrcode.make(data)
    
    # Convert QR code to an image
    qr_img = qr.convert("RGB")

    # Create a blank white space above QR code to add text
    width, height = qr_img.size
    new_height = height + 50  # Extra space for the text
    new_img = Image.new("RGB", (width, new_height), "white")

    # Paste the QR code onto the new image
    new_img.paste(qr_img, (0, 50))  # Position QR code below the text area

    # Draw the unique ID text on the new image
    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)  # Use Arial font
    except:
        font = ImageFont.load_default()  # Fallback to default font

    # Get text size using textbbox (Pillow 10+)
    text_bbox = draw.textbbox((0, 0), unique_id, font=font)  # Get bounding box of text
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (width - text_width) // 2
    text_y = 10  # Position at the top of the image
    draw.text((text_x, text_y), unique_id, fill="black", font=font)

    # Save the new image to a BytesIO object
    img_io = BytesIO()
    new_img.save(img_io, format="PNG")
    img_io.seek(0)
    
    return img_io

# Function to generate a unique ID (4-digit + name)
def generate_unique_id(name):
    random_id = random.randint(1000, 9999)
    unique_id = f"{random_id}-{name}"
    return unique_id

# Function to validate mobile number (must be exactly 10 digits)
def validate_mobile_number(mobile):
    mobile_regex = r'^[0-9]{10}$'
    return bool(re.match(mobile_regex, mobile))

# Store Data in Google Sheet and Generate QR Code
if st.button("Register"):
    if not name:
        st.error("Please enter your name.")
    elif not mobile:
        st.error("Please enter your mobile number.")
    elif not validate_mobile_number(mobile):
        st.error("Please enter a valid 10-digit mobile number.")
    else:
        # Generate a unique ID for the user
        unique_id = generate_unique_id(name)

        # Append Data to Google Sheet
        sheet.append_row([unique_id, name, mobile])
        st.success("Successfully Registered!")

        # Generate QR Code with unique ID text
        user_data = f"Name: {name}\nMobile: {mobile}\nID: {unique_id}"
        qr_img_with_text = generate_qr_with_text(user_data, unique_id)

        # Display the QR Code image with unique ID
        st.image(qr_img_with_text, caption=f"QR Code for {name}")

        # Provide a download link for the QR code image
        st.download_button(
            label="Download QR Code",
            data=qr_img_with_text,
            file_name=f"{name}_qr_code.png",
            mime="image/png"
        )
