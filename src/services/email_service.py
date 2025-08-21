"""
Email service for sending notifications to users
"""
import logging
from flask import current_app, render_template_string
from flask_mail import Mail, Message
from src.app import mail


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_device_claimed_email(user_email, user_nickname, device_name, device_type, device_model=None, device_registration=None):
        """
        Send email notification when a device is successfully claimed.
        
        Args:
            user_email (str): User's email address
            user_nickname (str): User's display name
            device_name (str): Name of the claimed device
            device_type (str): Type of device (e.g., aircraft)
            device_model (str, optional): Device model
            device_registration (str, optional): Device registration/tail number
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create email subject
            subject = f"Device Claimed Successfully - {device_name}"
            
            # Create email body
            device_details = []
            if device_model:
                device_details.append(f"Model: {device_model}")
            if device_registration:
                device_details.append(f"Registration: {device_registration}")
            
            device_info = f" ({', '.join(device_details)})" if device_details else ""
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Device Claimed - KanardiaCloud</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #FF5722 0%, #FF7043 100%);
                        color: white;
                        padding: 30px 20px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .content {{
                        background: #ffffff;
                        padding: 30px;
                        border: 1px solid #e0e0e0;
                        border-top: none;
                        border-radius: 0 0 8px 8px;
                    }}
                    .device-card {{
                        background: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 6px;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .device-name {{
                        font-size: 18px;
                        font-weight: 600;
                        color: #FF5722;
                        margin-bottom: 10px;
                    }}
                    .device-detail {{
                        margin: 5px 0;
                        color: #666;
                    }}
                    .cta-button {{
                        display: inline-block;
                        background: #FF5722;
                        color: white;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        font-weight: 500;
                        margin: 20px 0;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e0e0e0;
                        color: #666;
                        font-size: 14px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎉 Device Successfully Claimed!</h1>
                </div>
                
                <div class="content">
                    <p>Hello {user_nickname or user_email},</p>
                    
                    <p>Great news! Your device has been successfully claimed and added to your KanardiaCloud account.</p>
                    
                    <div class="device-card">
                        <div class="device-name">{device_name}{device_info}</div>
                        <div class="device-detail"><strong>Type:</strong> {device_type.title()}</div>
                        {f'<div class="device-detail"><strong>Model:</strong> {device_model}</div>' if device_model else ''}
                        {f'<div class="device-detail"><strong>Registration:</strong> {device_registration}</div>' if device_registration else ''}
                    </div>
                    
                    <p>You can now:</p>
                    <ul>
                        <li>View and manage your device in the dashboard</li>
                        <li>Access logbook entries and flight data</li>
                        <li>Create and manage checklists</li>
                        <li>Design custom instrument layouts</li>
                        <li>Configure pilot mappings for shared aircraft</li>
                    </ul>
                    
                    <p style="text-align: center;">
                        <a href="https://casey.kanardia.eu/dashboard" class="cta-button">Go to Dashboard</a>
                    </p>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Happy flying!</p>
                    <p><strong>The KanardiaCloud Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from KanardiaCloud. Please do not reply to this email.</p>
                    <p>© 2025 Kanardia d.o.o. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_body = f"""
Device Successfully Claimed - KanardiaCloud

Hello {user_nickname or user_email},

Great news! Your device has been successfully claimed and added to your KanardiaCloud account.

Device Details:
- Name: {device_name}{device_info}
- Type: {device_type.title()}
{f'- Model: {device_model}' if device_model else ''}
{f'- Registration: {device_registration}' if device_registration else ''}

You can now:
• View and manage your device in the dashboard
• Access logbook entries and flight data
• Create and manage checklists
• Design custom instrument layouts
• Configure pilot mappings for shared aircraft

Access your dashboard: https://casey.kanardia.eu/dashboard

If you have any questions or need assistance, please don't hesitate to contact our support team.

Happy flying!
The KanardiaCloud Team

---
This is an automated message from KanardiaCloud. Please do not reply to this email.
© 2025 Kanardia d.o.o. All rights reserved.
            """
            
            # Create and send email
            msg = Message(
                subject=subject,
                recipients=[user_email],
                body=text_body,
                html=html_body
            )
            
            mail.send(msg)
            
            logging.info(f"Device claimed email sent successfully to {user_email} for device '{device_name}'")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send device claimed email to {user_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_test_email(recipient_email):
        """
        Send a test email to verify email configuration.
        
        Args:
            recipient_email (str): Email address to send test to
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = "KanardiaCloud Email Test"
            
            html_body = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Email Test - KanardiaCloud</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        background: #FF5722;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 6px;
                    }
                    .content {
                        padding: 20px;
                        background: #f9f9f9;
                        border-radius: 6px;
                        margin-top: 10px;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>✅ Email Test Successful!</h1>
                </div>
                <div class="content">
                    <p>This is a test email from KanardiaCloud.</p>
                    <p>If you're receiving this email, the email configuration is working correctly.</p>
                    <p><strong>Timestamp:</strong> {{ timestamp }}</p>
                </div>
            </body>
            </html>
            """
            
            text_body = """
Email Test - KanardiaCloud

✅ Email Test Successful!

This is a test email from KanardiaCloud.
If you're receiving this email, the email configuration is working correctly.

Timestamp: {{ timestamp }}
            """
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            html_body = html_body.replace("{{ timestamp }}", timestamp)
            text_body = text_body.replace("{{ timestamp }}", timestamp)
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                body=text_body,
                html=html_body
            )
            
            mail.send(msg)
            
            logging.info(f"Test email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send test email to {recipient_email}: {str(e)}")
            return False

    @staticmethod
    def send_email_with_attachment(to_email, subject, body, attachment_path, attachment_filename, attachment_type='application/octet-stream'):
        """
        Send email with file attachment.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body text
            attachment_path (str): Path to the file to attach
            attachment_filename (str): Name for the attachment file
            attachment_type (str): MIME type of attachment
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = Message(
                subject=subject,
                recipients=[to_email],
                body=body
            )
            
            # Add attachment
            with current_app.open_resource(attachment_path, 'rb') if attachment_path.startswith('/') else open(attachment_path, 'rb') as fp:
                msg.attach(
                    attachment_filename,
                    attachment_type,
                    fp.read()
                )
            
            # Send email
            mail.send(msg)
            
            logging.info(f"Email with attachment sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email with attachment to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_email_with_multiple_attachments(to_email, subject, body, attachments):
        """
        Send email with multiple file attachments.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body text
            attachments (list): List of attachment dictionaries with keys:
                - path: str - Path to the file to attach
                - filename: str - Name for the attachment file
                - mime_type: str - MIME type of attachment
                - data: bytes (optional) - Raw file data instead of path
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = Message(
                subject=subject,
                recipients=[to_email],
                body=body
            )
            
            # Add attachments
            for attachment in attachments:
                if 'data' in attachment:
                    # Use raw data directly
                    msg.attach(
                        attachment['filename'],
                        attachment['mime_type'],
                        attachment['data']
                    )
                else:
                    # Read from file path
                    with current_app.open_resource(attachment['path'], 'rb') if attachment['path'].startswith('/') else open(attachment['path'], 'rb') as fp:
                        msg.attach(
                            attachment['filename'],
                            attachment['mime_type'],
                            fp.read()
                        )
            
            # Send email
            mail.send(msg)
            
            logging.info(f"Email with {len(attachments)} attachments sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email with attachments to {to_email}: {str(e)}")
            return False
