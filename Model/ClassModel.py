import math
import traceback
import pandas as pd
from Logs import ClassLogger
from tabulate import tabulate
from datetime import datetime
from Conexao import ConectionClass
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from Mail.ClassMail import enviar_email_all
from utils.auxliares import auxliares


def fontes_inserts(self,urls):

    query = """
           INSERT INTO fontes_download.obito_download
               (periodizacao, data_captura, link_captura)
           VALUES 
               (%s, %s, %s) RETURNING id; """

    try:
        with self.pool_raspagem.get_connection() as conn:
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


def cnt_obitos_inserts(self,cntidobito,fonte,ano,data_completa):
   
    query = """INSERT INTO cntobito (cntobitocnt,cntobitoflag,cntobitofcm,cntobitoano) 
            VALUES 
               (%s, %s, %s, %s) RETURNING cntobitocnt; """

    try:
        print(query)
        with self.pool_raspagem.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cntidobito,fonte,ano,data_completa))
                novo_id = cursor.fetchone()[0]
            
            with self.lock:
                self.batch_counter_status1 += 1
                if self.batch_counter_status1 >= 1:
                    conn.commit()
                    self.batch_counter_status1 = 0 
            
            return { 
                "status": 'sucesso',
                "novo_id": novo_id
            } 
    except Exception as e:
        ClassLogger.logging.error(f"Erro ao inserir os dados na cntobito.. : - {traceback.format_exc()}")
        return { "status": 'error', 'msg': str(e) }


#inserir o lote dos registos
def insert_base_obito(self,registro):
    # exits = False
    # exits = exists_by_name(self,registro['NOME'],registro['DATA_FALECIMENTO'])

    # print(f"MEUS DADSOS {exits}")

    # if not exits:
    print(f"NOME INFORMADO  {registro}")
        # TRATAMENTO PARA INSERIR OS DADOS DENTRO DO BANCO 

    if registro['DATA_FALECIMENTO'] == "0000-00-00":
            registro['DATA_FALECIMENTO'] = None
    if registro['ANO_NASCIMENTO_INFORMADO'] == "0000-00-00":
        registro['ANO_NASCIMENTO_INFORMADO'] = None
    if registro['IDADE'] == "nan":
           registro['IDADE'] = None

    idade = registro['IDADE']
    if isinstance(idade, float):
        idade = int(idade) if not math.isnan(idade) else None
        # valor = registro.get("ANO_NASCIMENTO_INFORMADO")

        # if pd.isna(valor):
        #     registro["ANO_NASCIMENTO_INFORMADO"] = None
        # else:
        #     try:
        #         registro["ANO_NASCIMENTO_INFORMADO"] = int(
        #             str(valor)[:4]
        #         )
        #     except (ValueError, TypeError):
        #         registro["ANO_NASCIMENTO_INFORMADO"] = None
            
        # return
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
                registro['CIDADE'],
                type(registro['IDADE']),
                type(registro['ANO_NASCIMENTO_INFORMADO']),
            
                ))
            
         
            # return
        try:
            with self.pool_raspagem.get_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(query, (
                                registro['NOME'],
                                idade,
                                registro['DATA_FALECIMENTO'],
                                sanitize(registro['ANO_NASCIMENTO_ESTIMADO']),
                                registro['LINK_FONTE'],
                                sanitize(registro['ANO_NASCIMENTO_INFORMADO']),
                                registro['CIDADE'],
                                registro['DATA_CAPTURA']
                                 ))
                            
                            novo_id = cursor.fetchone()[0]

                            if novo_id:
                                return_info_familiar = inser_familiares(self,conn,registro,novo_id)
                                  # INSERIR OS COMPLEMENTOS NA OUTRA TABELA  COM O ID

                        return {
                                "nome": registro['NOME'],
                                "LINK_FONTE" : registro['LINK_FONTE'],
                                "id_obito": novo_id,
                                "status": "sucesso",
                                "info_familiar": return_info_familiar if return_info_familiar else auxliares.INFO_INSERT
                               
                        } 
        except Exception as e:
                    ClassLogger.logging.error(f"Falha ao inserir os dados na tabela  obito_dados - {repr(e)}")
                    print(f"nome o erro {registro['NOME']}")
                    return {
                        "nome": registro['NOME'],
                        "status": "ERRO_FATAL",
                        "LINK_FONTE": registro['LINK_FONTE'],
                        "error": traceback.format_exc()
                }
            
    except Exception as e:
        print(f"erro sendo apresentado {e}")
        print(traceback.format_exc())
        error = traceback.format_exc()
        ClassLogger.logging.error(f"Segundo try ao inserir os dados na tabela obito_dados - {error}")
        print(f"nome o erro{registro['NOME']}")
        return {
               "nome": registro,
               "status": "ERRO_FATAL", 
               "LINK_FONTE": registro['LINK_FONTE']
            }
    # else: 
    #     #PEGAR O QUE JÁ EXISTE E TRATAR
    #     return {
    #            "nome": registro,
    #            "status": "existes", 
    #            "LINK_FONTE": registro['LINK_FONTE']
    #         }
              


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


