"""Davis WeatherLink Live integration by Steve Sinchak."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from awesomeversion import AwesomeVersion
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.device_registry import DeviceEntry

from .coordinator import WeatherCoordinator

_LOGGER = logging.getLogger(__name__)

MIN_HA_VERSION = "2026.7.0"  # UnitOfDensity, used in sensor.py

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MyConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: WeatherCoordinator


async def async_setup_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Set up Davis WeatherLink Live from a config entry."""
    if AwesomeVersion(HA_VERSION) < MIN_HA_VERSION:
        raise ConfigEntryError(
            f"Davis WeatherLink Live requires Home Assistant {MIN_HA_VERSION} or newer "
            f"(running {HA_VERSION}). Please upgrade Home Assistant."
        )

    coordinator = WeatherCoordinator(hass, config_entry)
    # Raises ConfigEntryNotReady if the device can't be reached, so HA retries
    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = RuntimeData(coordinator)
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the integration when the options change."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow deleting a device from the UI."""
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
