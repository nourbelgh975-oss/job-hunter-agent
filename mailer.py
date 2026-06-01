import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_application_email(gmail_user, gmail_password, to_email, subject, body, cv_content=None, cv_filename=None):
    """
    Sends an application email via Gmail SMTP using TLS.
    
    Parameters:
    - gmail_user: Sender's Gmail address (e.g. user@gmail.com)
    - gmail_password: Gmail App Password (16 characters)
    - to_email: Recipient email address
    - subject: Email subject line
    - body: Email cover letter/message content
    - cv_content: Raw bytes of the CV attachment (optional)
    - cv_filename: Filename for the CV attachment (optional)
    
    Returns:
    - (success: bool, message: str)
    """
    if not gmail_user or not gmail_password:
        return False, "Gmail credentials are not configured in settings."
        
    try:
        # Create MIMEMultipart message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach the body of the email
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach CV if provided
        if cv_content and cv_filename:
            part = MIMEApplication(cv_content, Name=cv_filename)
            part['Content-Disposition'] = f'attachment; filename="{cv_filename}"'
            msg.attach(part)
            
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(0) # 0 means off, 1 means on
        server.starttls()
        
        # Log in
        server.login(gmail_user, gmail_password)
        
        # Send
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.quit()
        
        return True, "Email successfully sent."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed. Please check your Gmail address and verify that you are using an 'App Password' instead of your main password."
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"
