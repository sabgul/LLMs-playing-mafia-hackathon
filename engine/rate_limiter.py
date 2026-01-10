import time


class RateLimiter:
    def __init__(self, requests_per_minute):
        self.delay = 60.0 / requests_per_minute
        self.last_call = 0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_call = time.time()