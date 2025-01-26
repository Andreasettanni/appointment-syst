# app/services/whatsapp.py
from app.extensions import db
from app.models.appointment import Notification
import requests
from datetime import datetime

class WhatsAppService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID"

    def send_appointment_reminder(self, appointment):
        notification = Notification(
            type='whatsapp',
            appointment_id=appointment.id,
            message=f"Promemoria: hai un appuntamento il {appointment.datetime}"
        )

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": appointment.client.phone,
                    "type": "template",
                    "template": {
                        "name": "appointment_reminder",
                        "language": {
                            "code": "it"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": appointment.datetime.strftime("%d/%m/%Y %H:%M")
                                    }
                                ]
                            }
                        ]
                    }
                }
            )

            if response.status_code == 200:
                notification.status = 'sent'
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = 'failed'

        except Exception as e:
            notification.status = 'failed'
            print(f"Error sending WhatsApp notification: {str(e)}")

        db.session.add(notification)
        db.session.commit()