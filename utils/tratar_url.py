from urllib.parse import urlparse


def e_url_valida(url):
    
    try:
        resultado = urlparse(url)
     
        if resultado.netloc:
            return resultado.netloc
        else:
            return resultado.path
    except Exception:
        return 'FONTE NÃO LOCALIZADA'

