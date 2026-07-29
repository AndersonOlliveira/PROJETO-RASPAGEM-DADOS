from config.config import URL_INICIAL
from downloads.request import pull_request
from parser.cards import extrair_cards
from parser.paginacao import extrair_links
from utils.csv import salvar_csv
from Logs import ClassLogger


def iniciar():

    fila = [URL_INICIAL]

    visitadas = set()

    while fila:

        url = fila.pop(0)

        if url in visitadas:
            continue

        print(f"Processando {url}")

        visitadas.add(url)

        soup = pull_request(url)

        registros = extrair_cards(soup)

        salvar_csv(registros)

        links = extrair_links(soup)

        for link in links:

            if link not in visitadas:

                fila.append(link)

    ClassLogger.logging.info("Finalizado")