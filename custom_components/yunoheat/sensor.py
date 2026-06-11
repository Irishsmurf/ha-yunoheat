"""Sensor platform for the Yuno Energy Heat integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import YunoHeatConfigEntry
from .coordinator import YunoHeatData, YunoHeatDataUpdateCoordinator
from .entity import YunoHeatEntity


@dataclass(frozen=True, kw_only=True)
class YunoHeatSensorEntityDescription(SensorEntityDescription):
    """Describes a Yuno Heat sensor entity."""

    value_fn: Callable[[YunoHeatData], StateType | datetime]


def _latest_usage_kwh(data: YunoHeatData) -> float | None:
    """Return the kWh consumed in the most recent reading period."""
    if data.latest_event is None:
        return None
    return data.latest_event.quantity


def _latest_cost(data: YunoHeatData) -> float | None:
    """Return the cost of the most recent reading period."""
    if data.latest_event is None:
        return None
    return data.latest_event.amount_with_discount


def _last_reading_at(data: YunoHeatData) -> datetime | None:
    """Return the timestamp of the most recent meter reading."""
    if data.latest_event is None:
        return None
    if data.latest_event.fields and data.latest_event.fields.time_of_read_dt:
        return data.latest_event.fields.time_of_read_dt
    return data.latest_event.created_at_dt


def _meter_reading_kwh(data: YunoHeatData) -> float | None:
    """Return the cumulative meter register from the most recent reading."""
    if data.latest_event is None or data.latest_event.fields is None:
        return None
    return data.latest_event.fields.meter_value_kwh


SENSORS: tuple[YunoHeatSensorEntityDescription, ...] = (
    YunoHeatSensorEntityDescription(
        key="balance",
        translation_key="balance",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value_fn=lambda data: data.balance,
    ),
    YunoHeatSensorEntityDescription(
        key="latest_usage",
        translation_key="latest_usage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=_latest_usage_kwh,
    ),
    YunoHeatSensorEntityDescription(
        key="latest_cost",
        translation_key="latest_cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_EURO,
        suggested_display_precision=2,
        value_fn=_latest_cost,
    ),
    YunoHeatSensorEntityDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_last_reading_at,
    ),
    YunoHeatSensorEntityDescription(
        key="meter_reading",
        translation_key="meter_reading",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=_meter_reading_kwh,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YunoHeatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yuno Heat sensors from a config entry."""
    coordinator = entry.runtime_data
    entities: list[YunoHeatEntity] = [
        YunoHeatSensor(coordinator, description) for description in SENSORS
    ]

    cumulative_description = SensorEntityDescription(
        key="cumulative_usage",
        translation_key="cumulative_usage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    )
    entities.append(YunoHeatCumulativeSensor(coordinator, cumulative_description))

    async_add_entities(entities)


class YunoHeatSensor(YunoHeatEntity, SensorEntity):
    """A sensor exposing one Yuno Heat account metric."""

    entity_description: YunoHeatSensorEntityDescription

    def __init__(
        self,
        coordinator: YunoHeatDataUpdateCoordinator,
        description: YunoHeatSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)

    @property
    def native_value(self) -> StateType | datetime:
        """Return the current value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)


class YunoHeatCumulativeSensor(YunoHeatEntity, RestoreSensor):
    """A sensor that maintains a cumulative total of usage events."""

    def __init__(
        self,
        coordinator: YunoHeatDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)
        self._state: float = 0.0
        self._last_event_id: int | None = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (state := await self.async_get_last_sensor_data()) is not None:
            try:
                self._state = float(state.native_value)
            except (TypeError, ValueError):
                pass

        if (state := await self.async_get_last_state()) is not None:
            if "last_event_id" in state.attributes:
                self._last_event_id = state.attributes["last_event_id"]

        self._update_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {"last_event_id": self._last_event_id}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        super()._handle_coordinator_update()

    def _update_state(self) -> None:
        """Update the cumulative state from recent events."""
        events = self.coordinator.data.recent_events
        if not events:
            return

        events_to_process = []
        for event in events:
            if (
                self._last_event_id is not None
                and event.event_id <= self._last_event_id
            ):
                break
            events_to_process.append(event)

        for event in reversed(events_to_process):
            if event.quantity is not None:
                self._state += event.quantity
            self._last_event_id = event.event_id

    @property
    def native_value(self) -> StateType:
        """Return the current value."""
        return self._state
