from datetime import datetime
from Logs import ClassLogger
import re


def extrair_cards(self,soup):

        try:
             # print(f"{soup}")
            dados = {}
           
       
        
            linhas = soup.find_all("tr")

            for linha in linhas:
                registros = []
                colunas = linha.find_all("td")

                if len(colunas) < 2:
                    continue

                chave = colunas[0].get_text(" ", strip=True).replace(":", "").upper()
                valor = colunas[1].get_text(" ", strip=True).upper()

                dados[chave] = valor

                registros.append(dados)

            
            print(f"LISTA COM OS REGISTROS LOCALIZADO {registros}")


            return registros
            
        except Exception as e:
               ClassLogger.logging.error(
                   f"Erro fatal na execução: {e}",
                   exc_info=True
               )
               return [] 