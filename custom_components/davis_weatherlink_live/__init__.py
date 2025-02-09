"""The Davis WeatherLink Live Local integration by Steve Sinchak."""

from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN
from .davis_weatherlink_live import DavisWeatherLinkLive

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Davis WeatherLink Live Local integration."""
    # Register the reload service
    async def async_reload_config_entry(call):
        """Reload the integration's config entry."""
        _LOGGER.info("Reloading config entry for %s", DOMAIN)
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "reload", async_reload_config_entry)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Davis WeatherLink Live Local integration from a config entry."""
    
    # Construct WWL URL from the option provided host and path
    wll_url = "http://" + entry.options["api_host"] + entry.options["api_path"]
    _LOGGER.info("WeatherLink Live URL %s", wll_url)
    
    # Create an instance of the API using the provided URL
    wll_local = DavisWeatherLinkLive(wll_url)

    async def async_update_data():
        """Fetch new data from the WeatherLink API."""
        try:
            return await hass.async_add_executor_job(wll_local.get_weather_data)
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}")

    # Setup DataUpdateCoordinator for periodic data updates
    _LOGGER.info("Setting Update Interval to %s seconds", entry.options["update_interval"])
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="davis_weatherlink_live_local",
        update_method=async_update_data,
        update_interval=timedelta(seconds=entry.options["update_interval"]),  # Fetch every update_interval
    )

    # Refresh data at startup
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator inside Home Assistant's data dictionary
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward entry setups to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    
    # Remove stored data if unloading was successful
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            await coordinator.async_shutdown()  # Ensure background updates stop

    # If no more entries exist, remove the domain key from hass.data
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN, None)

    return unload_ok