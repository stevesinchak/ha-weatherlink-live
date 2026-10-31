"""Download-diagnostics output."""

from unittest.mock import AsyncMock, patch

from custom_components.davis_weatherlink_live.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.test_init import DID, OPTIONS, URL, setup, wll_payload  # noqa: F401 (fixture)


async def test_diagnostics_redacts_host(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["options"]["api_host"] == "**REDACTED**"
    assert diag["options"]["update_interval"] == OPTIONS["update_interval"]
    assert diag["raw_api"]["data"]["did"] == DID  # kept for debugging unique ids
    assert diag["raw_api"]["data"]["conditions"] == wll_payload["data"]["conditions"]
    assert diag["last_update_success"] is True
    assert diag["realtime"] is None


async def test_diagnostics_realtime_status(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    with patch(
        "custom_components.davis_weatherlink_live.RealtimeListener.async_start", AsyncMock()
    ):
        entry = await setup(hass, {**OPTIONS, "realtime_section": {"realtime": True}})

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["realtime"] == {
        "listening": False,
        "renewing": False,
        "packets_since_renewal": 0,
        "values": 0,
    }
    assert await hass.config_entries.async_unload(entry.entry_id)
