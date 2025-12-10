import requests
from app.core.config import settings

# Load config
WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_PHONE_ID = settings.WHATSAPP_PHONE_ID
WHATSAPP_API_VERSION = settings.WHATSAPP_API_VERSION or "v21.0"

# Your templates
TEMPLATE_WELCOME = settings.WHATSAPP_TEMPLATE_WELCOME            # user_welcome_alert
TEMPLATE_FLAGGED = settings.WHATSAPP_TEMPLATE_FLAGGED            # risk_high_alert

# Temporary – WhatsApp default template
TEMPLATE_HELLO = "hello_world"  

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
            "language": {"code": "en_US"},
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
# 1️⃣ SEND DEFAULT "HELLO WORLD" TEMPLATE (0 variables)
# ===========================================================
def send_hello_world(phone: str):
    print("🚀 send_hello_world CALLED →", phone)

    return _send_template(
        phone,
        TEMPLATE_HELLO,
        components=None    # hello_world takes **zero** variables
    )


# ===========================================================
# 2️⃣ SEND WELCOME MESSAGE (1 variable)
# ===========================================================
# def send_welcome_message(phone: str, username: str):
#     print("🚀 send_welcome_message CALLED —>", phone, username)

#     template_name = TEMPLATE_WELCOME or TEMPLATE_HELLO

#     if not phone:
#         print("❌ No phone number provided.")
#         return

#     components = [
#         {
#             "type": "body",
#             "parameters": [
#                 {"type": "text", "text": username},
#             ],
#         }
#     ]

#     return _send_template(phone, template_name, components)


# For now priority to the helo world template since others are not approved
def send_welcome_message(phone: str, username: str):
    print("🚀 send_welcome_message CALLED —>", phone, username)

    template_name = TEMPLATE_WELCOME or TEMPLATE_HELLO

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

    # If using hello_world → no components allowed
    if template_name == "hello_world":
        return _send_template(phone, template_name, components=None)

    return _send_template(phone, template_name, components)



# ===========================================================
# 3️⃣ SEND HIGH-RISK ALERT (3 variables)
# ===========================================================
# def send_flagged_risk_message(phone: str, username: str, band: str, reason: str):
#     print("🚨 send_flagged_risk_message CALLED —>", phone, username, band)

#     template_name = TEMPLATE_FLAGGED or TEMPLATE_HELLO

#     if not phone:
#         print("❌ No phone number provided.")
#         return

#     components = [
#         {
#             "type": "body",
#             "parameters": [
#                 {"type": "text", "text": username},
#                 {"type": "text", "text": band},
#                 {"type": "text", "text": reason},
#             ],
#         }
#     ]

#     return _send_template(phone, template_name, components)


# For now priority to the helo world template since others are not approved
def send_flagged_risk_message(phone: str, username: str, band: str, reason: str):
    print("🚨 send_flagged_risk_message CALLED —>", phone, username, band)

    template_name = TEMPLATE_FLAGGED or TEMPLATE_HELLO

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

    # hello_world cannot accept variables → force no components
    if template_name == "hello_world":
        return _send_template(phone, template_name, components=None)

    return _send_template(phone, template_name, components)
