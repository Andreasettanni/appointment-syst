from twilio.rest import Client
from config import Config

def send_whatsapp_notification(to_number, message):
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    
    try:
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{Config.TWILIO_PHONE_NUMBER}',
            to=f'whatsapp:{to_number}'
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False
