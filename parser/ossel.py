import re
from Logs import ClassLogger
from datetime import datetime


def extrair_cards(self,soup):

    print(f"ESTOU ACESSADNO OS CARS VINDO DA PAGINA ORSSEL")
    try:
    

        registros = []
        div_mae = soup.find_all('div', class_="luiz-box")

        for div in div_mae:
            registro = {}

            # Nome (h2)
            nome = div.find("h2")
            if nome:
                registro["NOME"] = nome.get_text(strip=True)
            else:
                registro["NOME"] = "NÃO INFORMADO"

            # Local + data (h3)
            local_data = div.find("h3")
            texto = local_data.get_text(strip=True)
            falecimento = re.search(r"\d{2}/\d{2}/\d{4}", texto).group()
        
            if local_data:
                registro["LOCAL_DATA"] = local_data.get_text(strip=True).replace(" ", "")
                registro["DATA_FALECIMENTO"] = falecimento
            else:
                registro["LOCAL_DATA"] = '0000/00/00'
                registro["DATA_FALECIMENTO"] = '0000/00/00'

            # Texto principal (p)
            texto = div.find("p")
            if texto:
                conteudo = texto.get_text(" ", strip=True)
                idade = re.search(r"aos\s+(\d+)\s+anos", conteudo)
                if idade:
                    registro["IDADE"] = idade.group(1)
                else:
                    registro["IDADE"] = 0

                # Familiares
                familiares = re.search(r"casado\(a\) com (.*?),", conteudo)
                if familiares:
                    registro["CONJUGE"] = familiares.group(1).strip()
                else:
                    registro["CONJUGE"] = "NÃO INFORMADO"

                filhos = re.findall(r"([A-ZÁÉÍÓÚÇ]+)\s(\d+)\sANOS", conteudo)
                if filhos:
                    registro["FILHOS"] = [f"{nome} ({idade} anos)" for nome, idade in filhos]
                else:
                    registro["FILHOS"] = "NÃO INFORMADO"


                registro["TEXTO_COMPLETO"] = conteudo

            registro["DATA_CAPTURA"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            # registro["LINK"] = soup
            registros.append(registro)


        return registros

    

    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        
