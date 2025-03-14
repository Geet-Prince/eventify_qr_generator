import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import qrcode
import random
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

USERNAME = "123"  
PASSWORD = "123"  

def login():
    """Displays the login form."""
    st.title("🔐 Secure Login")
    st.subheader("Please enter your credentials to access the site.")

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.authenticated = True
            st.session_state.first_load = True  # Mark first login attempt
            st.rerun()  # ✅ Corrected: Using st.rerun() instead of st.experimental_rerun()
        else:
            st.error("❌ Incorrect username or password")

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "first_load" not in st.session_state:
    st.session_state.first_load = False

# Redirect only once after login
if st.session_state.authenticated and st.session_state.first_load:
    st.session_state.first_load = False  # Prevent further unnecessary reruns
    st.rerun()  # ✅ Corrected: Using st.rerun()

# Show login page if not authenticated
if not st.session_state.authenticated:
    login()
    st.stop()  # Prevents further execution until logged in

# --- Main Registration Page (Only accessible after login) ---
st.title("Event Registration")

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPE)
client = gspread.authorize(CREDS)

SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"  # Replace with your actual Sheet ID
SHEET_NAME = "Attendees"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

name = st.text_input("Enter Your Name")
mobile = st.text_input("Enter Your Mobile Number", max_chars=10)  # Limit to 10 digits

def generate_qr_with_text(data, unique_id):
    qr = qrcode.make(data)
    qr_img = qr.convert("RGB")

    width, height = qr_img.size
    new_height = height + 50  # Extra space for the text
    new_img = Image.new("RGB", (width, new_height), "white")
    new_img.paste(qr_img, (0, 50))  # Position QR code below the text area

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()  # Fallback to default font

    text_width = draw.textbbox((0, 0), unique_id, font=font)[2]
    text_x = (width - text_width) // 2
    draw.text((text_x, 10), unique_id, fill="black", font=font)

    img_io = BytesIO()
    new_img.save(img_io, format="PNG")
    img_io.seek(0)
    
    return img_io

def generate_unique_id(name):
    return f"{random.randint(1000, 9999)}-{name}"

def validate_mobile_number(mobile):
    return bool(re.match(r'^[0-9]{10}$', mobile))

if st.button("Register"):
    if not name:
        st.error("❌ Please enter your name.")
    elif not mobile:
        st.error("❌ Please enter your mobile number.")
    elif not validate_mobile_number(mobile):
        st.error("❌ Please enter a valid 10-digit mobile number.")
    else:
        unique_id = generate_unique_id(name)
        sheet.append_row([unique_id, name, mobile])
        st.success("✅ Successfully Registered!")

        user_data = f"Name: {name}\nMobile: {mobile}\nID: {unique_id}"
        qr_img_with_text = generate_qr_with_text(user_data, unique_id)

        st.image(qr_img_with_text, caption=f"QR Code for {name}")
        st.download_button("📥 Download QR Code", data=qr_img_with_text, file_name=f"{name}_qr_code.png", mime="image/png")

# Logout Button
if st.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()  # ✅ Corrected: Using st.rerun()
