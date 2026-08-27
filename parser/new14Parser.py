import re
from Logs import ClassLogger
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def extrair_cards(self,soup):

    print(f"ESTOU ACESSADNO OS CARS VINDO DA PAGINA 14 NEWS")
    # print(soup)
    # return

    try:
         
        registros = []

        # Localiza todas as tags h3 que possuem a classe de título de postagem do tema do site
        dados_procura = soup.find_all("div", class_="elementor-post__text")
        
            # for textos in dados_procura:

        for retorno_procura in dados_procura:    

            dados = retorno_procura.find("h3",class_="elementor-post__title")
            nome = dados.get_text(strip=True)
            p_idade = retorno_procura.find('div', class_="elementor-post__excerpt").get_text(strip=True)
            idade = re.search(r"(\d+) anos", p_idade).group(1)
            informacoes = re.search(r"(\d+) anos", p_idade).group(0)
            # Busca o link da notícia individual caso precise mapear posteriormente
            data_falecimento = retorno_procura.find('span', class_="elementor-post-date")
            links = retorno_procura.find("a")["href"] if retorno_procura.find("a") else ""
            resultado = urlparse(links)
            
            url_base = f"{resultado.scheme}://{resultado.netloc}"

            if nome:
                registro = {
                    "NOME": nome,
                    "DATA_FALECIMENTO": data_falecimento.get_text(strip=True),
                    "IDADE": idade,
                    "INFORMACOES": p_idade,
                    "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "LINK": url_base, 
                    "LINK_COMPLEMENTO": retorno_procura.find("a")["href"] if retorno_procura.find("a") else ""
            
            }   

                registros.append(registro)
            
        return registros
    

    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        

