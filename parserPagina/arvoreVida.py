from urllib.parse import urljoin
def extrair_links(soup,url):

    urls = []

    nav = soup.find("div", class_="paginacao")

    if not nav:
        return urls

   
    for a in nav.find_all("a", href=True):
   
           href = a["href"]
   
           urls.append(urljoin(url, href))
   
    return urls