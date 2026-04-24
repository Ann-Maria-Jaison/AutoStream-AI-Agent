import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_welcome_email(to_email, user_name, plan_name):
    """
    Sends a welcome email with a join link for the selected plan.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD") # Gmail App Password

    if not sender_email or not sender_password:
        print("Email credentials not set. Skipping email.")
        return False

    # Define join links based on plan
    join_links = {
        "Basic Plan": "https://autostream.ai/checkout/basic",
        "Pro Plan": "https://autostream.ai/checkout/pro"
    }
    
    join_link = join_links.get(plan_name, "https://autostream.ai/pricing")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = f"Welcome to AutoStream! - {plan_name}"

    body = f"""
    Hi {user_name},

    Thank you for choosing AutoStream! 
    
    You've selected the {plan_name}. We're excited to help you automate your video content creation.

    Click the link below to complete your setup and start creating:
    {join_link}

    If you have any questions, just reply to this email!

    Best,
    The AutoStream Team
    """
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✓ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
