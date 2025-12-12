import requests
from app.core.config import settings

# Load config
WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_PHONE_ID = settings.WHATSAPP_PHONE_ID
WHATSAPP_API_VERSION = settings.WHATSAPP_API_VERSION or "v21.0"

# Your templates
TEMPLATE_WELCOME = settings.WHATSAPP_TEMPLATE_WELCOME            # welcome_user_alert
TEMPLATE_FLAGGED = settings.WHATSAPP_TEMPLATE_FLAGGED            # flagged_risk_alert


BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"


# ===========================================================
# INTERNAL SENDER
# ===========================================================
def _send_template(to_phone: str, template_name: str, components=None):
    print("📌 ENTERED _send_template()", to_phone, template_name)

    # Required checks
    if not WHATSAPP_TOKEN:
        print("❌ WhatsApp TOKEN missing — aborting.")
        return
    if not WHATSAPP_PHONE_ID:
        print("❌ WhatsApp PHONE ID missing — aborting.")
        return
    if not template_name:
        print("❌ Template name missing.")
        return
    if not to_phone:
        print("❌ Phone number missing.")
        return

    # Auto format phone number
    if not to_phone.startswith("+") and not to_phone.startswith("91"):
        print("⚠ Auto-fixing phone: adding 91 prefix")
        to_phone = "91" + to_phone

    url = f"{BASE_URL}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
        },
    }

    if components:
        payload["template"]["components"] = components

    print("➡ URL:", url)
    print("➡ Payload:", payload)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print("📨 WhatsApp API response:", response.text)
        return response.json()
    except Exception as e:
        print("❌ WhatsApp API error:", e)
        return None


# ===========================================================
# 2️⃣ SEND WELCOME MESSAGE (1 variable)
# ===========================================================
def send_welcome_message(phone: str, username: str):
    print("🚀 send_welcome_message CALLED —>", phone, username)

    template_name = TEMPLATE_WELCOME

    if not template_name:
        print("❌ WHATSAPP_TEMPLATE_WELCOME not set — skipping.")
        return

    if not phone:
        print("❌ No phone number provided.")
        return

    components = [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": username},
            ],
        }
    ]


    return _send_template(phone, template_name, components)



# ===========================================================
# 3️⃣ SEND HIGH-RISK ALERT (3 variables)
# ===========================================================
def send_flagged_risk_message(phone: str, username: str, band: str, reason: str):
    print("🚨 send_flagged_risk_message CALLED —>", phone, username, band)

    template_name = TEMPLATE_FLAGGED

    if not template_name:
        print("❌ WHATSAPP_TEMPLATE_FLAGGED not set — skipping.")
        return

    if not phone:
        print("❌ No phone number provided.")
        return

    components = [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": username},
                {"type": "text", "text": band},
                {"type": "text", "text": reason},
            ],
        }
    ]

    return _send_template(phone, template_name, components)

def send_otp_message(phone: str, code: str):
    text = f"Your verification code is {code}. It is valid for 5 minutes."

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }

    url = f"{BASE_URL}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    print("➡ Sending OTP:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("📨 WhatsApp OTP response:", response.text)
    except Exception as e:
        print("❌ Error sending OTP:", e)