def update_info_fontes(self,idProcesso,qta):

    query = """UPDATE fontes_download.obito_download  SET 
                  processado = %s , quantidade = %s, data_captura = %s  WHERE id = %s ;"""
    

    params = [True, qta, datetime.now().strftime('%Y-%m-%d %H:%M:'), idProcesso]
    print(f"{params}")
    try:

        
        with self.pool_raspagem.get_connection() as conn:
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

def update_cntobito(self,link,ano, data_completa, cntid):

    query = """UPDATE cntobito SET cntobitoflag = %s , cntobitoano = %s,cntobitofcm = %s WHERE cntobitocnt = %s ;"""
    

    params = [link, ano, data_completa, cntid]
    print(f"{params}")
    try:

        
        with self.pool_raspagem.get_connection() as conn:
               with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    with conn.cursor() as cursor:
                        cursor.execute(query, tuple(params))
                        with self.lock:
                            self.batch_counter_status1 += 1
                            if self.batch_counter_status1 >= 1:
                                conn.commit()
                                self.batch_counter_status1 = 0 

                    linhas = cursor.rowcount

                    if linhas > 0:
                        return { 
                        "status": "sucesso",
                        "msg": "dados atualizado com sucesso "
                        }
                    else:
                        return { 
                             "status": "falha",
                             "msg": f"erro ao porcessar dados {traceback.format_exc()}",
                             "cndid" : cntid
                        }
        
              
                     

    except Exception as e:
        ClassLogger.logging.warning(traceback.format_exc())
        ClassLogger.logging.error(f"Erro ao atualizar status UPDATE cntobito - {str(e)}")
        return {  "status": "error","msg": traceback.format_exc(), "cntid": cntid }


def exists_by_name(self, person, falecimento):
            print(person)
            print(falecimento)

            if falecimento is None or str(falecimento).strip() in ['', 'NaN', '0000-00-00', '0000-00-00 00:00:00']:
                return { "status": "data_falecimento",
                                    "COLUNA_ERROR": ",".join(str(valor) for valor in [person, falecimento] if valor is not None),
                                    "dados_error": {
                                    "person": person,
                                    "falecimento": falecimento,
                                    }
                }

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
                with self.pool_raspagem.get_connection() as conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute(query, (person, data_falecimento_formatad))
                            resultado = cursor.fetchone()['exists']
                            print(f"qual e o resultado {resultado}")
                            return resultado
            except Exception as e: 
                erro_detalhado = traceback.format_exc()
                erro_msg = f"Falha em capturar os dados no obito_captura.obito_dados {str(e)}"
                ClassLogger.logging.error(erro_msg)
                # enviar_email_all(f"<h2>Erro processamento </h2><p>{erro_detalhado}</p>")
                
                return {
                    "status": "erro_conexao",
                    "error": erro_detalhado,
                    "COLUNA_ERROR": ",".join(str(valor) for valor in [person, falecimento] if valor is not None),
                    "dados_error": {
                        "person": person,
                        "falecimento": falecimento,
                    }
                }
                
