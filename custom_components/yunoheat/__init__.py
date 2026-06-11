"""The Yuno Energy Heat integration."""

from __future__ import annotations

import logging

from yunoheat import (
    APIConnectionError,
    AuthError,
    YunoHeatClient,
)
from yunoheat import ConfigEntryAuthFailed as YunoHeatAuthFailed

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client

from .const import CONF_TOKENS
from .coordinator import YunoHeatDataUpdateCoordinator
from .token_store import ConfigEntryTokenStore

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type YunoHeatConfigEntry = ConfigEntry[YunoHeatDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: YunoHeatConfigEntry) -> bool:
    """Set up Yuno Energy Heat from a config entry."""
    email: str = entry.data[CONF_EMAIL]
    password: str = entry.data[CONF_PASSWORD]
    session = aiohttp_client.async_get_clientsession(hass)
    token_store = ConfigEntryTokenStore(hass, entry)

    client: YunoHeatClient | None = None
    if CONF_TOKENS in entry.data:
        try:
            client = await YunoHeatClient.from_saved_tokens(
                username=email,
                password=password,
                session=session,
                token_store=token_store,
            )
        except AuthError:
            _LOGGER.debug("Saved tokens are unusable; performing a fresh login")

    if client is None:
        try:
            client = await YunoHeatClient.login(
                email, password, session=session, token_store=token_store
            )
        except YunoHeatAuthFailed as err:
            raise ConfigEntryAuthFailed(f"Invalid credentials: {err}") from err
        except (AuthError, APIConnectionError) as err:
            raise ConfigEntryNotReady(
                f"Could not connect to the Yuno Heat API: {err}"
            ) from err

    coordinator = YunoHeatDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: YunoHeatConfigEntry) -> bool:
    """Unload a Yuno Energy Heat config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
