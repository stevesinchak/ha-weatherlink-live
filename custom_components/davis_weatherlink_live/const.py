# Constants for the Davis WeatherLink Live integration

DOMAIN = "davis_weatherlink_live"
API_PATH = "/v1/current_conditions"
API_TIMEOUT = 10
API_INITIAL_INTERVAL = 30
API_INITIAL_MAX_CACHE_AGE = 60

# Optional real-time UDP broadcast (WeatherLink Live only)
REALTIME_REQUEST_DURATION = 1200  # seconds the hub broadcasts per request
REALTIME_PORT = 22222  # spec default, used until the hub tells us otherwise
# Re-request often: it doubles as the retry after a failed request or a hub reboot,
# and the hub ignores requests shorter than the time it has left, so it is cheap
REALTIME_RENEW_SECONDS = 60
# The WLL accepts one HTTP connection at a time. Send the first request 7s after
# setup's poll so it, and every renewal 60s apart, falls between polls for the
# usual 10/15/20/30/60s poll intervals instead of colliding with them
REALTIME_FIRST_REQUEST_DELAY = 7
REALTIME_RETRY_DELAY = 3  # one quick retry if a request still collides
REALTIME_STALE_AFTER = 10  # seconds (4 missed packets) before falling back to polled values
