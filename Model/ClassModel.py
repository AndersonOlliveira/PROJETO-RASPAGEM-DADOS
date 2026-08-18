from tabulate import tabulate
from typing import Dict, List, Optional, Tuple
from Logs import ClassLogger
from Conexao import ConectionClass
from psycopg2.extras import RealDictCursor
from datetime import datetime
import traceback



def insert_interpol(self,registro: Dict, cursor, connection):
    
    query = """
           INSERT INTO fontes_download.interpol_download 
               (periodizacao, data_captura, link_captura,parametros_captura)
           VALUES 
               (%s, %s, %s,%s) RETURNING id; """

    try:
        cursor.execute(query, (
            registro['periodizacao'],
            registro['data_captura'],
            registro['url'],
            registro['siglas']
            # registro['sucesso']
        ))
     
        
       
      
        with self.lock:
          
            self.batch_counter_status1 += 1
           
            if self.batch_counter_status1 >= 1:
               connection.commit()
               self.batch_counter_status1 = 0

               # RETORNO DO ID PARA REALIZAR O UPDATE
               novo_id = cursor.fetchone()[0]


               ClassLogger.logger.info(f"Status atualizado para ::  - id retornado {novo_id} ")


               return novo_id
    except Exception as e:
      ClassLogger.logger.error(f"Erro ao atualizar status para  id retornado ::  - {str(e)}")


