"""DataUpdateCoordinator for the Yuno Energy Heat integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from yunoheat import (
    APIConnectionError,
    APIError,
    AuthError,
    EntityContext,
    EntityDiscoveryError,
    UsageEvent,
    YunoHeatClient,
)
from yunoheat import ConfigEntryAuthFailed as YunoHeatAuthFailed

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, USAGE_LOOKBACK_DAYS

_LOGGER = logging.getLogger(__name__)


@dataclass
class YunoHeatData:
    """Container for the data fetched from the Yuno Heat API on each refresh."""

    balance: float
    latest_event: UsageEvent | None


class YunoHeatDataUpdateCoordinator(DataUpdateCoordinator[YunoHeatData]):
    """Coordinator that polls the Yuno Heat API for balance and usage data."""

    config_entry: ConfigEntry
    context: EntityContext

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: YunoHeatClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_setup(self) -> None:
        """Resolve the account's entity context before the first refresh."""
        try:
            self.context = await self.client.get_context()
        except (YunoHeatAuthFailed, AuthError) as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (APIError, APIConnectionError, EntityDiscoveryError) as err:
            raise UpdateFailed(
                f"Error discovering the Yuno Heat account: {err}"
            ) from err

    async def _async_update_data(self) -> YunoHeatData:
        """Fetch the latest balance and meter reading from the Yuno Heat API."""
        now = dt_util.utcnow()
        try:
            bill = await self.client.get_open_bill_due()
            events = await self.client.get_usage_events(
                date_from=now - timedelta(days=USAGE_LOOKBACK_DAYS),
                date_to=now,
                count=1,
                order="desc",
            )
        except (YunoHeatAuthFailed, AuthError) as err:
            # The library already refreshes tokens and silently re-logs-in
            # with the stored credentials, so anything surfacing here is a
            # genuine credential problem that needs the reauth flow.
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (APIError, APIConnectionError, EntityDiscoveryError) as err:
            raise UpdateFailed(
                f"Error communicating with the Yuno Heat API: {err}"
            ) from err

        return YunoHeatData(
            balance=bill.open_bill_due,
            latest_event=events.objects[0] if events.objects else None,
        )
