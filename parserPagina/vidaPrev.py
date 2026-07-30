
def extrair_links(soup,url):

    urls = []

    nav = soup.find("span", class_="inline-flex rtl:flex-row-reverse shadow-sm rounded-md")

    if not nav:
        return urls

    for a in nav.find_all("a", href=True):
        href = a["href"]
        urls.append(href)
        

    return urls