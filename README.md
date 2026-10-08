# YQT Smart

Unofficial Home Assistant integration and Python client for GPS kids' smartwatches that use the YQT Smart cloud. The same backend powers white-label apps such as SeTracker, SeTracker 2 and CarePro+, so watches paired with those apps should work too.

Log in with the same account you use in the phone app. API details are documented in [`REVERSE_ENGINEERING.md`](REVERSE_ENGINEERING.md).

## Compatible watches

Confirmed working:

- FREEBOT `T53` ([Amazon](https://www.amazon.com/FREEBOT-Parental-Controls-Emergency-Birthday/dp/B0DRBPY8QC?th=1&linkCode=ll2&tag=nivadema-20&language=en_US&ref_=as_li_ss_tl))
- PTHTECHUS `PTH-G4-S02` ([Amazon](https://www.amazon.com/dp/B09198QYX8?th=1&linkCode=ll2&tag=nivadema-20&language=en_US&ref_=as_li_ss_tl))
- PTHTECHUS `PTH-G4-S07` ([Amazon](https://www.amazon.com/dp/B0B12MC8FP?th=1&linkCode=ll2&tag=nivadema-20&language=en_US&ref_=as_li_ss_tl))
- Tixpc `G31` ([Amazon](https://www.amazon.com/dp/B0DJVSDGT5?th=1&linkCode=ll2&tag=nivadema-20&language=en_US&ref_=as_li_ss_tl))
- tykjszgs `LT31` ([Amazon](https://www.amazon.com/dp/B0CZ6G69WY?th=1&linkCode=ll2&tag=nivadema-20&language=en_US&ref_=as_li_ss_tl))
- Wonlex `KT31` ([Wonlex](https://www.iwonlex.net/products/wonlex-4g-amoled-screen-gps-android-8-1-kids-videocall-smartwatch-kt31/))
- `GTQ68NO` ([montre-enfant.com](https://www.montre-enfant.com/produit/traceur-gps-enfant-4g-avec-bouton-d-appel-sos-modele-gtq68no))
- Garett Kids `Vibe AI 4G` ([garett.com.pl](https://garett.com.pl/produkt/smartwatch-garett-kids-vibe-ai-4g-czarny/))

## Home Assistant

### Install via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Kasperbi&repository=yqt-smart-api&category=integration)

1. Add this repository to HACS as a custom repository (category `Integration`).
2. Install `YQT Smart` and restart Home Assistant.

### Install manually

Copy `custom_components/yqt` into your Home Assistant `custom_components` directory and restart.

### Setup

Go to **Settings → Devices & services → Add integration**, search for `YQT Smart`, and enter your region, account and password.

Each watch becomes a device with:

- a `device_tracker` with the last known position
- battery, last-fix and speed sensors
- a stale-location binary sensor
- a button to request a fresh location
- diagnostic sensors for nearby Wi-Fi access points and cell towers (disabled by default)
- a Do Not Disturb schedule sensor. It reads the watch's shared settings
  endpoint, traced from APK analysis and confirmed working against a live
  device as of 2026-10-08. It can still legitimately show "Unknown" on a
  watch/account where the response doesn't match -- the raw server response
  is always available as an attribute on the sensor.

The integration also registers a **`yqt.set_dnd_schedule`** service to write
the schedule, usable from Developer Tools, scripts, or automations:

```yaml
action: yqt.set_dnd_schedule
target:
  device_id: YOUR_WATCH_DEVICE_ID
data:
  periods:
    - "22:00-07:00:mon,tue,wed,thu,fri"
```

Omit `periods` entirely (or pass an empty list) to clear/disable the
schedule. Only works for current-generation (`DC == 2`) watches; traced from
APK analysis and confirmed working against a live device as of 2026-10-08 --
see [`REVERSE_ENGINEERING.md`](REVERSE_ENGINEERING.md) for details.

## Command-line client

With [uv](https://docs.astral.sh/uv/) installed:

```bash
./yqt_client.py --region europe --account YOUR_EMAIL --password YOUR_PASSWORD devices
./yqt_client.py --region europe --account YOUR_EMAIL --password YOUR_PASSWORD last-position --did YOUR_DEVICE_ID
./yqt_client.py --region europe --account YOUR_EMAIL --password YOUR_PASSWORD fresh-position --did YOUR_DEVICE_ID
./yqt_client.py --region europe --account YOUR_EMAIL --password YOUR_PASSWORD find-settings --did YOUR_DEVICE_ID
./yqt_client.py --region europe --account YOUR_EMAIL --password YOUR_PASSWORD set-dnd --did YOUR_DEVICE_ID --period 22:00-07:00:mon,tue,wed,thu,fri
```

Run `./yqt_client.py --help` for all commands. The CLI and integration share the same code in `custom_components/yqt/core/`.

`set-dnd` writes the Do Not Disturb schedule for current-generation (`DC == 2`)
watches; it's traced from APK analysis and confirmed working against a live
device as of 2026-10-08 -- see [`REVERSE_ENGINEERING.md`](REVERSE_ENGINEERING.md)
and [issue #13](https://github.com/Niek/yqt-smart-api/issues/13). Omit
`--period` entirely to clear/disable the schedule.

## Disclaimer

Not affiliated with YQT or any watch vendor. The vendor can change the API at any time, which may break this project.
