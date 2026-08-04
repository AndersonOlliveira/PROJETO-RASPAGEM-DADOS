import unicodedata

def remover(texto):
    normalizado = unicodedata.normalize('NFKD', texto)
    return normalizado.encode('ascii', 'ignore').decode('utf-8')

