import time
from Logs import ClassLogger
from services.crawler import iniciar
from Mail.ClassMail import enviar_email_all
from utils.info_pastas import abrir_arquivos
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.montarParametros import gerar_urls_ggo

def Process(self,serves):
    ClassLogger.logging.info('ACESSANDO O PROCESS PARA ENVIAR OS DADOS')

    #1 PARA  grupoangelus
    #2 PARA  consonifunerais
    # PARA  ggo-interno.
    #3 PARA  VIDA PREV
    # PARA  orsola
    # PARA  aracatuba
    # PARA  pmfi
    #5 PARA  14news
    #6 PARA  gg-interno
    #7 PARA  arvore
    #8 PARA  pmfi
    #9 PARA  orsola
    #10 PARA  pontaGrossa
    #11 PARA  dlcorconvenios
    #11 PARA  dlcorconvenios


    # print(f"SERVIDORES {self.servidores[8]}")

    # servidor = self.servidores.get(8)

    # print(servidor)
    # return
    # TESTE DE GERAÇÃO DAS URL PARA OS ULTIMO 10 ANOS
    # result_url = gerar_urls_ggo("https://ggo-interno.com.br/obituario/?")

    # print(f"MEU RESULADO DA URL {result_url}")
    executor = None
    try:
        if not serves:
            return
        if serves:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                try:
                    futures = [ 
                    executor.submit(iniciar,self,servidor) for servidor in serves]
                 
                    # for servidor in serves:
                    #      print(f"Processando servidor: {servidor['nome']}")
                    #     # print(f"Processando servidor: {self.max_workers}")
                           
                    #     iniciar(self, servidor)
                    # print(futures)
                        # pasta = f"arquivos/{servidor['nome']}"
                        # registros_atual, diferenca,registros_antigo = abrir_arquivos(pasta)
                    

                except KeyboardInterrupt as e:
                          # Permite parar o script com Ctrl+C no terminal
                        ClassLogger.logging.info("\nEncerrando loop por comando do usuário Processo Dados (Ctrl+C).")
                          # break
                        enviar_email_all(f"[{time.strftime('%H:%M:%S')}]\nEncerrando loop por comando do usuário (Ctrl+C).")
                except Exception as e:
                              # Lida com erros inesperados e continua o loop
                        ClassLogger.logging.info(f"[{time.strftime('%H:%M:%S')}] Erro inesperado: {e}. Continuará em 30 segundos.")
                        enviar_email_all(f"[{time.strftime('%H:%M:%S')}] Erro inesperado: {e}. Continuará em 30 segundos.")
                
           


                

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro fatal na execução dos servidores: {e}",
            exc_info=True
        )
        enviar_email_all(f"[{time.strftime('%H:%M:%S')}]\nErro fatal na execução dos servidores: {e}")        


        
    