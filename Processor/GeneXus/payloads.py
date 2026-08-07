

def payload_consulta_velorio():
    return {
        "MPage": False,
        "cmpCtx": "W0009",
        "parms": [
            0,
            0,
            "10",
            1,
            False,
            {
                "s": "0",
                "v": [
                    ["0", "Contém"],
                    ["1", "Início"]
                ]
            },
            0,
            "",
            "    /  /   00:00:00",
            "    /  /   00:00:00",
            # {CurrentPage: 1, OrderedBy: 1, OrderedDsc: false, HidingSearch: 0, PageSize: " 10",…}

        ],
        "hsh": [],
        "objClass": "cemiterio.wcconsultavelorio",
        "pkgName": "com.asp",
        "events": [
            "GRIDPAGINATIONBAR.CHANGEPAGE"
        ],
        "grids": {
            "Grid": {
                "id": 184,
                "lastRow": 10,
                "pRow": ""
            }
        }
    }