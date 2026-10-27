"""Davis WeatherLink Live integration by Steve Sinchak."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from awesomeversion import AwesomeVersion
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .coordinator import WeatherCoordinator
from .realtime import RealtimeListener

_LOGGER = logging.getLogger(__name__)

MIN_HA_VERSION = "2026.7.0"  # UnitOfDensity, used in sensor.py

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MyConfigEntry = ConfigEntry[RuntimeData]


def migrate_unique_id(unique_id: str, did: str) -> str | None:
    """Return the new id for an old type 1/2 sensor id ("temp_tx1"), else None."""
    if re.search(r"_tx\d+$", unique_id):
        return f"{unique_id}_{did}"
    return None


def migrate_entities(ent_reg: er.EntityRegistry, entry_id: str, did: str) -> None:
    """Rename old type 1/2 unique ids, keeping the original entity and its history."""
    for entity in er.async_entries_for_config_entry(ent_reg, entry_id):
        new_id = migrate_unique_id(entity.unique_id, did)
        if new_id is None:
            continue
        # A dev build skipped this migration and created duplicates under the new id:
        # drop the duplicate so the original entity_id (with history) takes the new id
        if duplicate := ent_reg.async_get_entity_id(entity.domain, DOMAIN, new_id):
            ent_reg.async_remove(duplicate)
        ent_reg.async_update_entity(entity.entity_id, new_unique_id=new_id)


@dataclass
class RuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: WeatherCoordinator
    realtime: RealtimeListener | None = None


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

    did = coordinator.data["raw_api"]["data"].get("did")
    if not did:  # needed for unique ids; never build "..._None" ids
        raise ConfigEntryNotReady("Davis API response is missing the device id (did)")
    if config_entry.unique_id != did:  # older entries: none, or the zeroconf hostname
        hass.config_entries.async_update_entry(config_entry, unique_id=did)

    # Old ISS/soil ids ("temp_tx1") weren't unique across hubs; add the hub id
    migrate_entities(er.async_get(hass), config_entry.entry_id, did)

    realtime = None
    if config_entry.options.get("realtime_section", {}).get("realtime", False):
        realtime = RealtimeListener(
            hass,
            async_get_clientsession(hass),
            f"http://{config_entry.options['api_host']}",
            did,
        )
        config_entry.async_on_unload(realtime.async_stop)

    # Set before platforms load so sensors can subscribe to real-time updates
    config_entry.runtime_data = RuntimeData(coordinator, realtime)
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    if realtime:
        await realtime.async_start()  # never raises; on failure polling just continues
    return True


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload the integration when the options change."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: MyConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow deleting a device only if the hub no longer reports it."""
    runtime = getattr(config_entry, "runtime_data", None)
    if runtime is None or not runtime.coordinator.data:  # entry not loaded: nothing reporting
        return True
    live = {
        (DOMAIN, config_entry.entry_id + str(c.get("lsid")))
        for c in runtime.coordinator.data["raw_api"]["data"]["conditions"]
    }
    return not (device_entry.identifiers & live)


async def async_unload_entry(hass: HomeAssistant, config_entry: MyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
