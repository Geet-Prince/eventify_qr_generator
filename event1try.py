import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import qrcode
import random
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

st.title("Event Registration")

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_info(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPE)
client = gspread.authorize(CREDS)

SHEET_ID = "1I8z27cmHXUB48B6J52_p56elELf2tQVv_K-ra6jf1iQ"
SHEET_NAME = "Attendees"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = st.secrets["email_address"]
EMAIL_PASSWORD = st.secrets["email_password"]

name = st.text_input("Enter Your Name")
email = st.text_input("Enter Your Email")
mobile = st.text_input("Enter Your Mobile Number", max_chars=10)

def generate_qr_with_text(data, unique_id):
    qr = qrcode.make(data)
    qr_img = qr.convert("RGB")

    width, height = qr_img.size
    new_height = height + 50
    new_img = Image.new("RGB", (width, new_height), "white")
    new_img.paste(qr_img, (0, 50))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

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

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def send_email(to_email, subject, body, attachment):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=qr_code.png')
        msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Error sending email: {e}")
        return False

if st.button("Register"):
    if not name:
        st.error("❌ Please enter your name.")
    elif not email:
        st.error("❌ Please enter your email.")
    elif not validate_email(email):
        st.error("❌ Please enter a valid email address.")
    elif not mobile:
        st.error("❌ Please enter your mobile number.")
    elif not validate_mobile_number(mobile):
        st.error("❌ Please enter a valid 10-digit mobile number.")
    else:
        unique_id = generate_unique_id(name)
        sheet.append_row([unique_id, name, mobile, email])
        st.success("✅ Successfully Registered!")

        user_data = f"Name: {name}\nEmail: {email}\nMobile: {mobile}\nID: {unique_id}"
        qr_img_with_text = generate_qr_with_text(user_data, unique_id)

        st.image(qr_img_with_text, caption=f"QR Code for {name}")
        st.download_button("📥 Download QR Code", data=qr_img_with_text, file_name=f"{name}_qr_code.png", mime="image/png")

        # Send Email with QR Code
        subject = "Your Event QR Code"
        body = f"Hello {name},\n\nThank you for registering. Your event QR code is attached.\n\nBest Regards,\nEvent Team"

        if send_email(email, subject, body, qr_img_with_text):
            st.success("📧 QR Code sent to your email!")
