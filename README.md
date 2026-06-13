<img src="custom_components/yunoheat/brand/icon.png" alt="Yuno Energy Heat icon" align="right" width="96">

# Yuno Energy Heat

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/yunoheat/brand/dark_logo.png">
  <img alt="Yuno Energy Heat" src="custom_components/yunoheat/brand/logo.png" height="56">
</picture>

A [Home Assistant](https://www.home-assistant.io/) custom integration that brings your
[Yuno Energy Heat](https://yunoenergy.ie/) communal-heating account into Home Assistant as
sensors — your outstanding balance, latest usage and cost, the last meter reading, and a
cumulative total ready for the [Energy dashboard](https://www.home-assistant.io/docs/energy/).

[![Documentation](https://img.shields.io/badge/docs-irishsmurf.github.io-363086.svg)](https://irishsmurf.github.io/ha-yunoheat/)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-363086.svg)](https://hacs.xyz/)
[![Validate](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/validate.yaml/badge.svg)](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/validate.yaml)
[![Hassfest](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/hassfest.yaml)
[![Lint](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/lint.yaml/badge.svg)](https://github.com/Irishsmurf/ha-yunoheat/actions/workflows/lint.yaml)

> [!NOTE]
> This is an unofficial, community-built integration. It is **not** affiliated with,
> endorsed by, or supported by Yuno Energy.

---

## Features

Yuno Energy Heat is an Irish communal-heating provider. Your account exposes a balance, a
running stream of metered usage "events", and a meter register. This integration polls that
account every 6 hours and surfaces it as a single Home Assistant **device** with the
following sensors:

| Sensor | Entity ID | Device class | Description |
| --- | --- | --- | --- |
| Outstanding balance | `sensor.yuno_heat_outstanding_balance` | Monetary (€) | The amount currently due on your open bill. |
| Latest usage | `sensor.yuno_heat_latest_usage` | Energy (kWh) | Energy consumed in the most recent reading period. |
| Latest cost | `sensor.yuno_heat_latest_cost` | Monetary (€) | Cost of the most recent reading period (after any discount). |
| Last reading | `sensor.yuno_heat_last_reading` | Timestamp | When the most recent meter reading was taken. |
| Meter reading | `sensor.yuno_heat_meter_reading` | Energy (kWh) | The cumulative register value from the most recent reading. |
| Cumulative usage | `sensor.yuno_heat_cumulative_usage` | Energy (kWh) | Client-side running total of usage events, suitable for the Energy dashboard. |

Because each metric carries the correct device class and state class, the energy sensors
plug straight into the Energy dashboard and long-term statistics.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS → Integrations → ⋮ (top right) → Custom repositories**.
2. Add `https://github.com/Irishsmurf/ha-yunoheat` with the category **Integration**.
3. Search for **Yuno Energy Heat** and click **Download**.
4. Restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Irishsmurf&repository=ha-yunoheat&category=integration)

### Manual

1. Copy the `custom_components/yunoheat` directory into your Home Assistant
   `config/custom_components` directory.
2. Restart Home Assistant.

## Configuration

Configuration is entirely UI-driven — no YAML required.

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Yuno Energy Heat**.
3. Enter the **email** and **password** you use to sign in to the Yuno Energy portal.

The integration logs in, discovers your account, and creates the device and sensors. Your
login tokens are stored inside the config entry so they survive restarts; if your password
ever changes, Home Assistant prompts you to re-authenticate.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yunoheat)

## Adding to the Energy dashboard

Use the **Cumulative usage** sensor to track Yuno heat consumption over time:

1. Open **Settings → Dashboards → Energy**.
2. Under **Gas/Heating consumption** (or **Individual devices**), add
   `sensor.yuno_heat_cumulative_usage`.
3. Optionally attach the **Latest cost** sensor to track spend.

The cumulative sensor accumulates each new usage event client-side and restores its total
across restarts, so it keeps a monotonic increasing value even though the API only returns a
rolling window of recent events.

## Documentation

📖 **Full documentation is published at <https://irishsmurf.github.io/ha-yunoheat/>** — a
user guide, the architecture overview, and contribution instructions. The sources live in
[`docs/`](docs/) and are built as a [MkDocs](https://www.mkdocs.org/) site. To preview it
locally:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## Contributing

Issues and pull requests are welcome. The short version:

```bash
ruff check .   # the only local check; there are no tests
```

CI runs Ruff, [hassfest](https://developers.home-assistant.io/docs/creating_component_index/),
and HACS validation on every push. See [`docs/contributing.md`](docs/contributing.md) for the
full development and release workflow.

## Credits

- All API access goes through the [`pyyunoheat`](https://pypi.org/project/pyyunoheat/) library.
- Built following modern Home Assistant integration patterns (config entries, data update
  coordinators, entity descriptions, and translation keys).
