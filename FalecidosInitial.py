import time
from threading import Timer
from Logs import ClassLogger
# from Mail.ClassMail import enviar_email_all
from Processor.ClassProcessor import Processor


if __name__ == "__main__":
    instance = Processor(max_workers=2, batch_size=5)
    
    resultado_fluxo = instance.executar_ciclo()
 
   
    try:
    
            ClassLogger.logger.info("\nIniciando Processo para captura dos dados")
            print(f"Resultado do fluxo: {}")

              
             
    except KeyboardInterrupt:
            # Permite parar o script com Ctrl+C no terminal
           ClassLogger.logger.info("\nEncerrando loop por comando do usuário (Ctrl+C).")
                # break
    except Exception as e:
                # Lida com erros inesperados e continua o loop
            ClassLogger.logger.info(f"[{time.strftime('%H:%M:%S')}] Erro inesperado: {e}. Continuará em 30 segundos.")
            enviar_email_all(f"[{time.strftime('%H:%M:%S')}] Erro inesperado: {e}. Continuará em 30 segundos.")
            