from datetime import datetime
from Logs import ClassLogger
from downloads.request import pull_request
from downloads.RequestClient import RequestClient


def extrair_cards(self,soup):

    print(f"ESTOU SAINDO NA ARVORE? ")

    try:
        
        lista_pull = []

        links_busca_individual = soup.find_all(
                "div", class_="obituario-inner")

       
        for links in links_busca_individual:
            registro = {}
            # print(f"{links.find("a")["href"] if links.find("a") else ""}")
            busca_links = links.find("a")["href"] if links.find("a") else ""
           
            if busca_links:
                # result_soup =  pull_request(busca_links)
                # RequestClient.get should be called without an undefined 'self'.
                # If get is an instance method, instantiate RequestClient();
                # otherwise call it as a class/static method.
                # instantiate RequestClient and call its instance method
                client = RequestClient()
                result_soup = client.get(busca_links)
                p_tag = result_soup.find("p", class_="info-nome")
                nome =  p_tag.get_text(strip=True).upper()
                registro['NOME'] = nome
                registro['DATA_CAPTURA'] = datetime.now().strftime("%d/%m/%Y %H:%M"),
                ul_tag = result_soup.find_all("ul", class_="info-dados")
                for ul in ul_tag:
                    for li in ul.find_all("li"):
                        chave = li.find("span").get_text(strip=True)
                        valor = li.get_text(strip=True).replace(chave, "")
                        registro[chave.upper()] = valor.upper()

           
           
            lista_pull.append(registro)

            # print(lista_pull)
       
        return lista_pull
            

    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        

