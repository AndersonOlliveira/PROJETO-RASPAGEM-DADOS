from config.config import URL_BASE

def extrair_links(soup,url):

    urls = []

    nav = soup.find("nav")

    print(f"MEU NAV {nav}")

    # return

    if not nav:
        return urls
    else:
        nav = soup.find("div", class_="e-load-more-anchor")



        for a in nav.find_all("a"):

            href = a.get("href")

            if href:
                urls.append(url + href)

    return urls