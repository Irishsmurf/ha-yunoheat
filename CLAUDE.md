# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A HACS custom integration for Home Assistant exposing a Yuno Energy Heat (Irish communal-heating provider) account as sensors: balance, latest usage/cost, last meter reading, and a cumulative usage total for the Energy dashboard. Domain is `yunoheat`, all code lives in `custom_components/yunoheat/`. The integration is not endorsed by Yuno Energy.

## Commands

- Lint: `ruff check .` (the only local check; there are no tests in this repo)
- CI on every push: Ruff, hassfest, and HACS validation (`.github/workflows/`)

### Cutting a release

1. Bump `version` in `custom_components/yunoheat/manifest.json`
2. Commit and push to `main`
3. `git tag vX.Y.Z && git push origin vX.Y.Z` — the Release workflow publishes the GitHub release from the tag; HACS picks it up from there

## The pyyunoheat library

All API access goes through `pyyunoheat` (import name `yunoheat`), pinned in `manifest.json` requirements. A local editable checkout lives at `~/dev/pyyunoheat` — **check the real client API, models, and exceptions there** (its `API_REFERENCE.md` and `yunoheat/` package) rather than guessing. The locally installed version may lag the manifest pin.

Naming trap: pyyunoheat exports its own `ConfigEntryAuthFailed`, which is not Home Assistant's exception of the same name. Throughout this codebase it is imported as `YunoHeatAuthFailed` and translated into HA's `ConfigEntryAuthFailed`/`ConfigEntryNotReady`/`UpdateFailed` at the boundary.

## Architecture

Data flow: `__init__.async_setup_entry` builds a `YunoHeatClient` (resuming from saved tokens, falling back to a fresh email/password login) → `YunoHeatDataUpdateCoordinator` polls every 6 hours, fetching the open bill balance and the last 60 days of usage events into a `YunoHeatData` dataclass → stored on `entry.runtime_data` (typed via the `YunoHeatConfigEntry` alias) → sensor platform reads it.

Key design points that span files:

- **Token persistence** (`token_store.py`): `ConfigEntryTokenStore` implements pyyunoheat's TokenStore protocol on top of `ConfigEntry.data[CONF_TOKENS]`, so the Keycloak token pair survives restarts and is deleted with the entry. The library silently refreshes tokens and re-logs-in with stored credentials, so any `AuthError` that still surfaces in the coordinator is a genuine credential problem and is raised as `ConfigEntryAuthFailed` to trigger the reauth flow (`config_flow.async_step_reauth*`).
- **Account identity**: the config entry `unique_id` is the Tridens `person.code`; entity unique IDs are `{unique_id}_{description.key}`, and `entity.py` ties all entities to a single service-type device whose serial number is the meter identifier from `coordinator.context` (resolved once in `_async_setup`).
- **Sensors** (`sensor.py`): plain sensors are declared in the `SENSORS` tuple using the `value_fn` entity-description pattern — add new metrics there. `YunoHeatCumulativeSensor` is different: a `RestoreSensor` that accumulates event quantities client-side across restarts, deduplicating via a `last_event_id` state attribute (events arrive newest-first; it processes only events with a higher ID, oldest-first).

## Conventions

- `~/dev/ha-pinergy` is the style reference for this integration; follow modern HA core patterns (runtime_data, entity descriptions, translation keys in `strings.json`/`translations/`).
- Branding lives in `custom_components/yunoheat/brand/` (HACS requires this exact dir name). The editable sources are `icon.svg` (512×512), `logo.svg` and `dark_logo.svg` (2186×512, wordmark indigo `#363086` / white respectively). The wordmark is Quicksand Bold **outlined to vector paths** so the SVGs have no font dependency; to re-typeset it, install Quicksand, edit live text, then re-outline.
- The shipped PNGs must follow the HA brands image spec (PNG, transparent, **trimmed** to minimum empty space, interlaced, lossless-optimized). Each asset has a normal + hDPI pair: `icon.png` 256×256 + `icon@2x.png` 512×512 (1:1 square); `logo.png`/`dark_logo.png` 256-tall + `…@2x.png` 512-tall (landscape, shortest side at the spec max). Don't hand-edit PNGs — regenerate from the SVGs: render at high res with cairosvg, trim the alpha bbox (square the icon by padding the short side), resize to the target sizes, then `convert … -strip -interlace PNG -define png:compression-level=9` to interlace + optimize.
