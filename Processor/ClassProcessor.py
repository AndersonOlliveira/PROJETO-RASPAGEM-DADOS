import threading
from datetime import datetime
import time
from Logs import ClassLogger
from utils.CrawlerStats import enviar_relatorio_email,enviar_email_all
from Tratamentos.ProcessoDados import Process
from Tratamentos.Normlizar import arquivos_process
from parser.grupoangelus import extrair_cards as parser_grupo
from parser.vidaPrev import extrair_cards as parser_vdprev
from parser.new14Parser import extrair_cards as parser_news
from parser.consonifunerais import extrair_cards as parser_consoni
from parser.ggo import extrair_cards as parser_ggo
from parser.ossel import extrair_cards as parser_ossel
from parser.parser_arvore import extrair_cards as parser_arvore
from parser.parser_pmfi import extrair_cards as parser_pmfi
from parser.parser_orsola import extrair_cards as parser_ors
from parser.parser_ponta import extrair_cards as parser_ponta
from parser.parser_ponta_dados import extrair_cards as parser_ponta_dados
from parser.parser_dlconvencios import extrair_cards as parser_dl
from parser.parser_aracatuba import extrair_cards as parser_aracatuba
from parserPagina.consonifunerais import extrair_links as parser_consoni_div
from parserPagina.vidaPrev import extrair_links as parser_vida_href
from parserPagina.parse_ossels import extrair_links as parse_ossel_link
from parserPagina.ggoInterno import extrair_links as parse_gg_link
from parserPagina.arvoreVida import extrair_links as parse_arvore_div
from parserPagina.orsolaPage import extrair_links as orsolaPage
from parserPagina.pontaGrossa import extrair_links as PontaGrossaPage
from parserPagina.Angelus import extrair_links as angeleus
from utils.CrawlerStats import CrawlerStats
from utils.obter_servidor import obter_servidores

from downloads.RequestClient import RequestClient

import pandas as pd
from pathlib import Path


