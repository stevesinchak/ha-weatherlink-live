"""Tests for the optional real-time UDP broadcast listener."""

import asyncio
import json
import socket
from unittest.mock import MagicMock, patch

import aiohttp
import pytest

from custom_components.davis_weatherlink_live import realtime
from custom_components.davis_weatherlink_live.realtime import (
    RealtimeListener,
    is_realtime_key,
    parse_realtime,
)
from custom_components.davis_weatherlink_live.sensor import get_device_sensors
from tests.test_fake_apis import fake_server

# These tests talk to the simulators over localhost on purpose
pytestmark = pytest.mark.usefixtures("socket_enabled")

DID = "001D0A700002"

# ISS record shaped like the spec's example broadcast
ISS = {
    "lsid": 48308,
    "data_structure_type": 1,
    "txid": 1,
    "wind_speed_last": 2,
    "wind_dir_last": 90,
    "rain_size": 1,
    "rain_rate_last": 0,
    "rain_15_min": 3,
    "rain_60_min": 4,
    "rain_24_hr": 5,
    "rain_storm": None,
    "rain_storm_start_at": None,
    "rainfall_daily": 6,
    "rainfall_monthly": 7,
    "rainfall_year": 8,
    "wind_speed_hi_last_10_min": 9,
    "wind_dir_at_hi_speed_last_10_min": 180,
}


def packet(**changes):
    return json.dumps({"did": DID, "ts": 1, "conditions": [{**ISS, **changes}]}).encode()


def make_listener():
    return RealtimeListener(MagicMock(), None, "http://wll", DID)


def test_parse_realtime_maps_names_and_units():
    data = parse_realtime({"did": DID, "conditions": [ISS]}, DID)
    sfx = f"_tx1_{DID}"
    assert data["wind_speed_last" + sfx] == 2
    assert data["wind_dir_last_rose" + sfx] == "E"
    assert data["rainfall_last_15_min" + sfx] == 0.03  # renamed field, counts x 0.01"
    assert data["rainfall_year" + sfx] == 0.08
    assert data["rain_storm" + sfx] == 0.0  # null = no storm in progress


def test_realtime_keys_match_sensor_entities():
    # Drift guard: every value from the broadcast must land on a real sensor
    sensor_keys = {d.key for d in get_device_sensors(ISS, "entry1", DID)}
    rt_keys = set(parse_realtime({"conditions": [ISS]}, DID))
    assert rt_keys <= sensor_keys
    assert all(is_realtime_key(k) for k in rt_keys)
    assert not is_realtime_key(f"temp_tx1_{DID}")


def test_ignores_other_hubs_and_junk():
    listener = make_listener()
    listener.handle_packet(b"not json")
    listener.handle_packet(json.dumps({"did": "OTHERHUB", "conditions": [ISS]}).encode())
    assert listener.value(f"wind_speed_last_tx1_{DID}") == (False, None)


def test_notifies_only_on_change():
    listener = make_listener()
    calls = []
    listener.add_listener(lambda: calls.append(1))
    listener.handle_packet(packet())
    listener.handle_packet(packet())  # identical: no new notification
    listener.handle_packet(packet(wind_speed_last=5))
    assert len(calls) == 2
    assert listener.value(f"wind_speed_last_tx1_{DID}") == (True, 5)


def test_values_go_stale():
    listener = make_listener()
    with patch.object(realtime.time, "monotonic", return_value=100.0):
        listener.handle_packet(packet())
    with patch.object(realtime.time, "monotonic", return_value=100.0 + realtime.REALTIME_STALE_AFTER + 1):
        assert listener.value(f"wind_speed_last_tx1_{DID}") == (False, None)


def free_udp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def start_now(listener, port):
    """async_start, then run the delayed first request right away (no 7s wait).

    Returns (started, delay requested, renewal scheduled). Leaves the listener running.
    """
    with patch.object(realtime, "REALTIME_PORT", port), patch.object(
        realtime, "REALTIME_RETRY_DELAY", 0
    ), patch.object(realtime, "async_call_later") as call_later, patch.object(
        realtime, "async_track_time_interval"
    ) as track:
        started = await listener.async_start()
        if started:
            await call_later.call_args.args[2]()  # the scheduled first request
        delay = call_later.call_args.args[1] if call_later.called else None
        return started, delay, track.called


def session_returning(status=None, error=None):
    session = MagicMock()
    if error:
        session.get.side_effect = error
    else:
        session.get.return_value.__aenter__.return_value = MagicMock(status=status)
    return session


def test_first_request_is_delayed_off_the_poll():
    session = session_returning(error=aiohttp.ClientConnectionError("busy"))
    listener = RealtimeListener(MagicMock(), session, "http://wll", DID)

    async def run():
        result = await start_now(listener, free_udp_port())
        await listener.async_stop()
        return result

    _, delay, _ = asyncio.run(run())
    assert delay == realtime.REALTIME_FIRST_REQUEST_DELAY == 7


def test_hub_says_no_stops_realtime():
    # AirLink / no ISS: the hub refuses the broadcast. Must not raise, and stops listening.
    listener = RealtimeListener(MagicMock(), session_returning(status=409), "http://wll", DID)
    started, _, renewing = asyncio.run(start_now(listener, free_udp_port()))
    assert started and not renewing
    assert listener._transport is None


def test_unreachable_hub_retries_once_then_keeps_renewing():
    # A refused connection (hub busy, e.g. mid-poll) must not disable real-time
    session = session_returning(error=aiohttp.ClientConnectionError("Connect call failed"))
    listener = RealtimeListener(MagicMock(), session, "http://wll", DID)

    async def run():
        result = await start_now(listener, free_udp_port())
        await listener.async_stop()
        return result

    started, _, renewing = asyncio.run(run())
    assert started and renewing
    assert session.get.call_count == 2  # first try + one quick retry


def test_end_to_end_with_simulator():
    """Start the broadcast on fake_api.py and receive real UDP packets."""
    port = free_udp_port()
    flags = {"REALTIME_PORT": port, "BROADCAST_ADDR": "127.0.0.1", "_broadcast_until": 0.0, "_broadcast_thread": None}

    async def run(base_url):
        async with aiohttp.ClientSession() as session:
            listener = RealtimeListener(MagicMock(), session, base_url, "002E0B349999")
            got_packet = asyncio.Event()
            listener.add_listener(got_packet.set)
            assert (await start_now(listener, port))[0] is True
            try:
                await asyncio.wait_for(got_packet.wait(), timeout=5)
            finally:
                await listener.async_stop()
            return listener.value("wind_speed_last_tx1_002E0B349999")

    with fake_server("fake_api", **flags) as url:
        fresh, value = asyncio.run(run(url.rsplit("/v1/", 1)[0]))
    assert fresh and isinstance(value, float)


def test_parse_realtime_skips_non_iss_records():
    assert parse_realtime({"conditions": [{**ISS, "data_structure_type": 2}]}, DID) == {}


def test_socket_errors_are_only_logged():
    realtime._Protocol(make_listener()).error_received(OSError("boom"))


def test_port_in_use_disables_realtime():
    async def run():
        loop = asyncio.get_running_loop()
        with patch.object(loop, "create_datagram_endpoint", side_effect=OSError("in use")):
            return await make_listener().async_start()

    assert asyncio.run(run()) is False


def test_no_packets_warns_once(caplog):
    listener = make_listener()

    async def run():
        with patch.object(listener, "_async_request_with_retry"):
            await listener._async_renew()
            await listener._async_renew()

    asyncio.run(run())
    assert sum("no UDP broadcast packets" in r.message for r in caplog.records) == 1