def get_list_cpf(self) -> List[Dict]: 
     
     
      query = """SELECT cpf, link_fonte ,TO_CHAR(data_falecimento , 'YYYY-MM-DD') as ano FROM obito_captura.obito_dados where cpf is not null order by obito_id desc"""
      
      try:
                    
            with self.pool_raspagem.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                      cursor.execute(query,)
                      list_cpf = cursor.fetchall()
                
                      if not list_cpf:
                        return None
                return [dict(registro) for registro in list_cpf]
                                    
      except Exception as e:
                    ClassLogger.logger.error(f"Falha em caputrar os dados o erro get_lista_name_base_interpol - {str(e)}")
                
def get_list_cpf_cntid(self,cpf, link,ano) -> List[Dict]: 
      
      dados_achadados = []
      query = """SELECT cntid FROM  cnt, cntfis WHERE cntid = cntfiscnt AND cntcpfcgc = %s"""
      # LEMBRAR QUE PRECISA VIRA UMA TUPLA PARA A BUSCA POR CONTA DO PGADMIN 

      try:
                    
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query,(cpf,))
                    list_cpf_cntid = cursor.fetchall()
                     
                    if list_cpf_cntid:
                        for registro in list_cpf_cntid:
                            dados_achadados.append({
                                "status": "localizado",
                                "cntId": registro["cntid"],
                                "cpf": cpf,
                                "link": link,
                                "ano": ano,
                            })
                    else:
                        dados_achadados.append({
                            "status": "n_localizado",
                            "cntId": None,
                            "cpf": cpf,
                            "link": link,
                            "ano": ano,
                            "dados": [{"cpf": cpf, "cntid": None}],
                        })
                    return [dict(registro) for registro in dados_achadados]            


                                    
      except Exception as e:
            erro_detalhado = traceback.format_exc()
            ClassLogger.logging.error(f"Erro ao localizar CPF: {cpf} :: {str(erro_detalhado)}")
            ClassLogger.logging.error(f"Falha em caputrar os dados o erro SELECT cntid FROM  cnt, cntfis WHERE cntid - {str(e)}")


def get_list_cntobito(self,cpf,cntid,link,ano) -> List[Dict]: 
     
    
      query = """SELECT cntobitocnt , cntobitoflag ,cntobitofcm , cntobitoano FROM cntobito WHERE cntobitocnt = %s"""
      try:
                    
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query,(cntid,))
                    list_cnt_obito = cursor.fetchall()

                    print(f"tenho resultado aqui? {list_cnt_obito}")
                
                    if list_cnt_obito:
                        return {
                                "status": "localizado",
                                "cpf": cpf,
                                "cntid": cntid,
                                "fontes":link,
                                "ano": ano,
                                "registros" : list_cnt_obito,
                                "dados": [{"cpf": cpf, "cntid": cntid}]
                        }
                    else:
                         return {
                              "status": "n_localizado",
                               "cpf": cpf, 
                               "cntid": cntid,
                               "fontes": link,
                               "ano": ano,
                              "dados": [{"cpf": cpf, "cntid": cntid}]
                             
                        }                    
      except Exception as e:
            erro_detalhado = traceback.format_exc()
            ClassLogger.logging.error(f"Erro ao localizar CPF: {cpf} :: {str(erro_detalhado)}")
            ClassLogger.logging.error(f"Falha em caputrar os dados o erro SELECT cntid FROM  cnt, cntfis WHERE cntid - {str(e)}")
                 
