import traceback
from Logs import ClassLogger
from tabulate import tabulate
from datetime import datetime
from Conexao import ConectionClass
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from Mail.ClassMail import enviar_email_all
from utils.auxliares import auxliares


def fontes_inserts(self,urls):

    print(f"ESTOU SAINDO PARA INSERIR A URL DE BUSCA?")

    # print(f"SELF ENVIADO {self.db} ")
    # return

    
    query = """
           INSERT INTO fontes_download.obito_download
               (periodizacao, data_captura, link_captura)
           VALUES 
               (%s, %s, %s) RETURNING id; """

    try:
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                    cursor.execute(query, (
                        self.periodo,
                        datetime.now().strftime("%Y-%m-%d"),
                        urls
                        ))
                    # The cursor is closed when this context exits.
                    novo_id = cursor.fetchone()[0]
            with self.lock:
            
                self.batch_counter_status1 += 1
            
                if self.batch_counter_status1 >= 1:
                     conn.commit()
                self.batch_counter_status1 = 0

                ClassLogger.logging.info(f"id Retornano vindo do insert {novo_id} ")
                return novo_id
    except Exception as e:
      print(traceback.format_exc())
      ClassLogger.logging.error(f"Erro ao caputura id retornado :: - {repr(e)}")


#inserir o lote dos registos
# def insert_base_interpol(self, registro: dict, conn, falha_ids):
def insert_base_obito(self,registro):
    # exits = False
    exits = exists_by_name(self,registro['NOME'],registro['DATA_FALECIMENTO'])

    print(f"MEUS DADSOS {exits}")

    if not exits:
        print(f"NOME INFORMADO  {registro}")
        if registro['DATA_FALECIMENTO'] == "0000-00-00":
            registro['DATA_FALECIMENTO'] = None
        if registro['ANO_NASCIMENTO_INFORMADO'] == "0000-00-00":
            registro['ANO_NASCIMENTO_INFORMADO'] = None
   
        try:
            query = """INSERT INTO obito_captura.obito_dados(
	                nome, idade, data_falecimento, ano_nascimento_estimado, link_fonte, data_nascimento, cidade,data_captura)
                    VALUES  (%s,%s, %s, %s, %s, %s, %s, %s) RETURNING obito_id;"""
            print(query)
            print((
                registro['NOME'],
                registro['IDADE'],
                registro['DATA_FALECIMENTO'],
                registro['ANO_NASCIMENTO_ESTIMADO'],
                registro['LINK_FONTE'],
                registro['ANO_NASCIMENTO_INFORMADO'],
                registro['CIDADE']
            
                ))
            # if 'DATA NÃO INFORMADA' in registro['ANO_NASCIMENTO_ESTIMADO']:
            #     registro['ANO_NASCIMENTO_ESTIMADO'] = 0000   

            # if 0 in registro['ANO_NASCIMENTO_INFORMADO']:
            #     registro['ANO_NASCIMENTO_INFORMADO'] = 0000  

            try:
                with self.db.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(query, (
                                registro['NOME'],
                                registro['IDADE'],
                                registro['DATA_FALECIMENTO'],
                                registro['ANO_NASCIMENTO_ESTIMADO'],
                                registro['LINK_FONTE'],
                                registro['ANO_NASCIMENTO_INFORMADO'],
                                registro['CIDADE'],
                                registro['DATA_CAPTURA'],
                                 ))
                            
                            novo_id = cursor.fetchone()[0]

                            if novo_id:
                                return_info_familiar = inser_familiares(self,conn,registro,novo_id)
                                  # INSERIR OS COMPLEMENTOS NA OUTRA TABELA  COM O ID
                            
                        print(f"ID RERTORNADO PARA O ÓBITO {novo_id}")

                        return {
                                "nome": registro['NOME'],
                                "LINK_FONTE" : registro['LINK_FONTE'],
                                "id_obito": novo_id,
                                "status": "sucesso",
                                "info_familiar": return_info_familiar if return_info_familiar else auxliares.INFO_INSERT
                               
                        } 
            except Exception as e:
                    print( traceback.format_exc())
                    ClassLogger.logging.error(f"Falha ao inserir os dados na tabela  obito_dados - {repr(e)}")
                    return {
                        "nome": registro['nome'],
                        "status": "erro",
                        "LINK_FONTE": registro['LINK_FONTE'],
                        "error": traceback.format_exc()
                }
            
        except Exception as e:
            print(traceback.format_exc())
            print(f"ERRRO NO SEGUNDO TRY")
            # print(f"{registro['nome']}")
            return {
               "nome": registro,
               "status": "ERRO_FATAL", 
               "LINK_FONTE": registro['LINK_FONTE']
            }
    else: 
        print(f"SAINDO NO ELSE DA VERIFICACO DOS DADOS")
        return {
               "nome": registro,
               "status": "existes", 
               "LINK_FONTE": registro['LINK_FONTE']
            }
              


