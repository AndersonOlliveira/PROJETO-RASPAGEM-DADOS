import re
import time
import random
import requests
import threading 

from Logs import ClassLogger
from datetime import datetime
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from Processor.ClassResquest import RateLimiter
# self contem todos as configurações 
# buffer_mensagens_emails =[]
timer_ativo = False
lock_error = threading.Lock()

def pull_request(servidor):
    global buffer_mensagens_emails, timer_ativo, lock_error 
            
    JANELA_COLETA_SEGUNDOS = 60
    soup_page = ""
    erro = False
    lock_erros = threading.Lock()
    acumulo_erros = defaultdict(lambda: {
    "ERROR":0,
    })
    ClassLogger.logging.info(f"ESTOU CHAMANDO A PAGINA PARA PROCESSAR AS CHAMADAS DA URL")    
    ClassLogger.logging.warning(servidor)
    #https://obituario.grupoangelus.com.br/g/4?page=2052  6  registros por pagina7

    session = requests.Session()
    rate_limiter = RateLimiter()


    session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive"
            })
       
    for tentativa in range(3):
        try:
            rate_limiter.wait()
    
            # escolher user-agent (navegador) e aplicá-lo aos headers antes da requisição
            navegador = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            ])
            session.headers["User-Agent"] = navegador
            response = session.get(servidor, timeout=JANELA_COLETA_SEGUNDOS)
            if response.status_code == 403:
                ClassLogger.logging.info(f" 403 detectado (tentativa {tentativa+1})")
                msg_custom = f"Acesso Negado (403). Verifique permissões ou Headers. Detalhes: {servidor}"
                        
                with lock_erros:
                    erro = True
                    acumulo_erros[servidor]["ERROR"] += 1
                    # buffer_mensagens_emails.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg_custom}")
    
                    # Se não houver um timer rodando, inicia um agora
                    if not timer_ativo:
                        timer_ativo = True
                                     # Inicia uma thread separada que vai esperar X segundos antes de enviar tudo
                        threading.Timer(JANELA_COLETA_SEGUNDOS).start()
    
                    ClassLogger.logging.error(f"Erro 403: {msg_custom}")
    
                    rate_limiter.increase_penalty()
                    time.sleep(2)
    
                    continue
    
                rate_limiter.decrease_penalty()
                response.raise_for_status()
        except requests.exceptions.Timeout:
                    soup_page = f"TIMEOUT: Requisição excedeu 5 minutos {servidor}"
                    erro = True
                    ClassLogger.logger.error(f"Timeout na requisição: {servidor}")
        except requests.exceptions.HTTPError as e:
            try:
                detalhes_servidor = e.response.json()
            except:
                detalhes_servidor = e.response.text
    
                status = e.response.status_code
                msg_custom = f"Erro HTTP {status}: {detalhes_servidor}"


           #metodo de busca original para a consulta de dados
        # # resposta = requests.get(servidor, headers={'User-Agent': 'Mozilla/5.0'})
        # response.raise_for_status()

        # soup_page = BeautifulSoup(resposta.text, 'html.parser')
        soup_page = BeautifulSoup(response.text, 'html.parser')

    
        return soup_page

      

    # except requests.exceptions.RequestException as e:
    #     ClassLogger.logging.error(f"Erro ao acessar o site: {e}")
