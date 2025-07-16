import json
import requests
import datetime
from urllib.parse import urlencode
import os
import sys

CONFIG_PATH = ".seatsurfing_config.json"

def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        print(f"❌ Config file '{path}' not found. Exiting.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)

def check_api_alive(base_url):
    test_endpoints = ["/auth/ping", "/location", "/swagger", "/"]
    print("🔍 Probing API endpoints...")
    for path in test_endpoints:
        try:
            resp = requests.get(base_url + path, timeout=5)
            print(f"GET {path} → {resp.status_code}")
            if resp.status_code == 200:
                print("✅ API appears responsive.")
                return True
        except Exception as e:
            print(f"GET {path} → ❌ {e}")
    print("❌ API seems unreachable or not behaving as expected.")
    return False

def login(base_url, email, password, org_id, cookie):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/login/",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Cookie": cookie
    }

    payload = {
        "email": email,
        "password": password,
        "organizationId": org_id,
        "longLived": False
    }

    resp = requests.post(f"{base_url}/auth/login", headers=headers, json=payload)
    resp.raise_for_status()
    access_token = resp.json()["accessToken"]
    print("✅ Logged in! Access token:", access_token[:20], "…")
    return access_token

def check_availability(base_url, location_id, desk_id, desk_label, enter, leave, access_token, cookie):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "authorization": f"Bearer {access_token}"
    }

    params = {"enter": enter, "leave": leave}
    url = f"{base_url}/location/{location_id}/space/availability?{urlencode(params)}"

    resp = requests.get(url, headers=headers)
    print("🔍 Availability check status:", resp.status_code)
    resp.raise_for_status()

    spaces = resp.json()

    matching_spaces = [
        s for s in spaces
        if s["id"] == desk_id and s.get("available") and s.get("allowed", True)
    ]

    if not matching_spaces:
        print(f"❌ '{desk_label}' is not available between {enter} and {leave}.")
        return False

    print(f"✅ '{desk_label}' is available!")
    return True

def make_reservation(base_url, desk_id, desk_label, enter, leave, access_token, cookie, subject="skibidooobi"):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "authorization": f"Bearer {access_token}"
    }

    booking_payload = {
        "enter": enter,
        "leave": leave,
        "spaceId": desk_id,
        "subject": subject,
        "userEmail": ""  # Optional if already logged in
    }

    resp = requests.post(f"{base_url}/booking/", json=booking_payload, headers=headers)
    print("📡 Booking status:", resp.status_code)
    print("📨 Response:", resp.text)
    resp.raise_for_status()
    print(f"✅ Successfully booked '{desk_label}' from {enter} to {leave}.")

def main():
    config = load_config()

    BASE_URL = config["BASE_URL"]
    EMAIL = config["EMAIL"]
    PASSWORD = config["PASSWORD"]
    ORG_ID = config["ORG_ID"]
    LOCATION_ID = config["LOCATION_ID"]
    COOKIE = config["COOKIE"]
    DESK_ID = config["TARGET_SPACE_ID"]
    DESK_LABEL = config["TARGET_SPACE_LABEL"]

    today = datetime.date.today().isoformat()
    enter = f"{today}T16:00:00.000Z"
    leave = f"{today}T17:59:59.000Z"

    if not check_api_alive(BASE_URL):
        exit(1)

    access_token = login(BASE_URL, EMAIL, PASSWORD, ORG_ID, COOKIE)

    if check_availability(BASE_URL, LOCATION_ID, DESK_ID, DESK_LABEL, enter, leave, access_token, COOKIE):
        make_reservation(BASE_URL, DESK_ID, DESK_LABEL, enter, leave, access_token, COOKIE)

if __name__ == "__main__":
    main()
