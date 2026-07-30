import random
import time
import requests

from bs4 import BeautifulSoup
from Logs import ClassLogger
from Processor.ClassResquest import RateLimiter


class RequestClient:
    def __init__(self):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.session.headers.update({
            "User-Agent": self.user_agent(),
            "Accept": "text/html",
            "Connection": "keep-alive"
        })

    def user_agent(self):
        return random.choice([
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Mozilla/5.0 (X11; Linux x86_64)...",
        ])

    def get(self,url):
        for tentativa in range(5):
            try:
                self.rate_limiter.wait()
                self.session.headers["User-Agent"] = self.user_agent()
                resposta = self.session.get(url,timeout=(10,30))
                resposta.raise_for_status()

                return BeautifulSoup(resposta.text,"html.parser")

            except requests.exceptions.ConnectionError as e:
                ClassLogger.logging.warning(f"Timout {url}")

            except requests.exceptions.HTTPError as e:
                ClassLogger.logging.warning(f"HTTP {e.response.status_code}")

        time.sleep(2** tentativa)

        return None
        