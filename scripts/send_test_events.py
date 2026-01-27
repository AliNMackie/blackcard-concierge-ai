import requests
import json
import os
import time

BACKEND_URL = "http://localhost:8080"

def send_webhook(endpoint, payload_path):
    url = f"{BACKEND_URL}/webhooks/{endpoint}"
    print(f"Sending to {url}...")
    
    try:
        with open(payload_path, 'r') as f:
            data = json.load(f)
            
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    print("--- Elite Concierge E2E Test Sender ---")
    
    # 1. Send Terra Event
    print("\n[1] Sending Terra Recovery Event (Low Score)...")
    send_webhook("terra", "backend/samples/terra_recovery_event.json")
    
    # 2. Send WhatsApp Event
    print("\n[2] Sending WhatsApp Message...")
    send_webhook("whatsapp", "backend/samples/whatsapp_message_event.json")
    
    print("\nDone. Check the Dashboards.")
