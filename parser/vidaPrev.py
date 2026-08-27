import re
from Logs import ClassLogger
from datetime import datetime



def extrair_cards(self,soup):

    # print(soup)

    ul = soup.find("ul", class_="flex flex-col py-2")
    
    for a_tag in ul.find_all("a"):
        if a_tag.get("title") == "Falecimentos":
            url = a_tag.get("href")
            # texto = a_tag.get_text(strip=True)
            
            # print(f"Elemento encontrado! Botão: {texto} -> Link retornado: {url}")

    

    blocos = soup.find_all('div', class_="bg-white rounded-lg shadow-sm overflow-hidden group flex flex-col h-full")
    registros = []

    for bloco in blocos:
        falecimento = bloco.find("div", class_="absolute top-3 right-3 bg-secondary text-white text-[10px] font-bold px-2 py-1 rounded uppercase")
        cidade = bloco.find('p',class_="text-gray-500 text-[12px] mb-4 flex items-center justify-center gap-1")
        nome = bloco.find("h3", class_="text-primary text-lg font-black uppercase leading-tight mb-1")
        img = bloco.find("img")
        link = bloco.find("a")
        teste = bloco.find("div", class_="space-y-2")
        tag_homenagem = teste.find("a")
        if tag_homenagem:
            link_homenagem = tag_homenagem.get("href")
            ano_nacimento, data_falecimento,cidade_link = montar_dados(self,link_homenagem)

      
        if nome:
            registro = {
                "NOME": nome.get_text(strip=True),
                "CIDADE":cidade_link,
                # "CIDADE":cidade.get_text(strip=True),
                # "DATA_FALECIMENTO": falecimento.get_text(strip=True),
                "DATA_FALECIMENTO": data_falecimento,
                "IMG": img.get("src"),
                "DATA_NASCIMENTO": ano_nacimento,
                "LINK": url,
                "LINK_COMPLEMENTO": link.get("href"),
                "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
            }

        
        registros.append(registro)


    return registros


def montar_dados(self,link_url):
    # print(f"LINK ENVIADO {link_url}")
    try:
      
        detalhe = self.client.get(link_url)
        div_datas = detalhe.find("div", class_="flex flex-wrap justify-center md:justify-start gap-6 text-gray-500 mb-8 font-medium")

        if div_datas:
            
            datas = div_datas.get_text(strip=True)
            padrao = r"(\d{2}/\d{2}/\d{4})\s*—\s*(\d{2}/\d{2}/\d{4})\s*(.*)"

            match = re.match(padrao, datas)

            if match:
                data_nascimento = match.group(1)
                data_falecimento = match.group(2)
                cidade = match.group(3).strip()
                
                # print(f"Nascimento: {data_nascimento}")
                # print(f"Falecimento: {data_falecimento}")
                # print(f"Cidade: {cidade}")
            else:
                print("Não foi possível extrair os dados.")

    
        return data_nascimento,data_falecimento, cidade
      
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
        return {}   
   