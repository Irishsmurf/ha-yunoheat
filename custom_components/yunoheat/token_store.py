"""Token storage bridge persisting pyyunoheat tokens in the config entry."""

from __future__ import annotations

import logging

from yunoheat import TokenData

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKENS

_LOGGER = logging.getLogger(__name__)


class ConfigEntryTokenStore:
    """pyyunoheat TokenStore that reads/writes tokens in ConfigEntry data.

    Keeps the Keycloak token pair inside Home Assistant's config entry
    storage instead of the library's default file on disk, so tokens
    survive restarts and are removed together with the integration.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the store for a config entry."""
        self._hass = hass
        self._entry = entry

    async def load(self) -> TokenData | None:
        """Return tokens from the config entry, or None if absent/invalid."""
        data = self._entry.data.get(CONF_TOKENS)
        if data is None:
            return None
        try:
            return TokenData.from_dict(data)
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.warning("Discarding invalid saved tokens: %s", err)
            return None

    async def save(self, tokens: TokenData) -> None:
        """Persist refreshed tokens back into the config entry."""
        self._hass.config_entries.async_update_entry(
            self._entry,
            data={**self._entry.data, CONF_TOKENS: tokens.to_dict()},
        )