#PROCESSO INVERSO PEGANDO OS IDS 
def list_obitos_with(self) -> List[Dict]:
      
      query = """WITH cnt_obito AS (
				    SELECT cn.cntid, cn.cntcpfcgc 
				    FROM cnt AS cn
				    INNER JOIN cntfis AS fis ON cn.cntid = fis.cntfiscnt 
				    WHERE cn.cntcpfcgc IN (SELECT DISTINCT cpf FROM obito_captura.obito_dados)
				)
				SELECT 
				    od.cpf,
				    co.cntid
				FROM obito_captura.obito_dados AS od
				INNER JOIN cnt_obito AS co ON od.cpf = co.cntcpfcgc;"""
      
      
      try:
                    
            with self.pool_raspagem.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query,)
                    registros = cursor.fetchall()
                
                    if not registros:
                        return None
                    if registros:
                        total_resultado = len(registros)
                        if total_resultado > 1:
                            return {
                            "status": "localizado", 
                            "dados": registros, 
                            "id_obito": obito_id,
                            "registro": registro
                        }
                        else:
                            return {
                            "status": "sucesso",
                            "CPF": resultado[0]['cpf'],
                                                                "id_obito": obito_id,
                                                                "registro": registro,
                                                                "cntid":  resultado[0]['cntid']
                        }
                    else:
                        return {
                             "status": "n_encontrado",
                               "id_obito": obito_id,
                                "registro": registro
                     }
                ClassLogger.logger.error(f"MINHA QUANTIDADE {len(registros)} ")
                return [dict(registro) for registro in registros]
                                    
      except Exception as e:
             ClassLogger.logging.error(f"Falha em caputrar os dados o erro list_interpol - {str(e)}")
        


def search_from_name_obito(self, nome_busca, data_nascimento,obito_id,registro):
        print(f"[INICIO] in nan {nome_busca} | obito_id={registro['obito_id']} | data-{data_nascimento}", flush=True)
        query = """SELECT cntid, documento as cpf, trim(to_char(nascimento, 'YYYY')) as ano_nascimentos
        FROM vw_data_nascimento
        WHERE UPPER(nome) = %s 
        AND length(documento) = %s """
        # query = """SELECT cntcpfcgc AS cpf, cntid , trim(to_char(cntfisncm, 'YYYY')) as ano_nascimentos
        #            FROM cnt, cntfis
        #            WHERE cntid = cntfiscnt
        #              AND UPPER(cntnom) = %s
        #              AND length(cntcpfcgc) = %s"""
        params = [nome_busca.strip().upper(), auxliares.CPF_LEN]
        if data_nascimento:
            # query += " AND cntfisncm = %s"
            query += " AND nascimento = %s"
            params.append(data_nascimento.strip())
        query += " LIMIT 2"


        try:
            #PROCURO EM PRODUDCAO
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, tuple(params))
                    resultado = cursor.fetchall()
                    # print(f"TOTAL A SER PROCESSADO {len(resultado)} registros para {nome_busca}")
                    print(f"LISTA COM OS ENCONTRADOS: {(resultado)}")

                    if resultado:
                        total_resultado = len(resultado)
                        if total_resultado > 1:
                            return {
                                  "status": "homonimo", 
                                  "dados": resultado, 
                                  "id_obito": obito_id,
                                  "registro": registro,
                                   "ano_nascimentos": resultado[0]['ano_nascimentos']
                                }
                        else:
                            return {
                                      "status": "sucesso",
                                      "CPF": resultado[0]['cpf'],
                                      "id_obito": obito_id,
                                      "registro": registro,
                                      "cntid":  resultado[0]['cntid'],
                                      "ano_nascimentos": resultado[0]['ano_nascimentos']
                            }
                    else:
                        return {
                                "status": "n_encontrado",
                                "id_obito": obito_id,
                                "registro": registro
                                
                            }
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                ClassLogger.logging.error(f"Falha em consultar os dados? - {str(erro_detalhado)}")
                return {
                "status": "erro_conexao",
                "error": str(e),
                "id_obito": obito_id,
               
            }
