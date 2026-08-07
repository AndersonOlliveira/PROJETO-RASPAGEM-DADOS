import random
import time
import requests
import pandas as pd
from utils.erros import salvar_erros
from datetime import datetime
from bs4 import BeautifulSoup
from Logs import ClassLogger
from Processor.ClassResquest import RateLimiter


class RequestClient:
    def __init__(self, stats):
        self.stats = stats
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.session.headers.update({
            "User-Agent": self.user_agent(),
            "Accept": "text/html",
            "Connection": "keep-alive"
        })

        self.erros = [] # ARMAZENA OS ERROS

    def salvar_erros(self,pasta):
        salvar_erros(self.erros,pasta)
        self.erros.clear()

    def user_agent(self):
        return random.choice([
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            # "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            # "Mozilla/5.0 (X11; Linux x86_64)...",
        ])

    def get(self,url):
        for tentativa in range(5):
            try:
                self.rate_limiter.wait()
                self.session.headers["User-Agent"] = self.user_agent()
                resposta = self.session.get(url,timeout=(10,30))
                resposta.raise_for_status()
                self.stats.processada()
                content_type = resposta.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    return BeautifulSoup(resposta.text,"html.parser")
                else:
                    return resposta.content

            except requests.exceptions.ReadTimeout as e:
                # self.stats.url()
                self.stats.timeout()

                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)

                ClassLogger.logging.warning(
                    f"Timeout de leitura ({tentativa+1}/5): {url}"
                )

            except requests.exceptions.ConnectionError as e:
                self.stats.timeout()

                self.adicionar_erro(url,tentativa + 1,e)
                ClassLogger.logging.warning(f"Erro de conexão ({tentativa+1}/5): {url}")

            except requests.exceptions.HTTPError as e:
                self.stats.timeout()
                self.stats.http_error()
                
                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)
                ClassLogger.logging.warning(f"HTTP {e.response.status_code}")
                if e.response.status_code == 404:
                    self.stats.http_error()

                    break
            except requests.exceptions.RequestException as e:
                self.stats.timeout()

                ClassLogger.logging.error(
                    f"Erro Requests: {e}"
                )

        
        time.sleep(2** tentativa)
        # self.erros.append({
        #         "url": url,
        #         "tentativas": tentativa + 1,
        #         "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        #         "erro": str(e)
        #     })

        if self.erros:
            # pasta = Path("arquivos") / nome
            # pasta.mkdir(parents=True, exist_ok=True)
            # nome = self.servidores.get(nome)
            pd.DataFrame(self.erros).to_csv(
                    "arquivos/error/erros.csv",
                    sep=";",
                    index=False,
                    encoding="utf-8-sig"
                )
        return None
    
    def post(self,url,data):
        for tentativa in range(5):
            try:
                self.rate_limiter.wait()
                self.session.headers["User-Agent"] = self.user_agent()
                resposta = self.session.post(url,data=data,timeout=(10,30))
                resposta.raise_for_status()

                self.stats.processada()
                return BeautifulSoup(resposta.text,"html.parser")

            except requests.exceptions.ReadTimeout as e:
                self.stats.timeout()

                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)

                ClassLogger.logging.warning(
                    f"Timeout de leitura ({tentativa+1}/5): {url}"
                )

            except requests.exceptions.ConnectionError as e:
                self.stats.timeout()

                self.adicionar_erro(
                                    url,
                                    tentativa + 1,
                                    e)
                ClassLogger.logging.warning(f"Erro de conexão ({tentativa+1}/5): {url}")

            except requests.exceptions.HTTPError as e:
                self.stats.timeout()
                
                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)
                ClassLogger.logging.warning(f"HTTP {e.response.status_code}")
                if e.response.status_code == 404:
                    break
            except requests.exceptions.RequestException as e:
                self.stats.timeout()

                ClassLogger.logging.error(
                    f"Erro Requests: {e}"
                )

        
        time.sleep(2** tentativa)
        # self.erros.append({
        #         "url": url,
        #         "tentativas": tentativa + 1,
        #         "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        #         "erro": str(e)
        #     })

        if self.erros:
            pd.DataFrame(self.erros).to_csv(
                    "arquivos/error/erros.csv",
                    sep=";",
                    index=False,
                    encoding="utf-8-sig"
                )
        return None
    
    def post_json(self,url,data):
        print(url)
        print(data)
        
        for tentativa in range(5):
            try:
                self.rate_limiter.wait()
                self.session.headers["User-Agent"] = self.user_agent()
                self.session.headers["Content-Type"] ="application/json"
                resposta = self.session.post(url,data=data,timeout=(10,30))
                resposta.raise_for_status()
                self.stats.processada()
                return resposta.content

            except requests.exceptions.ReadTimeout as e:
                self.stats.timeout()

                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)

                ClassLogger.logging.warning(
                    f"Timeout de leitura ({tentativa+1}/5): {url}"
                )

            except requests.exceptions.ConnectionError as e:
                self.stats.timeout()

                self.adicionar_erro(
                                    url,
                                    tentativa + 1,
                                    e)
                ClassLogger.logging.warning(f"Erro de conexão ({tentativa+1}/5): {url}")

            except requests.exceptions.HTTPError as e:
                self.stats.timeout()
                
                self.adicionar_erro(
                    url,
                    tentativa + 1,
                    e)
                ClassLogger.logging.warning(f"HTTP {e.response.status_code}")
                if e.response.status_code == 404:
                    break
            except requests.exceptions.RequestException as e:
                self.stats.timeout()

                ClassLogger.logging.error(
                    f"Erro Requests: {e}"
                )

        
        time.sleep(2** tentativa)
        # self.erros.append({
        #         "url": url,
        #         "tentativas": tentativa + 1,
        #         "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        #         "erro": str(e)
        #     })

        if self.erros:
            pd.DataFrame(self.erros).to_csv(
                    "arquivos/error/erros.csv",
                    sep=";",
                    index=False,
                    encoding="utf-8-sig"
                )
        return None


    def adicionar_erro(self, url, tentativa, erro):

        self.erros.append({
            "url": url,
            "tentativa": tentativa,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "erro": str(erro)
        })
        