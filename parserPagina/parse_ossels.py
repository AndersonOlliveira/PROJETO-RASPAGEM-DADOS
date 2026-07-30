from urllib.parse import urljoin

def extrair_links(soup, url_base):

    urls = []

    ul = soup.find("ul", class_="pagination")

    if not ul:
        return urls

    for a in ul.find_all("a", href=True):

        href = a["href"]

        urls.append(urljoin(url_base, href))

    return urls