#inserir o lote dos registos
# def insert_base_interpol(self, registro: dict, conn, falha_ids):
def insert_base_obito(self, registro):
    exits = False

    exits = exists_by_name(self,registro['NOME'],registro['DATA_FALECIMENTO'])

    if not exits:
   
        try:
                query = """
                    INSERT INTO  public.cntobitocaptura(
	                    nome, idade, data_falecimento, ano_nascimento_estimado, link_fonte, ano_nascimento, cidade, familiares_a, familiares_b, conjuge, data_captura)
                    VALUES  (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

              

                print(query)
                print((
                registro['nome_completo'],
                registro['sexo'],
                registro['data_nascimento'],
                registro['nacionalidade'],
                registro['idiona'],
                registro['acusacao'],
                registro['thumbnail'],
                registro['data_consulta'],
                registro['hora_consulta'],
                registro['id_interpol'],
                registro['naturalidade'],
                registro['person_sigla_unico']
                ))
        
        
            # return
                # try:
                    
                #     with self.db.get_connection() as conn:
                #         with conn.cursor() as cursor:
                #             cursor.execute(query, (
                                
                #                 registro['nome_completo'],
                #                 registro['sexo'],
                #                 registro['data_nascimento'],
                #                 registro['nacionalidade'],
                #                 registro['idiona'],
                #                 registro['acusacao'],
                #                 registro['thumbnail'],
                #                 registro['data_consulta'],
                #                 registro['hora_consulta'],
                #                 registro['id_interpol'],
                #                 registro['naturalidade'],
                #                 registro['country_wanted'],
                #                 True  #quando inserir recebe true
                #             ))

                #         return {
                #                 "id": registro['id_interpol'],
                #                 "status": "sucesso",
                #                 "person_sigla_unico": registro['person_sigla_unico']
                #             } 
            
            
                # except Exception as e:
                #     ClassLogger.logger.error(f"falha em inserir os dados na base  insert_base_interpol - {repr(e)}")
                #     return {
                #             "id": registro['id_interpol'],
                #             "status": "erro",
                #             "person_sigla_unico": registro['person_sigla_unico'],
                #             'error': str(e)
                # }
        except Exception as e:
            return {
                # "id": registro['id_interpol'],
                # "status": "existente", 
                # "person_sigla_unico": registro['person_sigla_unico']
            }


def insert_data_interpol_new(conn,nome,
                nascimento,
                nacionalidade,
                naturalidade,
                id_interpol,
                sexo,
                acusacao,
                idioma,
                thumbnail,
                data_consulta,
                hora_consulta,
                pais_procurado,person_sigla_unico):
        
                query = """
                    INSERT INTO public.interpol_dados 
                        (nome, sexo, nascimento,nacionalidade,idioma,acusacao,foto,data_consulta_fonte,hora_consulta_fonte,id_interpol,naturalidade, pais_procurado,situacao)
                    VALUES  (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s) """

                # print(f"Registro a ser inserido:")
                # print(f"{nome}")
                # print(f"{nacionalidade}")
                # print(f"{naturalidade}")
                # print(f"{id_interpol}")
                # print(f"{sexo}")
                # print(f"{acusacao}")
                # print(f"{idioma}")
                # print(f"{thumbnail}")
                # print(f"{data_consulta}")
                # print(f"{pais_procurado}")
                # print(f"minha person sigla {person_sigla_unico}")

                print(query)
                print((
                nome,
                sexo,
                nascimento,
                nacionalidade,
                idioma,
                acusacao,
                thumbnail,
                data_consulta,
                hora_consulta,
                id_interpol,
                naturalidade,
                pais_procurado,
                True  #quando inserir recebe true
            ))
        
        
            # return
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (
                           nome,
                           sexo,
                           nascimento,
                           nacionalidade,
                           idioma,
                           acusacao,
                           thumbnail,
                           data_consulta,
                           hora_consulta,
                           id_interpol,
                           naturalidade,
                           pais_procurado,
                           True  #quando inserir recebe true
                        ))

                        return {
                            "id": id_interpol,
                            "status": "sucesso",
                            "person_sigla_unico": person_sigla_unico
                        } 
            
            
                except Exception as e:
                    ClassLogger.logger.error(f"falha em inserir os dados na base  insert_base_interpol - {repr(e)}")
                    return {
                            "id": id_interpol,
                            "status": "erro",
                            "person_sigla_unico": person_sigla_unico,
                            'error': str(e)
                }
        # except Exception as e:
        #     return {
        #         "id": id_interpol,
        #         "status": "existente", 
        #         "person_sigla_unico": person_sigla_unico
        #     }



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

       
              




def update_info_process(self,registro: Dict, cursor, connection):



    query = """UPDATE fontes_download.interpol_download  SET 
                  naturalidade = %s  WHERE id = %s ;"""
    
    set_parts = ["processado = %s"]
    params = [registro['status']]
    if registro['obs'] is not None:
        set_parts.append("obs = %s")
        params.append(registro['obs'])
    query = f"UPDATE fontes_download.interpol_download SET {', '.join(set_parts)} WHERE id = %s"
    params.append(registro['alter_id'])
    
    try:
        cursor.execute(query, tuple(params))
        with self.lock:
          
            self.batch_counter_status1 += 1
           
            if self.batch_counter_status1 >= 1:
               connection.commit()
               self.batch_counter_status1 = 0

            ClassLogger.logger.info(f"Status atualizado do id {registro['alter_id']}  com o Status {registro['status']} {datetime.now().strftime('%d/%m/%Y %H:%M')} ")

    except Exception as  e:
     ClassLogger.logger.error(f"Erro ao atualizar status para :: update_info_process  - {str(e)}")




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
           

def exists_by_name(conn, person,falecimento):

            print(conn)
            print(person)
            print(falecimento)
            
           
            query = """SELECT EXISTS(SELECT 1 FROM public.cntobitocaptura WHERE UPPER(nome) = UPPER(%s) and data_falecimento = (%s)) as exists"""
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query, (person,falecimento))
                        resultado = cursor.fetchall()
                        resultado = cursor.fetchone()['exists']
                        print(f"qual e o resultado {resultado}")
                        return resultado
            except Exception as e:              
                erro_detalhado = traceback.format_exc()
        
                # 2. Registra o erro completo no seu Logger
                ClassLogger.logging.error(
                    f"Falha em capturar os dados no cntobitocaptura.\n"
                    f"Detalhes do Erro:\n{erro_detalhado}"
                )
                
                return False
                
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