def inser_familiares(self,conn,registro,id_obito):
        
                query = """
                    INSERT INTO obito_captura.obito_familiares 
                        (id_obito, familiares_a, familiares_b,info_adicional)
                    VALUES  (%s,%s, %s, %s) RETURNING familiar_id;"""


                print(query)
                print((
                id_obito,
                registro['FAMILIARES_A'],
                registro['FAMILIARES_B'],
                registro['FAMILIARES'],
                ))
        
        
            # return
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (
                        id_obito,
                        registro['FAMILIARES_A'],
                        registro['FAMILIARES_B'],
                        registro['FAMILIARES'],
                    ))

                        return {
                            "ID_FAMILIAR": cursor.fetchone()[0],
                            "status": "sucesso",
                            
                    } 
            
            
                except Exception as e:
                    ClassLogger.logger.error(f"falha em inserir os dados na base  obito_captura.obito_familiares- {repr(e)}")
                    return {
                            "id": id_obito,
                            "status": "erro",
                            # "error": str(e),
                            "error": traceback.format_exc()
                }




def update_data_interpol(conn,id, nat, thumb,country_wanted,data_captura):
    
    query = """UPDATE public.interpol_dados SET 
                  naturalidade = %s , foto = %s , pais_procurado = %s , data_hora_consulta = %s WHERE id_interpol = trim(%s) ;"""
                #   naturalidade = %s , foto = %s WHERE nome_buscado = %s ;"""
     
    try:
         
         with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (nat,thumb,country_wanted,data_captura,id))

                if cursor.rowcount > 0:
                    print(f"TIVE SUCESSO EM ATUALIZAR")
                    return {
                        "status": "sucesso"
                    }
                else:
                    print(f"TIVE FALHA EM ATUALIZAR")
                    return {
                        "status": "erro",
                        "error": "No rows updated"
                    }
    
    except Exception as e:
            ClassLogger.logger.error(f"Erro ao atualizar a NATURALIDADE :: {str(e)}")
           
            return {
                    "status": "erro",
                    "error": str(e)
                }

       
def update_id_interpol(conn,name_person, id):
    
    query = """UPDATE public.interpol_dados SET 
                  id_interpol = %s  WHERE nome = %s ;"""
                #   nome_buscado = %s  WHERE nome = %s ;"""

     
    try:
         
          with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (id,name_person))
             
           
                return {
                    "status": "sucesso"
                }
    
    except Exception as e:
            ClassLogger.logger.error(f"Erro ao atualizar o campo nome Buscado :: {str(e)}")
           
            return {
                    "status": "erro",
                    "error": str(e)
                }

       
              


      
def update_id_interpol_status(self,id,new_status,data):
    
    query = """UPDATE public.interpol_dados SET 
                  situacao = %s, data_baixa = %s  WHERE id_interpol = %s ;"""
                #   nome_buscado = %s  WHERE nome = %s ;"""
     
    try:
         with self.db.get_connection() as conn:
             with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                 cursor.execute(query, (new_status,data,id))
                 
                 return {
                    "status": "sucesso"
                }
    
    except Exception as e:
            ClassLogger.logger.error(f"Erro ao atualizar Baixa do id {id} :: {str(e)}")
           
            return {
                    "status": "erro",
                    "error": str(e),
                    "id_interpol"  : id
                }

       
              
