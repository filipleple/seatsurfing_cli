import json
import requests
import datetime
from urllib.parse import urlencode
import os
import sys
import argparse

CONFIG_PATH = ".seatsurfing_config.json"

def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        print(f"❌ Config file '{path}' not found.")
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
    print("❌ API seems unreachable.")
    return False

def login(base_url, email, password, org_id, cookie):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "Origin": base_url,
        "Referer": f"{base_url}/ui/login/",
        "User-Agent": "Mozilla/5.0"
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

def check_availability_and_get_id(base_url, location_id, desk_label, enter, leave, access_token, cookie):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "authorization": f"Bearer {access_token}",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "User-Agent": "Mozilla/5.0"
    }

    params = {"enter": enter, "leave": leave}
    url = f"{base_url}/location/{location_id}/space/availability?{urlencode(params)}"
    resp = requests.get(url, headers=headers)
    print("🔍 Availability check status:", resp.status_code)
    resp.raise_for_status()

    spaces = resp.json()

    print(f"\n🪑 All desks between {enter} and {leave}:\n")
    for space in spaces:
        print(f"- {space.get('name')} | available={space.get('available')} | allowed={space.get('allowed')} | id={space.get('id')}")

    for space in spaces:
        if space.get("name") == desk_label and space.get("available") and space.get("allowed", True):
            print(f"\n✅ Found available match for '{desk_label}'")
            return space["id"]

    print(f"\n❌ No available match found for label: '{desk_label}'")
    return None

def make_reservation(base_url, desk_id, desk_label, enter, leave, access_token, cookie, subject="skibidooobi"):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "authorization": f"Bearer {access_token}",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "User-Agent": "Mozilla/5.0"
    }

    booking_payload = {
        "enter": enter,
        "leave": leave,
        "spaceId": desk_id,
        "subject": subject,
        "userEmail": ""
    }

    resp = requests.post(f"{base_url}/booking/", json=booking_payload, headers=headers)
    print("📡 Booking status:", resp.status_code)
    print("📨 Response:", resp.text)
    resp.raise_for_status()
    print(f"✅ Successfully booked '{desk_label}' from {enter} to {leave}.")


def parse_time_range(time_str):
    try:
        start_str, end_str = time_str.split("-")
        today = datetime.date.today().isoformat()
        enter = f"{today}T{start_str}:00.000Z"
        leave = f"{today}T{end_str}:00.000Z"
        return enter, leave
    except ValueError:
        print("❌ Invalid time format. Use HH:MM-HH:MM (e.g. 16:00-18:00)")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="SeatSurfing auto-booking tool")
    parser.add_argument("desk_label", help="Label of the desk to reserve (e.g. 'Desk 7')")
    parser.add_argument("time_range", help="Time range (e.g. '16:00-18:00')")

    args = parser.parse_args()
    desk_label = args.desk_label
    time_range = args.time_range

    enter, leave = parse_time_range(time_range)
    config = load_config()

    BASE_URL = config["BASE_URL"]
    EMAIL = config["EMAIL"]
    PASSWORD = config["PASSWORD"]
    ORG_ID = config["ORG_ID"]
    LOCATION_ID = config["LOCATION_ID"]
    COOKIE = config["COOKIE"]

    if not check_api_alive(BASE_URL):
        sys.exit(1)

    access_token = login(BASE_URL, EMAIL, PASSWORD, ORG_ID, COOKIE)
    desk_id = check_availability_and_get_id(BASE_URL, LOCATION_ID, desk_label, enter, leave, access_token, COOKIE)

    if desk_id:
        make_reservation(BASE_URL, desk_id, desk_label, enter, leave, access_token, COOKIE)

if __name__ == "__main__":
    main()
