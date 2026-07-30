import re

def extrair_cards(soup):

    lista = []

    cards = soup.find_all(
              "div",
              class_=re.compile(r"bg-\[#f6f6f3\]")
          )

    for card in cards:
        nome = card.find("h2")
        spans = card.find_all("span", class_=re.compile("font-semibold"))
        
        registro = {
            "NOME": nome.get_text(strip=True) if nome else "",
            "DATA_NASCIMENTO": spans[0].get_text(strip=True) if len(spans) > 0 else "",
            "DATA_FALECIMENTO": spans[1].get_text(strip=True) if len(spans) > 1 else "",
             "LINK": card.find("a")["href"] if card.find("a") else ""
        }
        

        lista.append(registro)

    return lista