def search_from_cpf_ano_nacimento(self, nome_busca, ano ,obito_id,registro):
        query = """SELECT documento AS cpf, 
        cntid , trim(to_char(a.nascimento , 'YYYY')) as ano_nascimentos
                   FROM 
	               vw_data_nascimento AS a
                   WHERE  
                     UPPER(a.nome) = %s
                     AND length(a.documento) = %s"""
        # query = """SELECT cntcpfcgc AS cpf, cntid , trim(to_char(cntfisncm, 'YYYY')) as ano_nascimentos
        #            FROM cnt, cntfis
        #            WHERE cntid = cntfiscnt
        #              AND UPPER(cntnom) = %s
        #              AND length(cntcpfcgc) = %s"""
        params = [nome_busca.strip().upper(), auxliares.CPF_LEN]
        if ano:
            query += " AND trim(to_char(a.nascimento, 'YYYY')) = %s"
            params.append(ano.strip())
        query += " LIMIT 2"
        try:
            #PROCURO EM PRODUDCAO
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, tuple(params))
                    resultado = cursor.fetchall()
                    # print(f"TOTAL A SER PROCESSADO {len(resultado)} registros para {nome_busca}")
                    # print(f"LISTA COM OS ENCONTRADOS: {(resultado)}")

                    if resultado:
                        total_resultado = len(resultado)
                        if total_resultado > 1:
                            return {
                                  "status": "homonimo", 
                                  "dados": resultado, 
                                  "id_obito": obito_id,
                                  "registro": registro,
                                   "ano_nascimentos": resultado[0]['ano_nascimentos']
                                }
                        else:
                            return {
                                      "status": "sucesso",
                                      "CPF": resultado[0]['cpf'],
                                      "id_obito": obito_id,
                                      "registro": registro,
                                      "cntid":  resultado[0]['cntid'],
                                      "ano_nascimentos": resultado[0]['ano_nascimentos']
                            }
                    else:
                        return {
                                "status": "n_encontrado",
                                "id_obito": obito_id,
                                "registro": registro
                                
                            }
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                ClassLogger.logging.error(f"Falha em consultar os dados? - {str(erro_detalhado)}")
                return {
                "status": "erro_conexao",
                "error": str(e),
                "id_obito": obito_id,
               
            }

def search_from_name_cidade(self, nome_busca, cidade,estado,obito_id,registro):
        query = """SELECT cntid,cntcpfcgc AS cpf
                   FROM cnt
        JOIN cntfisend
            ON cntid = cntfisendcnt
        WHERE
            UPPER(cntnom) LIKE %s
            AND length(cntcpfcgc) = %s
            AND UPPER(cntfisendcid) = %s"""
        params = [nome_busca.strip().upper(), auxliares.CPF_LEN,cidade]
        if estado:
            query += " AND cntfisendest = %s"
            params.append(estado.strip())
        query += " LIMIT 2"
        try:
            #PROCURO EM PRODUDCAO
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, tuple(params))
                    resultado = cursor.fetchall()
                    # print(f"TOTAL A SER PROCESSADO {len(resultado)} registros para {nome_busca}")
                    # print(f"LISTA COM OS ENCONTRADOS POR CIDADE......: {(resultado)}")

                    if resultado:
                        total_resultado = len(resultado)
                        if total_resultado > 1:
                            return {
                                  "status": "homonimo", 
                                  "CPF": resultado[0]['cpf'],
                                  "dados": resultado, 
                                  "id_obito": obito_id,
                                  "registro": registro,
                                #    "ano_nascimentos": resultado[0]['ano_nascimentos']
                                }
                        else:
                            return {
                                      "status": "sucesso",
                                      "CPF": resultado[0]['cpf'],
                                      "id_obito": obito_id,
                                      "registro": registro,
                                      "cntid":  resultado[0]['cntid'],
                                    #   "ano_nascimentos": resultado[0]['ano_nascimentos']
                            }
                    else:
                        return {
                                "status": "n_encontrado",
                                "id_obito": obito_id,
                                "registro": registro
                                
                            }
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                ClassLogger.logging.error(f"Falha em consultar os dados? - {str(erro_detalhado)}")
                return {
                "status": "erro_conexao",
                "error": str(e),
                "id_obito": obito_id,
               
            }
        
