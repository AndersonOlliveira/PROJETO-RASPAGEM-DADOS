# SEPARAR ESTES SERVIDORES PARA A BUSCA

def obter_servidores(self, ids):
    if isinstance(ids, int):
        ids = [ids]

    return [
        self.servidores[id]
        for id in ids
        if id in self.servidores
    ]

