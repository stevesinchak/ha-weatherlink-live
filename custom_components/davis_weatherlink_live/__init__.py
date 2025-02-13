"""The Integration 101 Template integration.

This shows how to use the requests library to get and use data from an external device over http and
uses this data to create some binary sensors (of a generic type) and sensors (of multiple types).

Things you need to change
1. Change the api call in the coordinator async_update_data and the config flow validate input methods.
2. The constants in const.py that define the api data parameters to set sensors for (and the sensor async_setup_entry logic)
3. The specific sensor types to match your requirements.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import WeatherCoordinator


_LOGGER = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# A list of the different platforms we wish to setup.
# Add or remove from this list based on your specific need
# of entity platform types.
# ----------------------------------------------------------------------------
PLATFORMS: list[Platform] = [Platform.SENSOR]

type MyConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator
    cancel_update_listener: Callable


async def async_setup_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Set up Example Integration from a config entry."""

    # ----------------------------------------------------------------------------
    # Initialise the coordinator that manages data updates from your api.
    # This is defined in coordinator.py
    # ----------------------------------------------------------------------------

    _LOGGER.debug("Setting up Coordinator")
    coordinator = WeatherCoordinator(hass, config_entry)

    # ----------------------------------------------------------------------------
    # Perform an initial data load from api.
    # async_config_entry_first_refresh() is special in that it does not log errors
    # if it fails.
    # ----------------------------------------------------------------------------
    _LOGGER.debug("Performing first refresh")
    await coordinator.async_config_entry_first_refresh()

    # ----------------------------------------------------------------------------
    # Test to see if api initialised correctly, else raise ConfigNotReady to make
    # HA retry setup.
    # Change this to match how your api will know if connected or successful
    # update.
    # ----------------------------------------------------------------------------
    if not coordinator.data:
        raise ConfigEntryNotReady

    # ----------------------------------------------------------------------------
    # Initialise a listener for config flow options changes.
    # This will be removed automatically if the integraiton is unloaded.
    # See config_flow for defining an options setting that shows up as configure
    # on the integration.
    # If you do not want any config flow options, no need to have listener.
    # ----------------------------------------------------------------------------
    cancel_update_listener = config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    # ----------------------------------------------------------------------------
    # Add the coordinator and update listener to your config entry to make
    # accessible throughout your integration
    # ----------------------------------------------------------------------------
    config_entry.runtime_data = RuntimeData(coordinator, cancel_update_listener)

    # ----------------------------------------------------------------------------
    # Setup platforms (based on the list of entity types in PLATFORMS defined above)
    # This calls the async_setup method in each of your entity type files.
    # ----------------------------------------------------------------------------
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)


    # Return true to denote a successful setup.
    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle config options update.

    Reload the integration when the options change.
    Called from our listener created above.
    """

    _LOGGER.info("Received Reload Request")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Delete device if selected from UI.

    Adding this function shows the delete device option in the UI.
    Remove this function if you do not want that option.
    You may need to do some checks here before allowing devices to be removed.
    """
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Unload a config entry.

    This is called when you remove your integration or shutdown HA.
    If you have created any custom services, they need to be removed here too.
    """

    _LOGGER.info("Unloading everything! bye bye")

    # Unload services
    for service in hass.services.async_services_for_domain(DOMAIN):
        hass.services.async_remove(DOMAIN, service)

    # Unload platforms and return result
    #return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    
    #oldie but goodie
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    
    # Remove stored data if unloading was successful
    if unload_ok:
        coordinator = config_entry.runtime_data.coordinator #hass.data[DOMAIN].pop(config_entry.entry_id, None)
        if coordinator:
            await coordinator.async_shutdown()  # Ensure background updates stop

    # If no more entries exist, remove the domain key from hass.data
    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    return unload_ok
