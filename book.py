import requests
import datetime

# 🔧 CONFIG — replace with your details
BASE_URL = "http://desk.3mdeb.com"
USERNAME = "filip.lewinski@3mdeb.com"
PASSWORD = "Qwerty1234!"
LOCATION_ID = "1"     # numeric ID of the location (e.g. your office floor)
WORK_START = "09:00:00" # booking window
WORK_END = "17:00:00"

# 1️⃣ Authenticate to receive JWT
resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"user": USERNAME, "password": PASSWORD}
)
print("Status:", resp.status_code)
print("Response:", resp.text)
resp.raise_for_status()
token = resp.json()["token"]  # adjust field if API returns differently

headers = {"Authorization": f"Bearer {token}"}

# 2️⃣ Get spaces with availability today
today = datetime.date.today().isoformat()
availability_payload = {
    "start": f"{today}T{WORK_START}",
    "end": f"{today}T{WORK_END}"
}
resp = requests.post(
    f"{BASE_URL}/location/{LOCATION_ID}/space/availability",
    json=availability_payload,
    headers=headers
)
resp.raise_for_status()
spaces = resp.json()

# 3️⃣ Select the first available space
if not spaces:
    print("No available spaces found for today.")
    exit(1)

space = spaces[0]
space_id = space["id"]

# 4️⃣ Create a booking
booking_payload = {
    "userId": None,  # omit or include if booking for yourself; system knows current user
    "locationId": LOCATION_ID,
    "spaceId": space_id,
    "start": availability_payload["start"],
    "end": availability_payload["end"]
}

resp = requests.post(
    f"{BASE_URL}/booking",
    json=booking_payload,
    headers=headers
)
resp.raise_for_status()
print("Booked space", space_id, "from", availability_payload["start"], "to", availability_payload["end"])
