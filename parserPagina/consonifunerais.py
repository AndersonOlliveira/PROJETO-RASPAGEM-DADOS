from config.config import URL_BASE

def extrair_links(soup,url):

    urls = []

    nav = soup.find("div", class_="e-load-more-anchor")

    if not nav:
        return urls

    proxima = nav.get("data-next-page")

    if proxima:
        urls.append(proxima)

    return urls