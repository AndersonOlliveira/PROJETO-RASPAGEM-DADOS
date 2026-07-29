from config.config import URL_BASE
def extrair_links(soup):

    urls = []

    nav = soup.find("nav")

    if not nav:
        return urls

    for a in nav.find_all("a"):

        href = a.get("href")

        if href:
            urls.append(URL_BASE + href)

    return urls