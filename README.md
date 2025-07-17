# 🪑 SeatSurfing Auto-Booking Script

Automatically reserve your preferred desk via the SeatSurfing API, either for a single day or the whole workweek.

## 🚀 Features

- Log in to your organization’s SeatSurfing instance.
- Check if a desk is available for a specific time.
- Reserve the desk automatically.
- Optionally reserve for **the full workweek** (Mon–Fri).
- All credentials and sensitive info stored in a local config file.


## 📦 Requirements

- Python 3.7+
- `requests` module (install via `pip install requests`)


## 🛠️ Setup

1. Clone this repo or copy the script locally.
2. Create a config file named `.seatsurfing_config.json` in the same directory.

### Example `.seatsurfing_config.json`:

```json
{
  "BASE_URL": "http://your.seatsurfing.app",
  "EMAIL": "your.email@domain.com",
  "PASSWORD": "your_password",
  "ORG_ID": "your-org-id-here",
  "LOCATION_ID": "your-location-id-here"
}
````

> 🔒 **Keep this file secret!** Do **not** commit it to Git.


## 🧑‍💻 Usage

### Basic: Book a desk today

```bash
python seatsurf.py "Desk 7" "16:00-18:00"
```

This will:

* Check availability for "Desk 7" today between 16:00 and 18:00 (local time).
* Book it if available.

### Full Week Booking

```bash
python seatsurf.py "Desk 7" "16:00-18:00" --week
```

This will:

* Attempt to book "Desk 7" for each weekday (Mon–Fri) this week between 16:00 and 18:00.
* Continue even if some days are unavailable.


## ⚠️ Notes

* Desk names must match **exactly** as listed in the SeatSurfing UI (e.g. `"Desk 7"`).
* Time format must be `HH:MM-HH:MM` in **24-hour format**.
* All times are assumed to be in **your local time**, but will be converted to UTC with `"Z"` suffix.


## 🧩 Future Ideas

* List all available desks (`--list`)
* Auto-pick any available desk
* Configurable subject line
* Timezone handling


## 🛡 License

MIT License. Use responsibly and don’t overload shared booking systems.

