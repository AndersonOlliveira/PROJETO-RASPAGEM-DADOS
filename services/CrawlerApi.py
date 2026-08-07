class CrawlerApi:


    def executar(self,servidor):
        print(f"SERVIDOR {servidor}")


        return {
            "status": "ok",
            "servidor": servidor
        }