def update_info_fontes(self,idProcesso,qta):

    query = """UPDATE fontes_download.obito_download  SET 
                  processado = %s , quantidade = %s, data_captura = %s  WHERE id = %s ;"""
    

    params = [True, qta, datetime.now().strftime('%Y-%m-%d %H:%M:'), idProcesso]
    print(f"{params}")
    try:

        
        with self.db.get_connection() as conn:
               with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                     with conn.cursor() as cursor:
                           cursor.execute(query, tuple(params))
                           return {
                                  "status": "sucesso"
                            }
              
                     ClassLogger.logging.info(f"Processo finalizado do id {registro['processo_id']} com o Status {True} {datetime.now().strftime('%d/%m/%Y')} ")

    except Exception as e:
          ClassLogger.logging.warning(traceback.format_exc())
          enviar_email_all(traceback.format_exc())
          ClassLogger.logging.error(f"Erro ao atualizar status True :: update_info_process  - {str(e)}")




def buscar_teste(self):

            query = ("""SELECT * FROM fontes_download.interpol_download""")
            
           

            try:
                
                ClassLogger.logger.warn(f"[DEBUG SQL] Parâmetros: ")
            
                with ConectionClass.DbConnect(self.config) as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query)
                        registros = cursor.fetchall()
                       
                        return [dict(registro) for registro in registros]
            
         
            except Exception as e:
                   ClassLogger.logger.error(f"Falha em caputrar os dados buscar_teste - {str(e)}")


            
            
                


# def search_data_interpol(self,idinterpol, cursor,conection):
def search_data_interpol(conn,idinterpol):
            print('CONSIGO PASSAR O ID')

           
            
            #retornando um boleano
#CAMPO VAI SER TROCADO PARA ID INTERPOL
            query = ("""SELECT EXISTS(SELECT 1 FROM public.interpol_dados WHERE id_interpol = trim(%s)) as exists""") 
              # SELECT 1 FROM public.interpol_dados WHERE nome_buscado = %s) as exists""")
            
            

            try:
                # with self.db.get_connection() as conn:
                  with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, (idinterpol.strip(),))
                    return cursor.fetchone()['exists']
            except Exception as e:
                     ClassLogger.logger.error(f"Falha em caputrar os dados o erro search_data_interpol {str(e)}")
           

