import threading
import time
import requests
import config

shared_state = {
    'data':    None,
    'updated': False,
}
_lock = threading.Lock()


def _poll_loop():
    url     = f'{config.API_BASE_URL}/api/display/latest'
    headers = {'x-api-key': config.API_KEY}

    while True:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                payload = resp.json()
                with _lock:
                    shared_state['data']    = payload.get('data')
                    shared_state['updated'] = True
            elif resp.status_code == 204:
                with _lock:
                    shared_state['data']    = None
                    shared_state['updated'] = True
            # network error or other status → keep last state
        except Exception:
            pass

        time.sleep(config.POLL_INTERVAL)


def start():
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()


def read_state():
    with _lock:
        data    = shared_state['data']
        updated = shared_state['updated']
        shared_state['updated'] = False
    return data, updated
