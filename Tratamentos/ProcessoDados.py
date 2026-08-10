import time
from Logs import ClassLogger
from services.crawler import iniciar
from Mail.ClassMail import enviar_email_all

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

            for servidor in serves:

                print(f"Processando servidor: {servidor['nome']}")

                iniciar(self, servidor)

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro fatal na execução dos servidores: {e}",
            exc_info=True
        )
        enviar_email_all(f"[{time.strftime('%H:%M:%S')}]\nErro fatal na execução dos servidores: {e}")        


            
    

        
    