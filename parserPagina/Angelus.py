
from urllib.parse import urljoin

def extrair_links(soup,url):

    print(f"ESTOU SAINDO PARA PEGAR OS LINKS PARA A PESQUISA")

    urls = []

    nav = soup.find("nav", class_="flex items-center justify-center gap-4 py-6")
    if not nav:
        return urls

    if nav:
        for a in nav.find_all("a", href=True):
            urls.append(urljoin("https://obituario.grupoangelus.com.br/g/4?",a["href"]))

    # print(f"{urls}")

    return urls