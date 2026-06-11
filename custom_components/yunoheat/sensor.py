"""Sensor platform for the Yuno Energy Heat integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
from homeassistant.core import HomeAssistant
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
    async_add_entities(
        YunoHeatSensor(coordinator, description) for description in SENSORS
    )


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
