"""Diagnostics for Davis WeatherLink Live: Settings > Devices & services > ⋮ > Download diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MyConfigEntry

# did (the hub's MAC) is kept on purpose: unique ids are built from it
TO_REDACT = {"api_host"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MyConfigEntry
) -> dict[str, Any]:
    """Return the options, the raw API response and the real-time status."""
    coordinator = entry.runtime_data.coordinator
    realtime = entry.runtime_data.realtime
    return {
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "raw_api": coordinator.data["raw_api"],
        "realtime": None
        if realtime is None
        else {
            "listening": realtime._transport is not None,
            "renewing": realtime._unsub_renew is not None,
            "packets_since_renewal": realtime._packets,
            "values": len(realtime._values),
        },
    }
