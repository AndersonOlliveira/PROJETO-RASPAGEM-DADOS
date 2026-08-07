# Processor/GeneXus/Grid.py

from copy import deepcopy
from Processor.GeneXus.payloads import payload_consulta_velorio

class GeneXusGrid:

    def __init__(self, client, url, payload):
        self.client = client
        self.url = url
        self.payload = payload

    def buscar_pagina(self, pagina):

        # body = copy.deepcopy(self.payload)
        body = payload_consulta_velorio()

        print(f"MEU {body}")

        estado = body["parms"][-2]
        estado["CurrentPage"] = pagina

        return self.client.post_json(self.url, body)