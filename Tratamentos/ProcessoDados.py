from Logs import ClassLogger

from services.crawler import iniciar

def Process(self):
    ClassLogger.logging.info('ACESSANDO O PROCESS PARA ENVIAR OS DADOS')

    #1 PARA  grupoangelus
    #2 PARA  consonifunerais
    # PARA  ggo-interno.
    #3 PARA  VIDA PREV
    # PARA  orsola
    # PARA  aracatuba
    # PARA  pmfi
    #5 PARA  14news
    print(f"SERVIDORES {self.servidores[2]}")

    servidor = self.servidores.get(2)

    # print(servidor)
    # return

    try:
        if servidor: 
            iniciar(self,servidor) 
    
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        


            
    

        
    