# Architecture

This page explains how the integration is put together — useful if you want to contribute or
just understand what happens behind the sensors. All code lives in
`custom_components/yunoheat/`, and every call to the Yuno API goes through the
[`pyyunoheat`](https://pypi.org/project/pyyunoheat/) library (import name `yunoheat`).

## Data flow

```
async_setup_entry (__init__.py)
        │  build YunoHeatClient — resume from saved tokens,
        │  else fresh email/password login
        ▼
YunoHeatDataUpdateCoordinator (coordinator.py)
        │  _async_setup: resolve EntityContext (meter identifier)
        │  _async_update_data: every 6 hours fetch
        │     • open bill balance
        │     • last 60 days of usage events
        ▼
YunoHeatData dataclass  ──►  entry.runtime_data
        ▼
sensor platform (sensor.py) reads runtime_data
```

The coordinator is stored on `entry.runtime_data`, typed through the
`YunoHeatConfigEntry = ConfigEntry[YunoHeatDataUpdateCoordinator]` alias, and the sensor
platform reads from there.

## Components

### `__init__.py` — entry setup

`async_setup_entry` builds the `YunoHeatClient`. If the entry already holds saved tokens it
resumes from them; otherwise (or if those tokens are unusable) it performs a fresh
email/password login. Library errors are translated to Home Assistant's exceptions at this
boundary — `ConfigEntryAuthFailed` for bad credentials (triggering reauth) and
`ConfigEntryNotReady` for connectivity problems (triggering a retry).

### `coordinator.py` — polling

`YunoHeatDataUpdateCoordinator` extends `DataUpdateCoordinator` with a six-hour interval.

- `_async_setup` runs once before the first refresh and resolves the account's
  `EntityContext` (which carries the meter identifier).
- `_async_update_data` fetches the open bill balance and the last 60 days of usage events
  (newest first), packing them into a `YunoHeatData` dataclass (`balance`, `latest_event`,
  `recent_events`).

Because the library silently refreshes tokens and re-logs-in with stored credentials, any
`AuthError` that still surfaces here is a genuine credential failure and is raised as
`ConfigEntryAuthFailed`.

### `token_store.py` — token persistence

`ConfigEntryTokenStore` implements pyyunoheat's `TokenStore` protocol on top of
`ConfigEntry.data[CONF_TOKENS]`. This keeps the Keycloak token pair inside Home Assistant's
config entry instead of the library's default on-disk file, so tokens survive restarts and
are removed when the integration is deleted.

### `config_flow.py` — setup and reauth

A UI-only flow collects email and password, validates them with a throwaway
`InMemoryTokenStore`, and stores the resulting tokens in the entry. The entry's `unique_id`
is the Tridens `person.code`, so the same account cannot be added twice. The reauth steps
re-validate a new password and guard against pointing the entry at a different account.

### `entity.py` — the device

`YunoHeatEntity` is the shared base class. It ties every entity to one **service-type
device** whose serial number is the meter identifier from `coordinator.context`. Entity
unique IDs follow the pattern `{account_id}_{description.key}`.

### `sensor.py` — the sensors

Two kinds of sensor live here:

- **Plain sensors** are declared in the `SENSORS` tuple using the `value_fn`
  entity-description pattern. Each description carries its device class, state class, unit,
  and a function that reads its value out of `YunoHeatData`. To add a new metric, add a new
  description to this tuple.
- **`YunoHeatCumulativeSensor`** is a `RestoreSensor` that accumulates usage quantities
  client-side. Events arrive newest-first; it deduplicates against a `last_event_id` state
  attribute and processes only events with a higher ID (oldest-first), so its total keeps
  increasing monotonically and survives restarts. This is what feeds the Energy dashboard.

## The `pyyunoheat` library

The integration is a thin Home Assistant adapter over `pyyunoheat`, which owns all HTTP,
authentication, and data modelling. The version is pinned in
`custom_components/yunoheat/manifest.json`.

!!! warning "Naming trap"
    `pyyunoheat` exports its **own** `ConfigEntryAuthFailed`, which is *not* Home Assistant's
    exception of the same name. Throughout this codebase the library's exception is imported
    as `YunoHeatAuthFailed` and translated into Home Assistant's
    `ConfigEntryAuthFailed` / `ConfigEntryNotReady` / `UpdateFailed` at the boundary.
