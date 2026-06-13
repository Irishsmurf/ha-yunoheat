# User guide

This guide walks you through installing the integration, connecting your Yuno Energy
account, understanding the sensors it creates, and wiring usage into the Energy dashboard.

## Prerequisites

- Home Assistant **2025.1.0** or newer.
- An active **Yuno Energy Heat** account, with the email and password you use to sign in to
  the [Yuno Energy portal](https://yunoenergy.ie/).
- [HACS](https://hacs.xyz/) installed (recommended), or filesystem access to your Home
  Assistant `config` directory for a manual install.

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations → ⋮ (top right) → Custom repositories**.
2. Add the repository URL `https://github.com/Irishsmurf/ha-yunoheat` and choose the
   category **Integration**.
3. Find the **Yuno Energy Heat** card and click **Download**.
4. Restart Home Assistant.

### Manual install

1. Download or clone this repository.
2. Copy the `custom_components/yunoheat` directory into your Home Assistant
   `config/custom_components` directory, so you end up with
   `config/custom_components/yunoheat/`.
3. Restart Home Assistant.

## Adding the integration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Yuno Energy Heat**.
3. Enter the **email** and **password** for your Yuno Energy account and submit.

The integration logs in, discovers your account, and creates a single device with all of
the sensors below.

!!! tip "One account per entry"
    Each config entry is keyed to one Yuno Energy account. Adding the same account twice is
    blocked; to track multiple accounts, add the integration once per set of credentials.

### If sign-in fails

| Message | Meaning | What to do |
| --- | --- | --- |
| *Invalid email address or password* | The credentials were rejected. | Double-check them in the Yuno Energy portal and try again. |
| *Failed to connect to the Yuno Heat API* | The API was unreachable. | Check your internet connection and retry; the service may be temporarily down. |

## The sensors

All sensors belong to one device named **Yuno Heat**. The device's serial number is your
meter identifier.

| Sensor | Unit | State class | Notes |
| --- | --- | --- | --- |
| **Outstanding balance** | € | Total | Amount due on the open bill. |
| **Latest usage** | kWh | Total | Energy used in the most recent reading period. |
| **Latest cost** | € | Total | Cost of that period, after any discount. |
| **Last reading** | — | — | Timestamp of the most recent meter reading. |
| **Meter reading** | kWh | Total increasing | Cumulative meter register from the latest reading. |
| **Cumulative usage** | kWh | Total increasing | Client-side running total of usage events. |

A reading is unavailable (the sensor shows *unknown*) until the account reports its first
usage event within the lookback window.

## Adding usage to the Energy dashboard

The **Cumulative usage** sensor is designed for the
[Energy dashboard](https://www.home-assistant.io/docs/energy/):

1. Open **Settings → Dashboards → Energy**.
2. Add `sensor.yuno_heat_cumulative_usage` under **Gas/Heating consumption** or as an
   **Individual device**.
3. To track spend alongside it, you can graph **Latest cost** on a regular dashboard card.

!!! info "Why a separate cumulative sensor?"
    The Yuno API only returns a rolling window of recent usage *events*, not a single
    ever-increasing total. The cumulative sensor adds up each new event and remembers the
    running total across restarts, giving the Energy dashboard the monotonic
    `total_increasing` value it expects. See [Architecture](architecture.md) for the
    details.

## Re-authentication

Your Keycloak login tokens are stored inside the config entry and refreshed automatically,
so you normally never re-enter your password. If you change your Yuno Energy password,
Home Assistant raises a **re-authentication** notification — open it and enter your new
password to restore the connection.

## Removing the integration

Delete the integration from **Settings → Devices & Services**. This removes the device, all
of its sensors, and the stored login tokens.
