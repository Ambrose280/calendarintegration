import os
import httpx

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "dummy_key")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "test@example.com")

async def send_reminder_email(to_email: str, to_name: str, meeting_time: str):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #f4f4f5; padding: 20px; }}
            .container {{ background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); max-width: 600px; margin: 0 auto; }}
            .header {{ color: #2563eb; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
            .content {{ color: #3f3f46; font-size: 16px; line-height: 1.5; }}
            .footer {{ margin-top: 30px; font-size: 14px; color: #71717a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Meeting Reminder</div>
            <div class="content">
                <p>Hi {to_name},</p>
                <p>This is a friendly reminder for your upcoming meeting scheduled at <strong>{meeting_time}</strong>.</p>
                <p>We look forward to speaking with you!</p>
            </div>
            <div class="footer">
                <p>Thank you,<br>Booking System</p>
            </div>
        </div>
    </body>
    </html>
    """

    payload = {
        "sender": {"name": "Booking System", "email": SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": "Upcoming Meeting Reminder",
        "htmlContent": html_content
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        return response.status_code == 201
