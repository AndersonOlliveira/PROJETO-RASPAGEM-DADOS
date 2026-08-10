import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

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
          print(f"Erro ao enviar e-mail: {e}" , exc_info=True) # Captura erros de SMTP
    
    except Exception as e:
          print(f"Erro inesperado: {e}", exc_info=True)
          raise

    
    # except Exception as e:
    #     print(f"Erro ao enviar email: {e}")
    #     raise
