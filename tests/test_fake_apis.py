"""Run the fake_api*.py simulators in-process and parse their responses."""

import asyncio
import contextlib
import copy
import importlib
import threading
from http.server import HTTPServer

import aiohttp
import pytest

from custom_components.davis_weatherlink_live.davis_weatherlink_live import (
    DavisWeatherLinkLive,
)
from custom_components.davis_weatherlink_live.sensor import (
    get_device_name,
    get_device_sensors,
)

SIMULATORS = ("fake_api", "fake_api_aqm1", "fake_api_aqm2")


@contextlib.contextmanager
def fake_server(module_name, **flags):
    """Serve a simulator's JSONHandler on a free local port; yields its URL."""
    base = importlib.import_module(module_name).JSONHandler
    # Turn off every fault toggle so local edits to the simulators can't make tests flaky
    attrs = {name: False for name in dir(base) if name.startswith("ENABLE_")}
    attrs.update(flags)
    attrs["log_message"] = lambda *args: None
    handler = type("TestHandler", (base,), attrs)

    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/current_conditions"
    finally:
        server.shutdown()
        server.server_close()


def fetch(url, entry_id):
    async def _fetch():
        async with aiohttp.ClientSession() as session:
            return await DavisWeatherLinkLive(url, session, entry_id).get_weather_data()

    return asyncio.run(_fetch())


def conditions(data):
    return data["raw_api"]["data"]["conditions"]


def sensor_keys(data, entry_id):
    did = data["raw_api"]["data"].get("did")
    return [
        description.key
        for condition in conditions(data)
        for description in get_device_sensors(condition, entry_id, did)
    ]


@pytest.mark.parametrize("module_name", SIMULATORS)
def test_every_sensor_has_data(module_name):
    with fake_server(module_name) as url:
        data = fetch(url, "E1")

    for condition in conditions(data):
        assert get_device_name(condition) is not None, condition
    missing = [key for key in sensor_keys(data, "E1") if key not in data]
    assert not missing, f"sensors with no parsed value: {missing}"


def test_wll_device_types():
    with fake_server("fake_api") as url:
        data = fetch(url, "E1")

    types = {v for k, v in data.items() if k.startswith("data_structure_type")}
    assert types == {1, 2, 3, 4, 6}


def test_unique_ids_dont_collide():
    keys = []
    for module_name, entry_id in zip(SIMULATORS, ("A", "B", "C")):
        with fake_server(module_name) as url:
            data = fetch(url, entry_id)
        keys += sensor_keys(data, entry_id)
        if module_name == "fake_api":
            data_wll = data

    # A second WLL hub: same transmitter channels, but its own hardware id and
    # its own cloud-assigned lsids (Davis lsids are unique per sensor)
    second_hub = copy.deepcopy(data_wll["raw_api"])
    second_hub["data"]["did"] = "SECONDHUB"
    for condition in second_hub["data"]["conditions"]:
        condition["lsid"] += 1_000_000
    keys += sensor_keys(DavisWeatherLinkLive(None, None, "D").parse_weather_data(second_hub), "D")

    duplicates = {key for key in keys if keys.count(key) > 1}
    assert not duplicates, f"duplicate unique ids: {duplicates}"


def test_connection_refused_raises():
    with fake_server("fake_api", ENABLE_CONNECTION_REFUSED=True) as url:
        with pytest.raises(aiohttp.ClientError):
            fetch(url, "E1")
