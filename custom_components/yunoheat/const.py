"""Constants for the Yuno Energy Heat integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "yunoheat"

MANUFACTURER: Final = "Yuno Energy"

DEFAULT_SCAN_INTERVAL: Final = timedelta(hours=6)

# Key inside ConfigEntry.data holding the TokenData.to_dict() payload.
CONF_TOKENS: Final = "tokens"

# How far back to look when querying for the most recent meter reading.
USAGE_LOOKBACK_DAYS: Final = 60
