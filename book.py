#!/usr/bin/python3

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

def login(base_url, email, password, org_id):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
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

def check_availability_and_get_id(base_url, location_id, desk_label, enter, leave, access_token):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "Origin": base_url,
        "Referer": f"{base_url}/ui/search/",
        "User-Agent": "Mozilla/5.0"
    }

    params = {"enter": enter, "leave": leave}
    url = f"{base_url}/location/{location_id}/space/availability?{urlencode(params)}"
    resp = requests.get(url, headers=headers)
    print(f"🔍 Availability check for {enter[:10]} → {resp.status_code}")
    resp.raise_for_status()

    spaces = resp.json()

    for space in spaces:
        name = space.get("name") or ""
        if name.lower() == desk_label.lower() and space.get("available") and space.get("allowed", True):
            print(f"✅ '{desk_label}' is available on {enter[:10]}")
            return space["id"]

    print(f"❌ '{desk_label}' is NOT available on {enter[:10]}")
    return None

def make_reservation(base_url, desk_id, desk_label, enter, leave, access_token, subject="skibidooobi"):
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
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
    print(f"📡 Booking on {enter[:10]} status: {resp.status_code}")
    print("📨 Response:", resp.text)
    resp.raise_for_status()
    print(f"✅ Successfully booked '{desk_label}' on {enter[:10]} from {enter[-13:-8]} to {leave[-13:-8]}.")

def parse_time_range(time_str, day):
    try:
        start_str, end_str = time_str.split("-")
        enter = f"{day.isoformat()}T{start_str}:00.000Z"
        leave = f"{day.isoformat()}T{end_str}:00.000Z"
        return enter, leave
    except ValueError:
        print("❌ Invalid time format. Use HH:MM-HH:MM (e.g. 16:00-18:00)")
        sys.exit(1)

def get_weekdays(start_day, count=5):
    """Get next `count` weekdays starting from `start_day`"""
    weekdays = []
    current = start_day
    while len(weekdays) < count:
        if current.weekday() < 5:  # Monday=0, Sunday=6
            weekdays.append(current)
        current += datetime.timedelta(days=1)
    return weekdays

def parse_day_argument(day_str):
    try:
        parts = day_str.strip().split(".")
        if len(parts) not in [2, 3]:
            raise ValueError("Invalid number of components")

        day = int(parts[0])
        month = int(parts[1])
        today = datetime.date.today()

        if len(parts) == 3:
            year = int(parts[2])
        else:
            year = today.year
            try_date = datetime.date(year, month, day)
            if try_date < today:
                # If the date already passed this year, assume next year
                year += 1

        return datetime.date(year, month, day)

    except ValueError:
        print("❌ Invalid day format. Use DD.MM or DD.MM.YYYY (e.g., 01.01 or 01.01.2025)")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="SeatSurfing auto-booking tool")
    parser.add_argument("desk_label", help="Label of the desk to reserve (e.g. 'Desk 7')")
    parser.add_argument("time_range", help="Time range (e.g. '16:00-18:00')")
    parser.add_argument("--week", action="store_true", help="Reserve the desk for the full week (Mon–Fri)")
    parser.add_argument("--day", help="Specify the day (DD.MM or D.M) to reserve instead of today")

    args = parser.parse_args()
    desk_label = args.desk_label
    time_range = args.time_range
    full_week = args.week
    override_day = parse_day_argument(args.day) if args.day else None

    config = load_config()

    BASE_URL = config["BASE_URL"]
    EMAIL = config["EMAIL"]
    PASSWORD = config["PASSWORD"]
    ORG_ID = config["ORG_ID"]
    LOCATION_ID = config["LOCATION_ID"]

    if not check_api_alive(BASE_URL):
        sys.exit(1)

    access_token = login(BASE_URL, EMAIL, PASSWORD, ORG_ID)

    if full_week:
        start_day = override_day or datetime.date.today()
        days = get_weekdays(start_day)

        print(f"\n📅 Attempting to reserve '{desk_label}' for the full week starting {start_day.isoformat()}...\n")
        for day in days:
            enter, leave = parse_time_range(time_range, day)
            desk_id = check_availability_and_get_id(BASE_URL, LOCATION_ID, desk_label, enter, leave, access_token)
            if desk_id:
                try:
                    make_reservation(BASE_URL, desk_id, desk_label, enter, leave, access_token)
                except Exception as e:
                    print(f"❌ Booking failed on {day.isoformat()}: {e}")
            else:
                print(f"⚠️ Skipping {day.isoformat()} — desk not available.\n")
    else:
        day = override_day or datetime.date.today()
        enter, leave = parse_time_range(time_range, day)
        desk_id = check_availability_and_get_id(BASE_URL, LOCATION_ID, desk_label, enter, leave, access_token)
        if desk_id:
            make_reservation(BASE_URL, desk_id, desk_label, enter, leave, access_token)

if __name__ == "__main__":
    main()
