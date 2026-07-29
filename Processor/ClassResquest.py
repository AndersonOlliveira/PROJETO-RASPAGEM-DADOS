import random
import threading
import time


class RateLimiter:
    def __init__(self, min_delay=1.0, max_delay=3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.lock = threading.Lock()
        self.last_request = 0
        self.penalty = 0  # aumenta quando dá 403

    def wait(self):
        with self.lock:
            now = time.time()

            delay = random.uniform(self.min_delay, self.max_delay) + self.penalty
            elapsed = now - self.last_request

            if elapsed < delay:
                sleep_time = delay - elapsed
                print(f" Aguardando {sleep_time:.2f}s")
                time.sleep(sleep_time)

            self.last_request = time.time()

    def increase_penalty(self):
        self.penalty = min(self.penalty + 1, 10)  # limite
        print(f" Aumentando penalidade: {self.penalty}")

    def decrease_penalty(self):
        if self.penalty > 0:
            self.penalty -= 0.5
