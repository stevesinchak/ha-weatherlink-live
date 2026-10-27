#Davis WeatherLink Live Simulator for testing Home Assistant integration
 
import json
import random
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


class JSONHandler(BaseHTTPRequestHandler):
    # Set this to True to enable random 30-second delays
    ENABLE_RANDOM_DELAY = False

    # Set this to True to enable connection refused errors
    ENABLE_CONNECTION_REFUSED = False

    # Set this to true to enable random connection refused errors (50% chance)
    ENABLE_RANDOM_CONNECTION_REFUSED = True

    # Real-time UDP broadcast (GET /v1/real_time?duration=N), like the real WLL
    REALTIME_PORT = 22222
    BROADCAST_ADDR = "255.255.255.255"
    _broadcast_until = 0.0
    _broadcast_thread = None

    @classmethod
    def _broadcast(cls):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while time.time() < cls._broadcast_until:
            packet = {
                "did": "002E0B349999",
                "ts": int(time.time()),
                "conditions": [
                    {
                        "lsid": 309782 + txid,
                        "data_structure_type": 1,
                        "txid": txid,
                        "wind_speed_last": round(random.uniform(0, 25), 2),
                        "wind_dir_last": random.randint(0, 359),
                        "rain_size": 1,
                        "rain_rate_last": 0,
                        "rain_15_min": 0,
                        "rain_60_min": 0,
                        "rain_24_hr": 0,
                        "rain_storm": None,
                        "rain_storm_start_at": None,
                        "rainfall_daily": 0,
                        "rainfall_monthly": 10,
                        "rainfall_year": 663,
                        "wind_speed_hi_last_10_min": round(random.uniform(10, 30), 2),
                        "wind_dir_at_hi_speed_last_10_min": random.randint(0, 359),
                    }
                    for txid in (1, 2)
                ],
            }
            sock.sendto(json.dumps(packet).encode(), (cls.BROADCAST_ADDR, cls.REALTIME_PORT))
            time.sleep(2.5)
        sock.close()

    def _start_realtime(self):
        cls = type(self)
        query = parse_qs(urlparse(self.path).query)
        duration = int(query.get("duration", ["1200"])[0])
        cls._broadcast_until = max(cls._broadcast_until, time.time() + duration)
        if cls._broadcast_thread is None or not cls._broadcast_thread.is_alive():
            cls._broadcast_thread = threading.Thread(target=cls._broadcast, daemon=True)
            cls._broadcast_thread.start()
        print(f"Broadcasting real-time data on UDP {cls.REALTIME_PORT}...")
        body = {
            "data": {
                "broadcast_port": cls.REALTIME_PORT,
                "duration": round(cls._broadcast_until - time.time()),
            },
            "error": None,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_GET(self):
        # Refuse all connections if enabled
        if self.ENABLE_CONNECTION_REFUSED:
            print("Refusing connection...")
            self.connection.close()
            return

        # Randomly refuse connection if enabled
        if self.ENABLE_RANDOM_CONNECTION_REFUSED and random.choice([True, False]):
            print("Refusing connection...")
            self.connection.close()
            return

        # Randomly delay response by 30 seconds if enabled
        if self.ENABLE_RANDOM_DELAY and random.choice([True, False]):
            print("Delaying response by 30 seconds...")
            time.sleep(30)
            print("Response sent after 30-second delay")

        if self.path.startswith("/v1/real_time"):
            self._start_realtime()
            return

        RESPONSE = {
            "data": {
                "did": "002E0B349999",
                "ts": 1746711828,
                "conditions": [
                    {
                        "lsid": 309782,
                        "data_structure_type": 1,
                        "txid": 1,
                        "temp": round(random.uniform(10.1, 90.9), 2),
                        "hum": round(random.uniform(40.1, 60.8), 2),
                        "dew_point": 37.7,
                        "wet_bulb": 46.7,
                        "heat_index": 63.8,
                        "wind_chill": None,
                        "thw_index": None,
                        "thsw_index": None,
                        "wind_speed_last": None,
                        "wind_dir_last": None,
                        "wind_speed_avg_last_1_min": None,
                        "wind_dir_scalar_avg_last_1_min": None,
                        "wind_speed_avg_last_2_min": None,
                        "wind_dir_scalar_avg_last_2_min": None,
                        "wind_speed_hi_last_2_min": None,
                        "wind_dir_at_hi_speed_last_2_min": None,
                        "wind_speed_avg_last_10_min": None,
                        "wind_dir_scalar_avg_last_10_min": None,
                        "wind_speed_hi_last_10_min": None,
                        "wind_dir_at_hi_speed_last_10_min": None,
                        "rain_size": 2,
                        "rain_rate_last": 0,
                        "rain_rate_hi": 0,
                        "rainfall_last_15_min": 0,
                        "rain_rate_hi_last_15_min": 0,
                        "rainfall_last_60_min": 0,
                        "rainfall_last_24_hr": 0,
                        "rain_storm": 0,
                        "rain_storm_start_at": None,
                        "solar_rad": None,
                        "uv_index": None,
                        "rx_state": 0,
                        "trans_battery_flag": 0,
                        "rainfall_daily": 0,
                        "rainfall_monthly": 10,
                        "rainfall_year": 663,
                        "rain_storm_last": 10,
                        "rain_storm_last_start_at": 1746183780,
                        "rain_storm_last_end_at": 1746273661,
                    },
                    {
                        "lsid": 309842,
                        "data_structure_type": 1,
                        "txid": 2,
                        "temp": None,
                        "hum": None,
                        "dew_point": None,
                        "wet_bulb": None,
                        "heat_index": None,
                        "wind_chill": None,
                        "thw_index": None,
                        "thsw_index": None,
                        "wind_speed_last": 3.00,
                        "wind_dir_last": 46,
                        "wind_speed_avg_last_1_min": 5.06,
                        "wind_dir_scalar_avg_last_1_min": 68,
                        "wind_speed_avg_last_2_min": 4.00,
                        "wind_dir_scalar_avg_last_2_min": 64,
                        "wind_speed_hi_last_2_min": 12.00,
                        "wind_dir_at_hi_speed_last_2_min": 17,
                        "wind_speed_avg_last_10_min": 4.62,
                        "wind_dir_scalar_avg_last_10_min": 52,
                        "wind_speed_hi_last_10_min": 12.00,
                        "wind_dir_at_hi_speed_last_10_min": 63,
                        "rain_size": 1,
                        "rain_rate_last": 0,
                        "rain_rate_hi": 0,
                        "rainfall_last_15_min": 0,
                        "rain_rate_hi_last_15_min": 0,
                        "rainfall_last_60_min": 0,
                        "rainfall_last_24_hr": 0,
                        "rain_storm": None,
                        "rain_storm_start_at": None,
                        "solar_rad": None,
                        "uv_index": None,
                        "rx_state": 0,
                        "trans_battery_flag": 0,
                        "rainfall_daily": 0,
                        "rainfall_monthly": 0,
                        "rainfall_year": 0,
                        "rain_storm_last": None,
                        "rain_storm_last_start_at": None,
                        "rain_storm_last_end_at": None,
                    },
                    {
                        "lsid": 3187671188,
                        "data_structure_type": 2,
                        "txid": 3,
                        "temp_1": 11.1,
                        "temp_2": 22.2,
                        "temp_3": 33.3,
                        "temp_4": 44.4,
                        "moist_soil_1": 1111,
                        "moist_soil_2": 2222,
                        "moist_soil_3": 3333,
                        "moist_soil_4": 4444,
                        "wet_leaf_1": 111,
                        "wet_leaf_2": 222,
                        "rx_state": 0,
                        "trans_battery_flag": 0,
                    },
                    {
                        "lsid": 309780,
                        "data_structure_type": 4,
                        "temp_in": 73.9,
                        "hum_in": 42.8,
                        "dew_point_in": 49.9,
                        "heat_index_in": 73.1,
                    },
                    {
                        "lsid": 309779,
                        "data_structure_type": 3,
                        "bar_sea_level": 30.079,
                        "bar_trend": -0.026,
                        "bar_absolute": 30.012,
                    },
                    {
                        "lsid": 852455,
                        "data_structure_type": 6,
                        "temp": 70.9,
                        "hum": 58.1,
                        "dew_point": 55.4,
                        "wet_bulb": 59.9,
                        "heat_index": 70.3,
                        "pm_1_last": 2,
                        "pm_2p5_last": 2,
                        "pm_10_last": 2,
                        "pm_1": 2.71,
                        "pm_2p5": 3.31,
                        "pm_2p5_last_1_hour": 3.84,
                        "pm_2p5_last_3_hours": 4.08,
                        "pm_2p5_last_24_hours": 2.61,
                        "pm_2p5_nowcast": 4.0,
                        "pm_10": 3.89,
                        "pm_10_last_1_hour": 4.45,
                        "pm_10_last_3_hours": 4.66,
                        "pm_10_last_24_hours": 3.09,
                        "pm_10_nowcast": 4.61,
                        "last_report_time": 1751909719,
                        "pct_pm_data_last_1_hour": 100,
                        "pct_pm_data_last_3_hours": 100,
                        "pct_pm_data_nowcast": 100,
                        "pct_pm_data_last_24_hours": 100,
                    },
                ],
            },
            "error": None,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(RESPONSE).encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 80), JSONHandler)
    print("Serving JSON on port 80...")
    server.serve_forever()
