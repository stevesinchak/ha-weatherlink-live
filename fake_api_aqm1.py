#Davis AQM Simulator for testing Home Assistant integration

import json
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class JSONHandler(BaseHTTPRequestHandler):
    # Set this to True to enable random 30-second delays
    ENABLE_RANDOM_DELAY = False

    # Set this to True to enable connection refused errors
    ENABLE_CONNECTION_REFUSED = False

    # Set this to true to enable random connection refused errors (50% chance)
    ENABLE_RANDOM_CONNECTION_REFUSED = False

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

        RESPONSE = {
            "data": {
                "did": "001D0A100021",
                "name": "AQM-III_Outdoor",
                "ts": 1772411237,
                "conditions": [
                {
                    "lsid": 0,
                    "data_structure_type": 6,
                    "temp": 79.86968,
                    "hum": 51.67798,
                    "dew_point": 60.49641,
                    "wet_bulb": 67.34972,
                    "heat_index": 79.86968,
                    "pm_1_last": 0.532973,
                    "pm_2p5_last": 0.626853,
                    "pm_10_last": 0.688284,
                    "pm_1": 0.532973,
                    "pm_2p5": 0.626853,
                    "pm_2p5_last_1_hour": 0.976856,
                    "pm_2p5_last_3_hours": 0.97408,
                    "pm_2p5_last_24_hours": 3.437191,
                    "pm_2p5_nowcast": 0.9,
                    "pm_10": 0.688284,
                    "pm_10_last_1_hour": 1.421958,
                    "pm_10_last_3_hours": 1.365617,
                    "pm_10_last_24_hours": 4.058475,
                    "pm_10_nowcast": 1.3,
                    "last_report_time": 1772411237,
                    "pct_pm_data_last_1_hour": 100,
                    "pct_pm_data_last_3_hours": 100,
                    "pct_pm_data_nowcast": 100,
                    "pct_pm_data_last_24_hours": 100
                }
                ]
            },
            "error": 0
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(RESPONSE).encode("utf-8"))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 81), JSONHandler)
    print("Serving JSON on port 81...")
    server.serve_forever()
