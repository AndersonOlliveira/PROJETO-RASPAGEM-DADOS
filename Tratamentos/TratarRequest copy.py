from types import SimpleNamespace
import pandas as pd
from pathlib import Path
import re
from .ProcessoDados import pull_request 

def process_tratar_pull_request(soup):

    csv_path = Path("tabela_populada.csv")
    primeira_pagina = True

    while soup:

        cards = soup.find_all(
            "div",
            class_=re.compile(r"bg-\[#f6f6f3\]")
        )

        lista = []

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

        if lista:
            df = pd.DataFrame(lista)

            df.to_csv(
                csv_path,
                sep=";",
                index=False,
                encoding="utf-8-sig",
                mode="a" if csv_path.exists() else "w",
                header=not csv_path.exists()
            )

        # procura botão Próxima Página
        nav = soup.find(
            "nav",
            class_="flex items-center justify-center gap-4 py-6"
        )

        if not nav:
            break

        proximo = nav.find("a")

        if not proximo:
            break

        href = proximo.get("href")

        if not href:
            break

        url = "https://obituario.grupoangelus.com.br" + href

        print(f"Buscando: {url}")

        request_obj = SimpleNamespace(servidor=url)

        # Nova página
        soup = pull_request(request_obj)

    print("Finalizado.")