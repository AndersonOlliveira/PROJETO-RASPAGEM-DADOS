from datetime import datetime,timedelta,date
from Logs import ClassLogger
from parserPagina.pontaGrossa import extrair_links as parser_ponta
from utils.data import obter_ultimos_dias
from utils.unicode import remover
import re



def extrair_cards(self,soup):
     

        try:

            return extrair_links(self, soup)
            
        except Exception as e:
               ClassLogger.logging.error(
                   f"Erro fatal na execução: {e}",
                   exc_info=True
               )
               return [] 


def processar_dados(self, soup):
        try:
            registros = self.extrair_cards(soup)
            print(f"REGISTROS EXTRAIDOS {registros}")
            return registros
        except Exception as e:
            ClassLogger.logging.error(
                f"Erro fatal na execução: {e}",
                exc_info=True
            )
            return []

def extrair_links(self,soup):
    try:
        links = set()
        links_busca = []
        # tabela = soup.find("table")
        # print(tabela.attrs)
        tabela = soup.find(
        "table",
        class_=lambda c: c and "dataTable" in c
        )

        if tabela is None:
            return []

        linhas = tabela.find("tbody").find_all("tr")
       
        for linha in linhas:
            colunas = linha.find_all("td")
            primeiro_td = colunas[0]

            nome = primeiro_td.find("strong").get_text(strip=True)

            descricao = primeiro_td.get_text(" ", strip=True)

            cidade = colunas[1].get_text(strip=True)

            data = colunas[2].get_text(strip=True)

            match = re.search(r"(\d+) anos", descricao)
            idade = match.group(1) if match else "IDADE NÃO INFORMADA"

            

            link = f"https://dlcorconvenios.com.br/memorial/{remover(nome.replace(" ", "-"))}"
            data_aniversario = montar_dados(self, link,url=None)
            links_busca.append({
                "NOME": nome if nome else "NOME NÃO INFORMADO",
                "DESCRICAO": descricao if descricao else "DESCRIÇÃO NÃO FOI INFORMADA",
                "CIDADE": cidade if cidade else "CIDADE NÃO FOI INFORMADA",
                "DATA_FALECIMENTO": data if data else "DATA DE FALECIMENTO NÃO INFORMOU",
                "DATA_NACIMENTO": data_aniversario,
                "LINK": link if link else "LINK NÃO CRIADO",
                "IDADE": idade
            })

        # print(links_busca)

     
        return links_busca
    except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {e}",exc_info=True)
            return [] 


def montar_dados(self,link_url,url):
    try:
        dados = {}
        detalhe = self.client.get(link_url)
      
        datas = [
            span.get_text(strip=True)
            for span in detalhe.select("span.elementor-icon-list-text")
        ]

        data_nascimento = datas[0] if len(datas) > 0 else "DATA DE NACIMENTO NÃO INFORMADA"
        data_falecimento = datas[1] if len(datas) > 1 else "DATA DE FALECIMENTO NÃO INFORMADA"

        return data_nascimento
      
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
        return {}   
   
     