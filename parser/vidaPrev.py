
from datetime import datetime



def extrair_cards(soup):

    blocos = soup.find_all('div', class_="bg-white rounded-lg shadow-sm overflow-hidden group flex flex-col h-full")
    registros = []

    for bloco in blocos:
   

        falecimento = bloco.find("div", class_="absolute top-3 right-3 bg-secondary text-white text-[10px] font-bold px-2 py-1 rounded uppercase")
        cidade = bloco.find('p',class_="text-gray-500 text-[12px] mb-4 flex items-center justify-center gap-1")
        nome = bloco.find("h3", class_="text-primary text-lg font-black uppercase leading-tight mb-1")
        img = bloco.find("img")
        link = bloco.find("a")
      
        if nome:
            registro = {
                "NOME": nome.get_text(strip=True),
                "CIDADE":cidade.get_text(strip=True),
                "DATA_FALECIMENTO": falecimento.get_text(strip=True),
                "IMG": img.get("src"),
                "LINK":link.get("href"),
                "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
            }

        
        registros.append(registro)


    return registros
