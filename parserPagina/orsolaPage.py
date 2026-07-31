
def extrair_links(soup,url):

    urls = []

    nav = soup.find("div", class_="wp-pagenavi")

    if not nav:
        return urls

    for a in nav.find_all("a", href=True):
        href = a["href"]
        urls.append(href)
        

    return urls