def exists_by_name(self, person,falecimento):
            print(person)
            print(falecimento)

            if falecimento is None or str(falecimento).strip() in ['', 'NaN', '0000-00-00', '0000-00-00 00:00:00']:
                return False

            try:
                # FORMATA A DATA PARA O PADRÃO DO BANCO E EVITA ERROS COM VALORES INVÁLIDOS
                data_falecimento_formatad = datetime.strptime(str(falecimento).strip(), "%Y/%m/%d").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    data_falecimento_formatad = datetime.strptime(str(falecimento).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    return False

            print(f"DATA FORMATAD? {data_falecimento_formatad}")

            query = """SELECT EXISTS(SELECT 1 FROM obito_captura.obito_dados WHERE UPPER(nome) = UPPER(%s) AND NULLIF(data_falecimento::TEXT, '') = %s) AS exists"""
            try:
                with self.db.get_connection() as conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute(query, (person, data_falecimento_formatad))
                            resultado = cursor.fetchone()['exists']
                            print(f"qual e o resultado {resultado}")
                            return resultado
            except Exception as e: 
                erro_detalhado = traceback.format_exc()
                erro_msg = f"Falha em capturar os dados no obito_captura.obito_dados {str(e)}"
                ClassLogger.logging.error(erro_msg)
                enviar_email_all(f"<h2>Erro processamento </h2><p>{erro_detalhado}</p>")
                
                return {
                    "status": "erro_conexao",
                    "error": erro_detalhado,
                    "COLUNA_ERROR": ",".join(str(valor) for valor in [person, falecimento] if valor is not None),
                    "dados_error": {
                        "person": person,
                        "falecimento": falecimento,
                    }
                }
                
def get_data_match_name_base(self) -> List[Dict]: 
     
     
      query = """SELECT UPPER(nome) as nome, to_char(nascimento, 'YYYY-MM-DD') AS data_nascimento , id_interpol AS id_interpol, nacionalidade, id as id_tabela FROM public.interpol_dados where nacionalidade  
                  LIKE '%BRAZIL%' and cpf is null 
                  GROUP BY nome,nascimento,id_interpol,nacionalidade,id ORDER BY nome"""
      
      
      try:
                    
            with self.db.get_connection() as conn:
                 with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                      cursor.execute(query,)
                      registros = cursor.fetchall()
                
                      if not registros:
                        return None
            
            
                
                
                 return [dict(registro) for registro in registros]
                                    
      except Exception as e:
                    ClassLogger.logger.error(f"Falha em caputrar os dados o erro get_data_match_name_base - {str(e)}")
                  

def get_lista_name_base_interpol(self) -> List[Dict]: 
     
     
      query = """SELECT UPPER(nome) as nome FROM public.interpol_dados
                where to_char(data_consulta_fonte, 'YYYY-MM-DD') != %s ORDER BY RANDOM() limit 1000"""
      
      

      params = (datetime.now().strftime("%Y-%m-%d"),)
      try:
                    
            with self.db.get_connection() as conn:
                 with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                      cursor.execute(query,params)
                      registros = cursor.fetchall()
                
                      if not registros:
                        return None
            
            
                
                 
                 return [dict(registro) for registro in registros]
                                    
      except Exception as e:
                    ClassLogger.logger.error(f"Falha em caputrar os dados o erro get_lista_name_base_interpol - {str(e)}")
                 
#PROCESSO INVERSO PEGANDO OS IDS 
def list_interpol(self) -> List[Dict]:
      query = """SELECT id_interpol AS ID_INTERPOL FROM public.interpol_dados 
                 WHERE id_interpol IS NOT NULL AND situacao = true ORDER BY id_interpol desc"""
      
      
      try:
                    
            with self.db.get_connection() as conn:
                 with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                      cursor.execute(query,)
                      registros = cursor.fetchall()
                
                      if not registros:
                        return None
                 ClassLogger.logger.error(f"MINHA QUANTIDADE {len(registros)} ")
                 return [dict(registro) for registro in registros]
                                    
      except Exception as e:
                    ClassLogger.logger.error(f"Falha em caputrar os dados o erro list_interpol - {str(e)}")
        


def search_from_name_interpol(self, nome_busca, idade_busca, idi_interpol,id_tabela):

        
      
        query = """SELECT cntcpfcgc as cpf FROM 
                    cnt, cntfis 
                    WHERE 
                    cntid = cntfiscnt
                    AND 
                    UPPER(cntnom) = %s  
                    AND 
                    length(cntcpfcgc) = 11 
                    AND cntfisncm = %s"""
        
        try:
           
                with self.db.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query, (nome_busca,idade_busca))
                        resultado = cursor.fetchall()
                            
                        if cursor.rowcount:
                            
                            return {
                                    "status": "sucesso",
                                    "CPF": resultado[0]['cpf'],
                                    "INTERPOL": idi_interpol,
                                    "ID_COLUNA_INTERPOL": id_tabela
                                }
                        else:
                                print(f"TIVE FALHA EM CONSULTAR OS DADOS")
                                return {
                                    "status": "erro",
                                    "error": "NÃO ENCONTRADO NA BASE DA PROSCORE",
                                    "INTERPOL": idi_interpol,
                                    "ID_COLUNA_INTERPOL": id_tabela
                                }
            
                        
                     
                                        
        except Exception as e:
                ClassLogger.logger.error(f"Falha em consultar os dados? - {str(e)}")
                return {
                "status": "erro_conexao",
                "error": str(e),
                "INTERPOL": idi_interpol,
                "ID_COLUNA_INTERPOL": id_tabela
            }
        # finally:
        #         if conn:
        #            self.db.put_connection(conn)



def push_cpf(self,cpf, idcolunaInterpol):
      
    query = """UPDATE public.interpol_dados SET 
                  cpf = %s  WHERE id = %s ;"""
            

  
    
     
    try:
         with self.db.get_connection() as conn:
             with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                 cursor.execute(query, (cpf,idcolunaInterpol))
                 
                 return {
                    "status": "sucesso"
                }
    
    except Exception as e:
            ClassLogger.logger.error(f"Erro ao atualizar Baixa do id {idcolunaInterpol} :: {str(e)}")
           
            return {
                    "status": "erro",
                    "error": str(e),
                    "id_interpol"  : idcolunaInterpol
                }
