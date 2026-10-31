"""Set up the whole integration in Home Assistant, fed by the fake_api.py simulator's data."""

import json
import urllib.request
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.davis_weatherlink_live.const import DOMAIN
from tests.test_fake_apis import fake_server

URL = "http://10.0.0.5/v1/current_conditions"
DID = "002E0B349999"  # fake_api.py's hub id
OPTIONS = {
    "api_host": "10.0.0.5",
    "api_path": "/v1/current_conditions",
    "update_interval": 30,
    "cache_section": {"cache": False, "cache_age": 60},
    "realtime_section": {"realtime": False},
}


@pytest.fixture
def wll_payload(socket_enabled):
    """Raw JSON from the fake_api.py simulator, served to HA through aioclient_mock."""
    with fake_server("fake_api") as url:
        with urllib.request.urlopen(url) as response:
            return json.load(response)


async def setup(hass, options=OPTIONS, unique_id=None, title="Davis Device"):
    hass.config.units = US_CUSTOMARY_SYSTEM  # the device reports °F and mph; compare unconverted
    entry = MockConfigEntry(domain=DOMAIN, options=options, unique_id=unique_id, title=title)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def state_of(hass, unique_id):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id, unique_id
    return hass.states.get(entity_id)


async def test_setup_and_unload(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.unique_id == DID

    temp = wll_payload["data"]["conditions"][0]["temp"]
    assert float(state_of(hass, f"temp_tx1_{DID}").state) == temp
    assert len(dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)) == len(
        wll_payload["data"]["conditions"]
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    "response",
    [
        {"exc": aiohttp.ClientConnectionError("refused")},
        {"status": 500},
    ],
)
async def test_unreachable_device_retries(hass, aioclient_mock, response):
    aioclient_mock.get(URL, **response)
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_missing_did_retries(hass, aioclient_mock, wll_payload):
    del wll_payload["data"]["did"]
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert "missing the device id" in entry.reason


async def test_old_home_assistant_refused(hass, aioclient_mock):
    with patch("custom_components.davis_weatherlink_live.HA_VERSION", "2026.6.0"):
        entry = await setup(hass)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert "requires Home Assistant 2026.7.0" in entry.reason
    assert aioclient_mock.call_count == 0


async def test_options_change_reloads(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)
    calls = aioclient_mock.call_count

    hass.config_entries.async_update_entry(entry, options={**OPTIONS, "update_interval": 60})
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert aioclient_mock.call_count > calls  # set up again, so fetched again


async def test_realtime_packet_updates_wind_sensor(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    with patch(
        "custom_components.davis_weatherlink_live.RealtimeListener.async_start", AsyncMock()
    ):
        entry = await setup(hass, {**OPTIONS, "realtime_section": {"realtime": True}})
    temp_before = state_of(hass, f"temp_tx1_{DID}").state

    iss = {"lsid": 309782, "data_structure_type": 1, "txid": 1, "wind_speed_last": 12.5}
    packet = {"did": DID, "ts": 1, "conditions": [iss]}
    entry.runtime_data.realtime.handle_packet(json.dumps(packet).encode())
    await hass.async_block_till_done()

    assert float(state_of(hass, f"wind_speed_last_tx1_{DID}").state) == 12.5
    assert state_of(hass, f"temp_tx1_{DID}").state == temp_before  # polled sensors untouched
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_old_hostname_unique_id_becomes_did(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass, unique_id="weatherlinklive-349999.local.")
    assert entry.unique_id == DID  # so discovery can follow IP changes


async def test_transmitter_added_later_gets_sensors(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)
    assert er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"temp_tx7_{DID}") is None

    iss = next(c for c in wll_payload["data"]["conditions"] if c["data_structure_type"] == 1)
    wll_payload["data"]["conditions"].append({**iss, "lsid": 999999, "txid": 7})
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, json=wll_payload)
    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert state_of(hass, f"temp_tx7_{DID}") is not None
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == len(wll_payload["data"]["conditions"])


async def test_old_default_title_gets_hub_name(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass)
    assert entry.title == f"Davis WeatherLink Live {DID}"


async def test_user_title_is_kept(hass, aioclient_mock, wll_payload):
    aioclient_mock.get(URL, json=wll_payload)
    entry = await setup(hass, title="Backyard Station")
    assert entry.title == "Backyard Station"
