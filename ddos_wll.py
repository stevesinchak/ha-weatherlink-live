#Test tool to place a heavy load on your WeatherLink Live device and
# test data caching feature of this integration. 

import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
TARGET_URL = "http://<ip>/v1/current_conditions"
TOTAL_REQUESTS = 100000  # Total number of requests to send
MAX_THREADS = 3      # Number of concurrent threads
TIMEOUT = 5           # Seconds before timing out a request

def send_request(request_id):
    """Sends a single GET request and returns the result."""
    try:
        response = requests.get(TARGET_URL, timeout=TIMEOUT)
        return f"Request {request_id}: Status {response.status_code}"
    except requests.exceptions.ConnectTimeout:
        return f"Request {request_id}: Error - Connection Timed Out"
    except requests.exceptions.ConnectionError:
        return f"Request {request_id}: Error - Connection Refused/Failed"
    except Exception as e:
        return f"Request {request_id}: Error - {str(e)}"

def run_performance_test():
    print(f"Starting test: {TOTAL_REQUESTS} requests across {MAX_THREADS} threads...")
    print(f"Target: {TARGET_URL}\n" + "-"*50)

    results = []
    
    # Using ThreadPoolExecutor to manage concurrency
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Schedule the requests
        futures = [executor.submit(send_request, i) for i in range(1, TOTAL_REQUESTS + 1)]
        
        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(result)

    print("-"*50)
    print(f"Test Complete. Total responses logged: {len(results)}")

if __name__ == "__main__":
    run_performance_test()