from datetime import datetime
from Logs import ClassLogger
import re


def extrair_cards(self,soup):

    try:
        div_mae = soup.find_all('div', class_="card-falecimento single")
        if div_mae:
            registro =[]
                
            for bloco in div_mae:
                registros = {}
                
                texto = bloco.get_text(strip=True).upper()
                nome = bloco.find('h3')
                nome = nome.get_text()
                registros['NOME'] = nome
                descricao = bloco.find('p', class_="descricao-ocorrido")
                descricao_completa = bloco.find('div', class_="descricao").get_text()
                # print(descricao_completa)
                data_hora = re.search(r"Ocorrido às ([\d:]+) do dia ([\d/]+)", descricao_completa).group(1)
               
                pais = re.search(r"filho de (.*?) e ([^,]+)", descricao_completa)
                filhos = re.search(r"deixando os filhos:\s*(.*?)\.", descricao_completa)
                residencia = re.search(r"Residia no (.*?) em ([^\n\.]+)", descricao_completa)


                texto = descricao.get_text()
                idade = re.search(r"(\d+)\s+anos", descricao.get_text()).group(1)
                registros['IDADE'] = idade
                datas = re.findall(r"\d{2}/\d{2}/\d{4}", texto)
                registros['DATA_FALECIMENTO'] =  ",".join(datas)
                registros['DATA_CAPTURA'] =  datetime.now().strftime("%d/%m/%Y %H:%M")
                registros['DATA_HORA'] = data_hora
                registros['PAIS'] = [pais.group(1).strip(), pais.group(2).strip()] if pais else []
                registros['FILHOS'] =  [f.strip() for f in filhos.group(1).replace(" e ", ",").split(",")] if filhos else []
                registros['RESIDENCIA'] = {"bairro": residencia.group(1).strip() if residencia else None, "cidade": residencia.group(2).strip() if residencia else None}

                registro.append(registros)



        return registro 

    except Exception as e:
            ClassLogger.logging.error(
                f"Erro fatal na execução: {e}",
                exc_info=True
            )
            return []

        