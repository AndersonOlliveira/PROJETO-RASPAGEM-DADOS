import re
from datetime import datetime
from Logs import ClassLogger
from downloads.request import pull_request
# from Processor.ClassProcessor import Processo
def extrair_cards(soup):


    try:
        
        lista_pull = []

        links_busca_individual = soup.find_all(
                "h6",
                # class_="elementor-widget-container")
                class_="elementor-heading-title elementor-size-default")

       
        for links in links_busca_individual:
            # print(f"{links.find("a")["href"] if links.find("a") else ""}")
            busca_links = links.find("a")["href"] if links.find("a") else ""
            if busca_links:
                result_soup =  pull_request(busca_links)
                # result_soup =  Processor.client.get(busca_links)

                print('tenho resultado?\n')
                print(result_soup)

            

      
            nome = result_soup.find("h6", class_="elementor-heading-title elementor-size-default")
        
            if nome:
            #    lista_pull["NOME"] = nome.text.strip()
       
                # Exemplo: pegar blocos de informações
               info_blocks = result_soup.find_all("div", class_="elementor-element elementor-element-c79de40 e-con-full e-flex e-con e-child")
              
       
               for bloco in info_blocks:
                   texto = bloco.get_text(strip=True)
       
                   nomes = nome.text.strip()
                   nascimento = re.search(r"\d{2}/\d{2}/\d{4}", texto).group()
                   falecimento = re.findall(r"\d{2}/\d{2}/\d{4}", texto)[1]
                   cidade = re.search(r"[A-Za-z\s]+- SP", texto).group()
                   idade = re.search(r"Idade:\d+ anos", texto).group().replace("Idade:", "")
                   familiares = re.search(r"Familiares:(.*?)Cerimonias:", texto).group(1).strip()
                   cerimonias = re.search(r"Cerimonias:(.*?)Outas Informações:", texto).group(1).strip()
                   outras_info = re.search(r"Outas Informações:(.*)", texto).group(1).strip()
       
                   dados_justado = {
                       "NOME": nomes,
                       "DATA_NASCIMENTO": nascimento,
                       "DATA_FALECIMENTO": falecimento,
                       "CIDADE": cidade,
                       "IDADE": idade,
                       "FAMILIARES": familiares,
                       "CERIMONIAS": cerimonias,
                       "OUTRAS_INFO": outras_info,
                       "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
                   }
       
           
            lista_pull.append(dados_justado)
       
        return lista_pull
            

    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        

