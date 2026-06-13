# Yuno Energy Heat

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark_logo.png">
  <img alt="Yuno Energy Heat" src="assets/logo.png" height="56">
</picture>

A [Home Assistant](https://www.home-assistant.io/) custom integration that brings your
**Yuno Energy Heat** communal-heating account into Home Assistant as sensors.

!!! note "Unofficial integration"
    This is a community-built integration. It is **not** affiliated with, endorsed by, or
    supported by Yuno Energy.

## What it does

[Yuno Energy](https://yunoenergy.ie/) Heat is an Irish communal-heating provider. This
integration logs into your account, polls it every six hours, and exposes the data as a
single Home Assistant device with sensors for:

- **Outstanding balance** — the amount currently due on your open bill.
- **Latest usage** and **latest cost** — energy and spend for the most recent reading period.
- **Last reading** — when the most recent meter reading was taken.
- **Meter reading** — the cumulative register value from that reading.
- **Cumulative usage** — a client-side running total, ready for the
  [Energy dashboard](https://www.home-assistant.io/docs/energy/).

## Where to go next

<div class="grid cards" markdown>

- :material-book-open-variant: **[User guide](user-guide.md)**

    Install via HACS, connect your account, and add the sensors to the Energy dashboard.

- :material-sitemap: **[Architecture](architecture.md)**

    How the integration is wired together — the coordinator, token persistence, and the
    cumulative sensor.

- :material-hammer-wrench: **[Contributing](contributing.md)**

    Development setup, linting, and how releases are cut.

</div>

## At a glance

| | |
| --- | --- |
| Domain | `yunoheat` |
| Integration type | Service (cloud polling) |
| Configuration | UI config flow (email + password) |
| Poll interval | Every 6 hours |
| API library | [`pyyunoheat`](https://pypi.org/project/pyyunoheat/) |
| Minimum Home Assistant | 2025.1.0 |
