import os
import smtplib
import traceback
from Logs import ClassLogger
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()

def enviar_email_all(corpo):
    msg = EmailMessage()
    msg['Subject'] = os.getenv('SMTP_SUBJECT')
    msg['From'] = os.getenv('SMTP_USER')
    msg['To'] = os.getenv('SMTP_DESTINATION')
    msg.set_content(corpo,subtype='html')  # Define o conteúdo como HTML
    try:
        with smtplib.SMTP(os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT')) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)

            return True
    except smtplib.SMTPException as e:
             ClassLogger.logging.info(f"Erro ao enviar e-mail: {e}" , exc_info=True) # Captura erros de SMTP
    
    except Exception as e:
          print(traceback.format_exc())
          ClassLogger.logging.warning(f"ERRO no envio do e-mail {traceback.format_exc()}")
          print(f"Erro inesperado: {e}", exc_info=True)
          raise

