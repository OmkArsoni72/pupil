
import requests

# ✅ Scheduler to self-ping every 10 minutes
def self_ping():
    try:
        res = requests.get("https://backend-jpaq.onrender.com")
        print("Self ping successful")
    except Exception as e:
        print("Self ping failed:", e)