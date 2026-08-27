import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def extrair_cards(self,soup):

    lista = []

    cards = soup.find_all(
              "div",
              class_=re.compile(r"bg-\[#f6f6f3\]")
          )

    for card in cards:
        nome = card.find("h2")
        spans = card.find_all("span", class_=re.compile("font-semibold"))

        links =  card.find("a")["href"]

        # print(f"url : {links}");
        resultado = urlparse(links)

        url_base = f"{resultado.scheme}://{resultado.netloc}"

                
        registro = {
            "NOME": nome.get_text(strip=True) if nome else "",
            "DATA_NASCIMENTO": spans[0].get_text(strip=True) if len(spans) > 0 else "",
            "DATA_FALECIMENTO": spans[1].get_text(strip=True) if len(spans) > 1 else "",
            "LINK": url_base,
            "LINK_COMPLEMENTO": card.find("a")["href"] if card.find("a") else "",
            "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

       

        lista.append(registro)

    return lista