def search_from_name_obito_nome(self, nome_busca, data_nascimento,obito_id,registro):
        query = """SELECT cntcpfcgc AS cpf, cntid, trim(to_char(cntfisncm, 'YYYY')) as ano_nascimentos
                   FROM cnt, cntfis
                   WHERE cntid = cntfiscnt
                     AND UPPER(cntnom) = %s
                     AND length(cntcpfcgc) = %s"""
        params = [nome_busca.strip().upper(), auxliares.CPF_LEN]
        if data_nascimento:
            query += " AND cntfisncm = %s"
            params.append(data_nascimento.strip())
        query += " LIMIT 2"
        try:
            #PROCURO EM PRODUDCAO
            with self.pool_producao.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, tuple(params))
                    resultado = cursor.fetchall()
                    # print(f"TOTAL A SER PROCESSADO {len(resultado)} registros para {nome_busca}")
                    # print(f"LISTA COM OS ENCONTRADOS: {(resultado)}")

                    if resultado:
                        total_resultado = len(resultado)
                        if total_resultado > 1:
                            return {
                                  "status": "homonimo", 
                                  "dados": resultado, 
                                  "id_obito": obito_id,
                                  "registro": registro
                                }
                        else:
                            return {
                                      "status": "sucesso",
                                      "CPF": resultado[0]['cpf'],
                                      "id_obito": obito_id,
                                      "registro": registro,
                                      "cntid":  resultado[0]['cntid']
                            }
                    else:
                        return {
                                "status": "n_encontrado",
                                "id_obito": obito_id,
                                "registro": registro
                            }
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                ClassLogger.logging.error(f"Falha em consultar os dados? - {str(erro_detalhado)}")
                return {
                "status": "erro_conexao",
                "error": str(e),
                "id_obito": obito_id,
               
            }
        



def push_cpf_obito(self,cpf, idObito,registro_bloco,tipo):

    set_parts = []
    params = []

    if tipo == 1:
        set_parts.append("cpf = %s")
        set_parts.append("tipo_obito = %s")
        params.extend([cpf, tipo])
    else:
        set_parts.append("tipo_obito = %s")
        params.append(tipo)

    query = f"""UPDATE obito_captura.obito_dados
                 SET {', '.join(set_parts)}
                 WHERE obito_id = %s;"""
    params.append(idObito)

    try:
         with self.pool_raspagem.get_connection() as conn:
             with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(params))
                
                return {
                    "status": "sucesso",
                    "msg": "sucesso em atualizar",
                    "id_obito": idObito,
                    "registros_atualizados": registro_bloco.get('cntid') if registro_bloco.get('cntid') else registro_bloco.get('dados')
                }
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        ClassLogger.logging.error(f"Erro ao atualizar Baixa do id {idObito} :: {str(erro_detalhado)}")
        return {
             "status": "erro",
             "error": str(e),
             "id_obito"  : idObito
        }


def full_dados(self)-> List[Dict]:

        query = """SELECT trim(UPPER(nome)) as nome, trim(to_char(data_nascimento, 'YYYY-MM-DD')) as data_nascimento ,obito_id FROM obito_captura.obito_dados
                   where data_nascimento is not null and cpf is null and tipo_obito not in (1)"""
                #  where data_nascimento is not null and cpf is null ORDER BY RANDOM() ASC LIMIT 2 """

        try:
                        
                with self.pool_raspagem.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query)
                        registros = cursor.fetchall()
                    
                        if not registros:
                            return None
                    return [dict(registro) for registro in registros]
                                        
        except Exception as e:
                print(traceback.format_exc())
                error = traceback.format_exc()
                ClassLogger.logging.error(f"Lista com o processamento de busca dos dados error: {error}")
                 

def full_dados_homonimos(self)-> List[Dict]:

        query = """SELECT trim(UPPER(nome)) as nome, trim(to_char(data_nascimento, 'YYYY-MM-DD')) as data_nascimento , obito_id , cidade , data_falecimento , ano_nascimento_estimado FROM obito_captura.obito_dados where cpf is null"""
               

        try:
            with self.pool_raspagem.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query)
                        registros = cursor.fetchall()
                    
                        if not registros:
                            return None
                return [dict(registro) for registro in registros]
                                        
        except Exception as e:
                print(traceback.format_exc())
                error = traceback.format_exc()
                ClassLogger.logging.error(f"Falha o processsar lista homonimos : {error}")
                 


#funcao para sanatizar
def sanitize(value):
   
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

