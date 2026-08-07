
import ssl
import requests
from pathlib import Path
import re
from Logs import ClassLogger 
import pandas as pd
import urllib3
import io
import os
from datetime import datetime
import json
import html
from Processor.GeneXus.Grid import GeneXusGrid


def extrair_cards(self,soup):

        print(f"ESTOU SAINDO NA CHAMADA DO ARACATUBA")
        registro = []

        payload = {"MPage":"false","cmpCtx":"W0009","parms":["true","2026/08/05 00:00:00"],"hsh":[],"objClass":"cemiterio.wcconsultavelorio","pkgName":"com.asp","events":["'DOEXPORT'"],"grids":{"Grid":{"id":184,"lastRow":100,"pRow":""}}}
    
        urll = f"https://s126.asp.srv.br:446/tributario.pm.aracatuba.sp/com.asp.tributario.externo.wpconsultavelorioext?8722e2ea52fd44f599d35d1534485d8ec41cb6a842f508a4b77a7c2f2344af9e,8722e2ea52fd44f599d35d1534485d8ec41cb6a842f508a4b77a7c2f2344af9e,gx-no-cache=1785950454250"


        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
            
            resposta = self.client.post_json(urll, payload)

            print(resposta)
            
            # if resposta and "gxCommands" in resposta:
            #     # 3 - pega a URL retornada
            #     arquivo = resposta["gxCommands"][0]["redirect"]["url"]
            #     print(f"EXECEL? {arquivo}")
            # 4 - baixa o Excel
            # excel = self.client.session.get(
            #     "https://s126.asp.srv.br:446" + arquivo
            # )

            # print(f"EXECEL? {excel}")
            # lista_pull = []
            # # print(f"MINHA RESPOSTA:: {soup}")

            # campo = soup.find("input", {"name": "W0009GridContainerDataV"})
            # # texto = soup.find("button",class_="btn btn-primary dropdown-toggle")

            # paginas = extrair_primeira_pagina(soup)
          
          
        except Exception as e:
                ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
                return {}   

def extrair_primeira_pagina(soup):
    texto = soup.find_all("div",{"id": "W0009HTML_GRIDPAGINATIONBAR"})
    print(texto)


    return {
        "registros": ...,
        "total_paginas": 117
    }

def processos(self,texto):

    print(texto)
    url = "https://s126.asp.srv.br:446/tributario.pm.aracatuba.sp/com.asp.tributario.externo.wpconsultavelorioext?8722e2ea52fd44f599d35d1534485d8ebd23f8882667a42549d360e621536d6b"
    grid = GeneXusGrid(
                      self.client,
                      url = url)
      
    for pagina in range(1, 118):
                      resposta = grid.buscar_pagina(pagina)
      
                      print(resposta)
      
                      # registros.extend(
                      #     # parser_json(resposta)
                      # )
      
                              # match = re.search(r"Página\s+(\d+)\s+de\s+(\d+)", texto)
      
                  # if match:
                  #     pagina_atual = int(match.group(1))
                  #     total_paginas = int(match.group(2))
      
                  #     print(pagina_atual)
                  #     print(total_paginas)
      
                  # for inp in soup.find_all("input", {"type": "hidden"}):
                  #     nome = inp.get("name")
                  #     valor = inp.get("value")
      
                  # if "Page" in str(nome) or "GRID" in str(nome):
                  #     print(nome, "=", valor)
      
    # if not campo:
    #    return []
    # valor = campo["value"]
      
    #               # converte &quot; para "
    # valor = html.unescape(valor)
      
    #               dados = json.loads(valor)
      
    #               print(len(dados))
    #               # print(valor)
      
    #               CAMPOS = {
    #               "CODIGO": 4,
    #               "NOME": 5,
    #               "DATA_NASCIMENTO": 6,
    #               "IDADE": 7,
    #               "DATA_FALECIMENTO": 8,
    #               "DATA_ENTRADA": 9,
    #               "DATA_SEPULTAMENTO": 10,
    #               "QUADRA": 11,
    #               "TUMULO": 12,
    #               "FUNERARIA": 13,
    #               "CEMITERIO": 14,
    #           }
      
    #               registros = []
      
    #               for linha in dados:
    #                   registros.append({
    #                       campo: linha[indice]
    #                       for campo, indice in CAMPOS.items()
    #                   })
      
                      # print(registros)
      
                  # print(f"MINHA RESPOSTA:: {corpo_da_resposta}")
      
                  # for inputs in corpo_da_resposta:
                  #         print(inputs)
                          # print(inputs.find(name_="W0009GridContainerDataV"))
                      #   print(f"hidden {inputs.find({ input='hidden'})} )
                              
                  # pasta = Path(r"arquivos\aracatuba")
                  # # garantir a criacao da pasta 
                  # pasta.mkdir(parents=True, exist_ok=True)
                  # ClassLogger.logging.info(f'Pasta Criada')
      
                  # if not registro:
                  #     registro = soup
                  # # df = pd.DataFrame(registro)
                  # df = pd.read_excel(io.BytesIO(soup),skiprows=4,header=0).columns.str.upper()
                  
      
                  # print(f"VOU ABRIR O ARQUIVO")
                  # print(df.head())
                  # # 4. Define o caminho do arquivo final
                  # caminho = pasta / 'dados_extraidos.csv'
                  
                 
                  
                  # # 5. Salva direto usando o pandas (SEM 'with open')
                  # df.to_excel(caminho, index=False)
                  # print("Download e geração do XLSX concluídos com sucesso!")
                  
                  # return registro
      
      
                  # if pasta.exists() and pasta.is_dir():
                  #        print(f"pasta existe")
                  #        df = pd.DataFrame(soup.content)
                  #        caminho = pasta / 'dados_extraidos.xlsx'
                  #        with open(caminho, 'w',encoding='utf-8') as arquivo:
      
                  #              df.to_excel(caminho, index=False)
                  #              print("Download concluído com sucesso!")      
      
