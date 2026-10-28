"""Optional real-time wind & rain from the WeatherLink Live UDP broadcast.

Isolated from polling: values live here, sensors overlay them while fresh, and
any failure just leaves the polled values in place.
Spec: https://weatherlink.github.io/weatherlink-live-local-api/
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import (
    API_TIMEOUT,
    REALTIME_FIRST_REQUEST_DELAY,
    REALTIME_PORT,
    REALTIME_RETRY_DELAY,
    REALTIME_RENEW_SECONDS,
    REALTIME_REQUEST_DURATION,
    REALTIME_STALE_AFTER,
)
from .davis_weatherlink_live import DavisApiError, DavisWeatherLinkLive as Davis

_LOGGER = logging.getLogger(__name__)

# Sensor field names (as used by the poller) that the broadcast updates
REALTIME_FIELDS = frozenset(
    {
        "wind_speed_last",
        "wind_dir_last",
        "wind_dir_last_rose",
        "wind_speed_hi_last_10_min",
        "wind_dir_at_hi_speed_last_10_min",
        "rain_rate_last",
        "rainfall_last_15_min",
        "rainfall_last_60_min",
        "rainfall_last_24_hr",
        "rain_storm",
        "rain_storm_start_at",
        "rainfall_daily",
        "rainfall_monthly",
        "rainfall_year",
    }
)


def is_realtime_key(key: str) -> bool:
    """True for sensor keys like 'wind_speed_last_tx1_<did>'."""
    field, sep, _ = key.partition("_tx")
    return bool(sep) and field in REALTIME_FIELDS


def parse_realtime(packet: dict[str, Any], did: str) -> dict[str, Any]:
    """Map an ISS broadcast packet to the same keys and units the poller produces."""
    out: dict[str, Any] = {}
    for c in packet.get("conditions") or []:
        if c.get("data_structure_type") != 1:
            continue
        sfx = f"_tx{c.get('txid')}_{did}"
        size = c.get("rain_size")

        def rain(value: float | None, size: int | None = size) -> float | None:
            return Davis.calculate_rain_amount(value, size)

        out.update(
            {
                "wind_speed_last" + sfx: c.get("wind_speed_last"),
                "wind_dir_last" + sfx: c.get("wind_dir_last"),
                "wind_dir_last_rose" + sfx: Davis.wind_dir_to_rose(c.get("wind_dir_last")),
                "wind_speed_hi_last_10_min" + sfx: c.get("wind_speed_hi_last_10_min"),
                "wind_dir_at_hi_speed_last_10_min" + sfx: c.get(
                    "wind_dir_at_hi_speed_last_10_min"
                ),
                "rain_rate_last" + sfx: rain(c.get("rain_rate_last")),
                # The broadcast uses shorter names for these three
                "rainfall_last_15_min" + sfx: rain(c.get("rain_15_min")),
                "rainfall_last_60_min" + sfx: rain(c.get("rain_60_min")),
                "rainfall_last_24_hr" + sfx: rain(c.get("rain_24_hr")),
                # null means no storm in progress, same as the poller
                "rain_storm" + sfx: rain(Davis.zero_if_none(c.get("rain_storm"))),
                "rain_storm_start_at" + sfx: Davis.unix_to_datetime(
                    c.get("rain_storm_start_at")
                ),
                "rainfall_daily" + sfx: rain(c.get("rainfall_daily")),
                "rainfall_monthly" + sfx: rain(c.get("rainfall_monthly")),
                "rainfall_year" + sfx: rain(c.get("rainfall_year")),
            }
        )
    return out


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self, listener: RealtimeListener) -> None:
        self._listener = listener

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        self._listener.handle_packet(data, addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("Real-time UDP socket error: %s", exc)


class RealtimeListener:
    """Requests the broadcast, receives packets, and holds the latest values."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        base_url: str,
        did: str,
    ) -> None:
        self._hass = hass
        self._session = session
        self._base_url = base_url
        self._did = did
        self._values: dict[str, Any] = {}
        self._last_seen: dict[str, float] = {}
        self._callbacks: list[Callable[[], None]] = []
        self._transport: asyncio.DatagramTransport | None = None
        self._unsub_renew: Callable[[], None] | None = None
        self._unsub_first: Callable[[], None] | None = None
        self._warned_request = False
        self._packets = 0  # packets received since the last renewal, for diagnostics
        self._warned_no_packets = False

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Call `callback` when any value changes; returns an unsubscribe function."""
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def value(self, key: str) -> tuple[bool, Any]:
        """(True, value) if `key` arrived in the last REALTIME_STALE_AFTER seconds."""
        seen = self._last_seen.get(key)
        if seen is None or time.monotonic() - seen > REALTIME_STALE_AFTER:
            return False, None
        return True, self._values[key]

    async def async_start(self) -> bool:
        """Listen, then request the broadcast shortly after. Never raises."""
        try:
            loop = asyncio.get_running_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: _Protocol(self),
                local_addr=("0.0.0.0", REALTIME_PORT),
                reuse_port=True,  # lets two hubs' entries (or other apps) share the port
                allow_broadcast=True,
            )
        except Exception as err:  # noqa: BLE001 - isolation: any failure only disables real-time
            _LOGGER.warning(
                "Real-time updates disabled, can't listen on UDP %s: %s", REALTIME_PORT, err
            )
            return False

        self._unsub_first = async_call_later(
            self._hass, REALTIME_FIRST_REQUEST_DELAY, self._async_first_request
        )
        _LOGGER.debug(
            "Real-time listening on UDP port %s for %s (%d sensors subscribed), "
            "requesting broadcast in %ss",
            REALTIME_PORT,
            self._did,
            len(self._callbacks),
            REALTIME_FIRST_REQUEST_DELAY,
        )
        return True

    async def async_stop(self) -> None:
        for unsub in (self._unsub_first, self._unsub_renew):
            if unsub:
                unsub()
        self._unsub_first = self._unsub_renew = None
        if self._transport:
            self._transport.close()
            self._transport = None

    async def _async_first_request(self, _now: datetime | None = None) -> None:
        self._unsub_first = None
        await self._async_request_with_retry()
        if self._transport:  # still running (a hub "no" stops the listener)
            self._unsub_renew = async_track_time_interval(
                self._hass, self._async_renew, timedelta(seconds=REALTIME_RENEW_SECONDS)
            )

    async def _async_request_with_retry(self) -> None:
        """Request the broadcast, retrying once. A hub "no" stops real-time."""
        for attempt in (1, 2):
            try:
                await self._async_request_broadcast()
                return
            except DavisApiError as err:  # the hub answered "no": AirLink, or no ISS
                _LOGGER.warning("Real-time updates disabled for %s: %s", self._base_url, err)
                await self.async_stop()
                return
            except Exception as err:  # noqa: BLE001 - hub busy/unreachable
                if attempt == 1:
                    _LOGGER.debug(
                        "Real-time request to %s failed (%s), retrying in %ss",
                        self._base_url,
                        err,
                        REALTIME_RETRY_DELAY,
                    )
                    await asyncio.sleep(REALTIME_RETRY_DELAY)
                    continue
                log = _LOGGER.debug if self._warned_request else _LOGGER.warning
                self._warned_request = True
                log(
                    "Real-time request to %s failed twice, trying again in %ss: %s",
                    self._base_url,
                    REALTIME_RENEW_SECONDS,
                    err,
                )

    async def _async_request_broadcast(self) -> int:
        """Ask the hub to broadcast; returns the UDP port."""
        async with self._session.get(
            f"{self._base_url}/v1/real_time",
            params={"duration": REALTIME_REQUEST_DURATION},
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
        ) as response:
            if 400 <= response.status < 500:  # 409: no ISS; 404: AirLink has no endpoint
                raise DavisApiError(f"real_time request returned HTTP {response.status}")
            response.raise_for_status()  # 5xx: hub busy, retried on renewal
            body = await response.json(content_type=None)
        _LOGGER.debug("Real-time broadcast requested from %s: %s", self._base_url, body)
        return int(body["data"]["broadcast_port"])

    async def _async_renew(self, _now: datetime | None = None) -> None:
        packets, self._packets = self._packets, 0
        _LOGGER.debug(
            "Real-time: %d UDP packets in the last %ss for %s",
            packets,
            REALTIME_RENEW_SECONDS,
            self._did,
        )
        if packets == 0 and not self._warned_no_packets:
            self._warned_no_packets = True
            _LOGGER.warning(
                "Real-time: no UDP broadcast packets received from %s in %ss. Check that "
                "Home Assistant can receive UDP broadcasts on port 22222 (same network/VLAN, "
                "host networking for Docker, no firewall blocking it)",
                self._base_url,
                REALTIME_RENEW_SECONDS,
            )
        await self._async_request_with_retry()

    def handle_packet(self, data: bytes, addr: tuple[str | Any, int] | None = None) -> None:
        """Store values from one UDP packet and notify sensors if anything changed."""
        self._packets += 1
        _LOGGER.debug("Real-time packet from %s (%d bytes): %s", addr, len(data), data[:500])
        try:
            packet = json.loads(data)
            if not isinstance(packet, dict) or packet.get("did") != self._did:
                _LOGGER.debug(
                    "Ignoring real-time packet for did %s (expecting %s)",
                    packet.get("did") if isinstance(packet, dict) else None,
                    self._did,
                )
                return  # another hub on the LAN, or junk
            parsed = parse_realtime(packet, self._did)
        except Exception as err:  # noqa: BLE001 - one bad packet must not stop the stream
            _LOGGER.debug("Ignoring bad real-time packet: %s", err)
            return

        now = time.monotonic()
        changed = False
        for key, val in parsed.items():
            self._last_seen[key] = now
            if key not in self._values or self._values[key] != val:
                self._values[key] = val
                changed = True
        _LOGGER.debug(
            "Real-time parsed %d values, changed=%s, notifying %d sensors",
            len(parsed),
            changed,
            len(self._callbacks) if changed else 0,
        )
        if changed:
            for callback in list(self._callbacks):
                callback()
