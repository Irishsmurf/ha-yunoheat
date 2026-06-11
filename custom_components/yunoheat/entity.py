"""Base entity for the Yuno Energy Heat integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import YunoHeatDataUpdateCoordinator


class YunoHeatEntity(CoordinatorEntity[YunoHeatDataUpdateCoordinator]):
    """Common base class tying all entities to the Yuno Heat account device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: YunoHeatDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        account_id = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{account_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(account_id))},
            name="Yuno Heat",
            manufacturer=MANUFACTURER,
            model="Communal Heat Account",
            serial_number=coordinator.context.meter_identifier,
            entry_type=DeviceEntryType.SERVICE,
        )