class Processor:
    def __init__(self, max_workers: int = 10, batch_size: int = 1000):
        # self.config = ConectionClass.DbConfig()
        self.max_workers = max_workers
        self.max_workers_conn = 2
        self.batch_size = batch_size
        # self.client = RequestClient()
        self.stats = CrawlerStats()
        self.client = RequestClient(self.stats)
        # self.client.salvar_erros(pasta)
        # self.idProcesso = idProcesso
        self.servidor = 'https://obituario.grupoangelus.com.br/g/4'
        self.consonifunerais = 'https://consonifunerais.com.br/falecidos/'
        self.servidores = {
                    1: {
                        "nome": "grupoangelus",
                        "url": "https://obituario.grupoangelus.com.br/g/4",
                        "parser": parser_grupo,
                        "pagination": True,
                        "pagin": angeleus,
                        "parametros": False
                    },

                    2: {
                        "nome": "consonifunerais",
                        "url": "https://consonifunerais.com.br/falecidos/",
                        "parser": parser_consoni,
                        "pagination": True,
                        "pagin": parser_consoni_div,
                        "parametros": False
                    },
                    3: {
                        "nome": "vidaprev",
                        "url": "https://www.vidaprev.com.br/falecimentos",
                        "parser": parser_vdprev,
                        "pagination": True,
                        "pagin": parser_vida_href,
                        "parametros": False
                    },

                    4: {
                        "nome": "ossel",
                        "url": "https://obituario.ossel.com.br/",
                        "parser": parser_ossel,
                        "pagination": True,
                        "pagin": parse_ossel_link,
                        "parametros": False
                    }, 
                        5: {
                        "nome": "14news",
                        "url": "https://14news.com.br/obituario/",
                        "parser": parser_news,
                        "pagination": True,
                        "pagin": parser_consoni_div,
                        "parametros": False
                    },
                    6: {
                        "nome": "ggo-interno",
                        "url": "https://ggo-interno.com.br/obituario/",
                        "parser": parser_ggo,
                        "pagination": True,
                        "pagin": parse_gg_link,
                        "parametros": True
                    }, 
                    7: {
                        "nome": "arvorespelavida",
                        "url": "https://arvorespelavida.org.br/obituario/",
                        "parser": parser_arvore,
                        "pagination": True,
                        "pagin": parse_arvore_div,
                        "parametros": False
                    },
                    8: {
                        "nome": "pmfi",
                        "url": "https://www3.pmfi.pr.gov.br/PSIPortal/SircofWeb/Formularios/wfrmSircObituario_Site.aspx",
                        "parser": parser_pmfi,
                        "pagination": False,
                        "pagin": parse_arvore_div,
                        "parametros": False
                    },
                    9: {
                        "nome": "orsola",
                        "url": "https://www.orsola.com.br/notas-de-falecimentos/",
                        "parser": parser_ors,
                        "pagination": True,
                        "pagin": orsolaPage,
                        "parametros": False
                    } , 10: {
                        "nome": "pontaGrossa",
                        "url": "https://app.pontagrossa.pr.gov.br/sisppg/servico_funerario/internet/mostra_hoje.php",
                        "parser": parser_ponta,
                        "pagination": False,
                        "pagin": PontaGrossaPage,
                        "parametros": False,
                        "tdados": parser_ponta_dados
                    }, 11: {
                        "nome": "dlcorconvenios",
                        "url": "https://dlcorconvenios.com.br/obituario/",
                        "parser": parser_dl,
                        "pagination": False,
                        "pagin": PontaGrossaPage,
                        "parametros": False,
                        "tdados": parser_ponta_dados
                    },
                      12: {
                        "nome": "aracatuba",
                        "url": "https://s126.asp.srv.br:446/tributario.pm.aracatuba.sp/com.asp.tributario.externo.wpconsultavelorioext",
                        # "url": "https://s126.asp.srv.br:446/tributario.pm.aracatuba.sp/PublicTempStorage/eewcConsultaVelorio-3951.xlsx",
                        "parser": parser_aracatuba,
                        "pagination": False,
                        "pagin": False,
                        "parametros": False,
                        "tdados": False,
                        "baixar": True
                    }
                }
        # self.parsers = {
        # 1: parser_grupo,
        # 2: parser_consoni,
        # 3: parser_ggo,
        # 4: parser_ossel
        # }
       
        self.servidor_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        self.batch_counter_status1 = 0
        self.batch_counter_status2 = 0
        self.batch_counter_status4 = 0
        self.qtPage = 160 # resultado na tela e apresentado somente 160 registros 
        self.indicePage = 1
        self.time_sleps = 2
        self.periodo = 'SEMANAL'
        self.true = True
        self.false =False
        self.parar = False
        # self.todos_resultados = []
        self.batch_size_verify = 50
        self.lock = threading.Lock()
        # self.db = ConectionPool.DbPool(maxconn=self.max_workers)

    def executar(self):
        inicio = datetime.now()
        ClassLogger.logging.info("=" * 80)
        ClassLogger.logging.info(f"Iniciando Consulta Site - {inicio}")
        time.sleep(2)
        ClassLogger.logging.info("=" * 80)

        try:
            # print(obter_servidores(self,[1, 7, 12]))
            registros = obter_servidores(self,[10])

            total_processados = Process(self,registros)

            # ENVIA 
            try:
                dados_relatorio = self.stats.todos_resultados
            except Exception:
                if isinstance(self.stats, list):
                    dados_relatorio = self.stats
                else:
                    dados_relatorio = getattr(self.stats, 'todos_resultados', self.stats)

            enviar_relatorio_email(dados_relatorio)

            
            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()
            ClassLogger.logging.info("---" * 80)
          

        except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {str(e)}")
            error = f"Erro fatal na execução: process_api {str(e)}"
            corpo = f"""<h2 style="color:red;">Falha no processo de Captura e tratamento dos dados</h2> <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Mensagem:: {error}</p>"""
            enviar_email_all(corpo)

        pass
             
    def processar_arquivos(self):
        inicio = datetime.now()
        ClassLogger.logging.info("=" * 80)
        ClassLogger.logging.info(f"Inicio proceso nomarlização dos dadose - {inicio}")
        time.sleep(2)
        ClassLogger.logging.info("=" * 80)
        try:
            # print(obter_servidores(self,[1, 7, 12]))
                    
            total_processados = arquivos_process(self)
        
            ClassLogger.logging.info(f"minha quantidade de dados processados :  {total_processados}")
                  
            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()
            ClassLogger.logging.info("---" * 80)
                  
        
        except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {str(e)}")
            error = f"Erro fatal na execução: process_api {str(e)}"
            corpo = f"""<h2 style="color:red;">Falha no processo de Captura e tratamento dos dados</h2> <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Mensagem:: {error}</p>"""
                  
        
        finally:
            ClassLogger.logging.error(f"Aplicação finalizada!")
        
             
 


    def executar_ciclo(self):
        self.executar() 
        # PROCESSAR OS DADOS CAPTURADOS
        # self.processar_arquivos() 

       
        

  