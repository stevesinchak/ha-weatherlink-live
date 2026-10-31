"""Config and options flow tests, run through Home Assistant's real flow manager."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.davis_weatherlink_live.const import DOMAIN
from custom_components.davis_weatherlink_live.davis_weatherlink_live import DavisApiError

DID = "001D0A000001"

USER_INPUT = {
    "api_host": "10.0.0.5",
    "api_path": "/v1/current_conditions",
    "update_interval": 30,
    "cache_section": {"cache": False, "cache_age": 60},
    "realtime_section": {"realtime": False},
}

DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("10.0.0.9"),
    ip_addresses=[ip_address("10.0.0.9")],
    hostname="weatherlinklive-33a9cb.local.",
    name="weatherlinklive-33a9cb._weatherlinklive._tcp.local.",
    port=80,
    type="_weatherlinklive._tcp.local.",
    properties={},
)


@pytest.fixture
def mock_fetch():
    """The device connection test; succeeds unless a test changes it."""
    with patch(
        "custom_components.davis_weatherlink_live.config_flow.DavisWeatherLinkLive.get_weather_data",
        new_callable=AsyncMock,
        return_value={"raw_api": {"data": {"did": DID}}},
    ) as fetch:
        yield fetch


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Don't run the real integration setup when an entry is created."""
    with patch(
        "custom_components.davis_weatherlink_live.async_setup_entry", return_value=True
    ) as setup:
        yield setup


async def start_user_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow_success(hass, mock_fetch):
    result = await start_user_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Davis WeatherLink Live {DID}"
    assert result["data"] == {}
    assert result["options"] == USER_INPUT
    mock_fetch.assert_awaited_once()


async def test_url_host_rejected_without_connecting(hass, mock_fetch):
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "api_host": "http://10.0.0.5"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"api_host": "api_host_http_not_allowed"}
    mock_fetch.assert_not_awaited()


async def test_interval_too_low(hass, mock_fetch):
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "update_interval": 5}
    )
    assert result["errors"] == {"update_interval": "update_interval_too_low"}
    mock_fetch.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (aiohttp.ClientConnectionError("refused"), "cannot_connect"),
        (TimeoutError(), "cannot_connect"),
        (DavisApiError("missing conditions"), "invalid_response"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_connection_errors_then_recover(hass, mock_fetch, error, expected):
    mock_fetch.side_effect = error
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected}

    # Device reachable again: submitting the same form now works
    mock_fetch.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_host_aborts(hass, mock_fetch):
    MockConfigEntry(domain=DOMAIN, options=USER_INPUT).add_to_hass(hass)
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_fetch.assert_not_awaited()


async def test_duplicate_hub_under_other_host_aborts(hass, mock_fetch):
    MockConfigEntry(domain=DOMAIN, unique_id=DID, options=USER_INPUT).add_to_hass(hass)
    result = await start_user_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "api_host": "wll.local"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def start_zeroconf(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=DISCOVERY
    )


async def test_zeroconf_discovery_prefills_host(hass, mock_fetch):
    result = await start_zeroconf(hass)
    assert result["type"] is FlowResultType.FORM
    schema_defaults = {str(k): k.default() for k in result["data_schema"].schema if hasattr(k.default, "__call__")}
    assert schema_defaults["api_host"] == "10.0.0.9"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "api_host": "10.0.0.9"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == DID


async def test_zeroconf_known_hub_new_ip_updates_host(hass, mock_fetch, mock_setup_entry):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DID, options=USER_INPUT)
    entry.add_to_hass(hass)
    result = await start_zeroconf(hass)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.options["api_host"] == "10.0.0.9"
    assert entry.options["update_interval"] == USER_INPUT["update_interval"]
    assert mock_setup_entry.called  # reloaded with the new IP


async def test_zeroconf_known_hub_same_ip_no_change(hass, mock_fetch, mock_setup_entry):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=DID, options={**USER_INPUT, "api_host": "10.0.0.9"}
    )
    entry.add_to_hass(hass)
    result = await start_zeroconf(hass)
    await hass.async_block_till_done()
    assert result["reason"] == "already_configured"
    assert not mock_setup_entry.called


async def test_zeroconf_unreachable_aborts(hass, mock_fetch):
    mock_fetch.side_effect = aiohttp.ClientConnectionError("busy")
    result = await start_zeroconf(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_options_flow(hass):
    entry = MockConfigEntry(domain=DOMAIN, options=USER_INPUT)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Invalid interval keeps the form open
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**USER_INPUT, "update_interval": 5}
    )
    assert result["errors"] == {"update_interval": "update_interval_too_low"}

    new_options = {**USER_INPUT, "update_interval": 60, "realtime_section": {"realtime": True}}
    result = await hass.config_entries.options.async_configure(result["flow_id"], new_options)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == new_options


async def test_options_new_host_is_tested(hass, mock_fetch):
    entry = MockConfigEntry(domain=DOMAIN, options=USER_INPUT)
    entry.add_to_hass(hass)
    new_options = {**USER_INPUT, "api_host": "10.0.0.99"}

    mock_fetch.side_effect = aiohttp.ClientConnectionError("refused")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], new_options)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.options == USER_INPUT  # nothing saved

    mock_fetch.side_effect = None
    result = await hass.config_entries.options.async_configure(result["flow_id"], new_options)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["api_host"] == "10.0.0.99"


async def test_options_unchanged_host_not_tested(hass, mock_fetch):
    # Saving other settings must not hit the device (it may be busy with the poller)
    entry = MockConfigEntry(domain=DOMAIN, options=USER_INPUT)
    entry.add_to_hass(hass)
    mock_fetch.side_effect = aiohttp.ClientConnectionError("busy")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**USER_INPUT, "update_interval": 60}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    mock_fetch.assert_not_awaited()


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DID, options=USER_INPUT)
    entry.add_to_hass(hass)
    return entry


async def test_reconfigure_updates_host(hass, mock_fetch, entry):
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_host": "10.0.0.77", "api_path": "/v1/current_conditions"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.options == {**USER_INPUT, "api_host": "10.0.0.77"}


async def test_reconfigure_other_hub_aborts(hass, mock_fetch, entry):
    mock_fetch.return_value = {"raw_api": {"data": {"did": "001D0AFFFFFF"}}}
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_host": "10.0.0.77", "api_path": "/v1/current_conditions"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.options == USER_INPUT


async def test_reconfigure_cannot_connect(hass, mock_fetch, entry):
    mock_fetch.side_effect = aiohttp.ClientError
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_host": "10.0.0.77", "api_path": "/v1/current_conditions"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_url_host_rejected(hass, mock_fetch, entry):
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"api_host": "http://10.0.0.77", "api_path": "/v1/current_conditions"}
    )
    assert result["errors"] == {"api_host": "api_host_http_not_allowed"}
    mock_fetch.assert_not_called()
