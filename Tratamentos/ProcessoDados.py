import time
from Logs import ClassLogger
from services.crawler import iniciar
from Mail.ClassMail import enviar_email_all
from utils.info_pastas import abrir_arquivos
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    try:
        if serves:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                try:
                    futures = [ 
                    executor.submit(iniciar,self,servidor) for servidor in serves]
                    # for future in as_completed(futures):
                    #     try:
                    #         result = future.result()
                    #         detalhes.append(result) # FAZ AS CONSULTAS INDIVIDUAIS E ADICIONA DENTRO DE DETALHE
                    #         print("✔ Detalhe recebido") 
                    #     except Exception as e:
                    #         ClassLogger.logger.error(f"Erro ao processar a URL: {e}", exc_info=True)
                                        

                    # for servidor in serves:
                    #      print(f"Processando servidor: {servidor['nome']}")
                    #     # print(f"Processando servidor: {self.max_workers}")
                           
                    #     iniciar(self, servidor)
                    #                        # pasta = f"arquivos/{servidor['nome']}"
                                           # registros_atual, diferenca = abrir_arquivos(self,pasta)

                except Exception as e:
                            ClassLogger.logging.error(f"Erro ao processar paginas para localizar as páginas: {e}", exc_info=True)
                            links = None

           


                

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro fatal na execução dos servidores: {e}",
            exc_info=True
        )
        enviar_email_all(f"[{time.strftime('%H:%M:%S')}]\nErro fatal na execução dos servidores: {e}")        


        
    