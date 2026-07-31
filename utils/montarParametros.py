from datetime import datetime
from urllib.parse import urlencode

def gerar_urls_ggo(url_base):

    urls = []

    ano = datetime.now().year -1

    for mes in range(1, 13):

        params = urlencode({
            "mes": mes,
            "ano": ano
        })

        urls.append(f"{url_base}?{params}")

    return urls