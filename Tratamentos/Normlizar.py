import os
import re
import numpy as np
import pandas as pd

from pathlib import Path
from collections import Counter, defaultdict
from Logs import ClassLogger
from utils.auxliares import auxliares
from utils.unicode import remover
from datetime import time,datetime, timedelta
from services.crawler import iniciar
from Model.ClassModel import insert_base_obito,exists_by_name
from concurrent.futures import ThreadPoolExecutor, as_completed





def arquivos_process(self, chave_servidor):
    """Processa todos os IDs de servidor recebidos."""
    if chave_servidor is None:
        return []

    if isinstance(chave_servidor, (str, int)):
        chave_servidor = [chave_servidor]

    dados_enviados = []
    for chave in chave_servidor:
        if chave not in self.servidores:
            ClassLogger.logging.warning(
                f"Servidor não encontrado para a chave: {chave}"
            )
            continue

        resultado = _arquivos_process_servidor(self, chave)
        if resultado:
            dados_enviados.extend(resultado)

    return dados_enviados


def _arquivos_process_servidor(self, chave_servidor):

    contador = defaultdict(lambda: {
        "ACHADAS": 0,
        "NA": 0,
        "ERROR":0,
        "QTINSERT": 0
        })
    
    ClassLogger.logging.info("ACESSANDO PAGINA PARA PROCESSAR OS DADOS")
    ClassLogger.logging.info("REALIZAR A NORMALIZAR!!")

    registros = self.servidores.get(chave_servidor)

    if not registros:
        ClassLogger.logging.warning(
            f"Servidor não encontrado para a chave: {chave_servidor}"
        )
        return []

    print(registros)
    arquivos = f"arquivos/{registros['nome']}"
    # print(arquivos)

    # return

    try:
        dados = []
        arquivos_data = []
        # df_filtrado = {}

        caminho_arquivos = Path(arquivos)
        nome = registros["nome"]

        for arquivo in caminho_arquivos.glob("*.csv"):

            print(f"Analisando: {arquivo.name}")

            
            if arquivo.name == "estatisticas.csv":
                     continue

            if not arquivo.name.startswith(f"{nome}_"):
                    continue

            try:
                data_str = arquivo.stem.replace(
                    f"{nome}_",
                    "",
                    1
                )

                data = datetime.strptime(
                    data_str,
                    "%d-%m-%Y"
                ).date()

                arquivos_data.append(
                    (data, arquivo)
                )

                print(f"MEUS DADOS LOCALIZADO {arquivos_data}")

            except ValueError:

           
                continue


            
            if not arquivos_data:

                print(
                    f"Nenhum arquivo com data encontrado para {nome}"
                )

            else:

                # Mais recente primeiro
                arquivos_data.sort(
                    key=lambda x: x[0],
                    reverse=True
                )

                arquivo_atual = arquivos_data[0][1]

                print(
                    f"Arquivo mais recente: "
                    f"{arquivo_atual.name}"
                )

                if len(arquivos_data) > 1:

                    arquivo_anterior = arquivos_data[1][1]

                    print(
                        f"Arquivo anterior: "
                        f"{arquivo_anterior.name}"
                    )

                else:

                    arquivo_anterior = None

                    print(
                        "Não existe arquivo anterior."
                    )

                    print(f"{arquivos_data}")
                    print(f"{arquivo_anterior}")


                arquivo_antigo = buscar_arquivo_antigo(
                    arquivos,
                    nome
                    )

                print(f"Arquivo antigo encontrado: {arquivo_antigo}")

            # print(f"MEUS DADOS LOCALIZADOS {qta_arquivo}")
               

            if arquivo == 'old' or arquivo == 'estatisticas.csv' or  arquivo == 'error':
                continue


            caminho_atual = arquivos

            print(f"Processando CAMINHO: {caminho_atual}")

            df = pegar_registros_novos(
                arquivo_atual,
                arquivo_antigo
            )

            if df.empty:
                print("Nenhum registro novo para processar.")
                continue

            print(
                f"Vou processar {len(df)} registros novos."
            )

                
            # print(f"Processando : {arquivo}")
            
            # Lê o CSV atual
            # df = pd.read_csv(f"{arquivos}/{arquivo}", sep=";")

            
            contador[arquivo]["ACHADAS"] += 1              
            contador[arquivo]["QTINSERT"] += len(df)       
          

    
            df.columns = df.columns.str.strip().str.rstrip(':').str.strip().str.replace(' ', '_')

            df.rename(columns={'FALECIMENTO':  auxliares.TEXTO_FALECIMENTO ,'DATA_NACIMENTO': 'DATA_NASCIMENTO'}, inplace=True)
            # df.rename(columns={'FALECIMENTO':  auxliares.TEXTO_FALECIMENTO ,'DATA_NACIMENTO': 'DATA_NASCIMENTO','FILIACAO_A': 'FAMILIARES_A','FILIACAO_B': 'FAMILIARES_B'}, inplace=True)

            print(df.columns)
            # df = df.drop_duplicates(subset=['NOME'])
            df = df.drop_duplicates(subset=['NOME', 'DATA_FALECIMENTO'])
            # print(df)

            if 'NOME' in df.columns:
                df = df[~df['NOME'].astype(str).str.strip().isin(['CANCELADO/TESTE', '.','TESTE', '********','CANCELADO'])].copy()

            
            if 'NOME' in df.columns:

                df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].apply(verificar_data)


                if 'IDADE' in df.columns:
                   
                    df['IDADE'] = df['IDADE'].apply(lambda x: re.findall(r'\d+', str(x))[0] if re.findall(r'\d+', str(x)) else 0)
                  
                    if 'DATA_NASCIMENTO' in df.columns:
                        mascara =( 
                            (df['IDADE'] == 0) & 
                            df['DATA_NASCIMENTO'].notna() &
                            df['DATA_FALECIMENTO'].notna()
                        )
                        
                        df.loc[mascara, 'IDADE'] = (
                        df.loc[mascara]
                        .apply(
                            lambda row: achar_idade(row['DATA_NASCIMENTO'],
                                                        row['DATA_FALECIMENTO']),axis=1))
                        df['IDADE'] = df['IDADE'] 
                else:
                    if 'DATA_NASCIMENTO' in df.columns:
                         df['IDADE'] = df.apply(lambda row: achar_idade(row['DATA_NASCIMENTO'], row['DATA_FALECIMENTO']), axis=1)
                    else:
                        df['IDADE'] = auxliares.A_IDADE # TROCADO DE 0 PARA NONE

                #INICIA COMO SEM INFORMACAO
                df['FAMILIARES_A'] =  auxliares.TEXTO_FAMILIARES
                df['FAMILIARES_B'] =  auxliares.TEXTO_FAMILIARES
                df['FAMILIARES'] =  auxliares.TEXTO_FAMILIARES
                # df['CONJUGE'] = auxliares.TEXTO_P


                if 'FAMILIARES' in df.columns:
                    df['FAMILIARES_A'] =  df['FAMILIARES'].apply(tratar_familiares_A).str.upper()
                    df['FAMILIARES_B'] =  df['FAMILIARES'].apply(tratar_familiares_B).str.upper()
                # else:
                    # Se não tem a coluna unificada 'FAMILIARES', verifica as colunas individuais
                if 'PAIS' in df.columns:
                    df['FAMILIARES_A'] = df['PAIS'].apply(tratar_familiares_array).str.upper()
                if 'FILHOS' in df.columns:
                    df['FAMILIARES_B'] = df['FILHOS'].apply(tratar_familiares_array).str.upper()
                if 'CONJUGE' in df.columns:
                    df['FAMILIARES_A'] = df['CONJUGE'].str.upper()
                else:
                    df['CONJUGE'] = auxliares.TEXTO_P
                if 'FILIACAO_A' in df.columns:
                    df['FAMILIARES_A'] =  df['FILIACAO_A'].apply(remover).str.upper()
                    df['FAMILIARES_B'] =  df['FILIACAO_B'].apply(remover).str.upper()
                    # else:
                    #     df['CONJUGE'] = auxliares.TEXTO_P

            
                
                # Aplica as funções nas colunas
                # df['CONJUGE'] = auxliares.TEXTO_P
                df['ANO_NASCIMENTO_ESTIMADO'] = df['IDADE'].apply(calcula_ano)
                if 'DATA_NASCIMENTO' in df.columns:
                    df['ANO_NASCIMENTO_INFORMADO'] = df['DATA_NASCIMENTO'].apply(formatar_data)
                else:
                    df['ANO_NASCIMENTO_INFORMADO'] = auxliares.A_NASCIMENTO

                if 'DATA_FALECIMENTO' in df.columns:
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].astype(str).str.strip("()', ")
                    if 'DATA_SEPULTAMENTO' in df.columns:
                        df['DATA_FALECIMENTO'] = df['DATA_SEPULTAMENTO'].apply(formatar_data_ontem)
                    
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].apply(formatar_data)
                else:
                    print('SAIO NO NESTE IF?')
                   
                    df['DATA_FALECIMENTO'] = auxliares.FALECIMENTO # CASO NÃO TENHA DATA
                print(f"DATA LOCALIZADA {df['DATA_FALECIMENTO']}")
                # if df['']
                df['NOME'] = df['NOME'].apply(remover).str.upper()
                if 'DATA_CAPTURA' in df.columns:
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].astype(str).str.strip("()', ")
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].apply(formatar_data_hora)
                else:
                    df['DATA_CAPTURA'] = formatar_data(datetime.now().strftime("%d/%m/%Y %H:%M")) # CASO NÃO TENHA DATA
                if 'LINK' in df.columns:
                    df['LINK'] = df['LINK']
                else:
                    df['LINK'] = registros['nome'] # PEGA O NOME QUANDO NÃO TIVER O LINK

                if 'CIDADE' in df.columns:
                    df['CIDADE'] = df['CIDADE'].str.upper()
                else:
                    df['CIDADE'] = auxliares.TEXTO_P

                 # Filtra apenas as colunas desejadas para o resultado final
                df_filtrado = df[['NOME', 'IDADE','DATA_FALECIMENTO','ANO_NASCIMENTO_ESTIMADO', 'LINK','DATA_CAPTURA','ANO_NASCIMENTO_INFORMADO','CIDADE','FAMILIARES_A','FAMILIARES_B','FAMILIARES']].rename(columns={'LINK': 'LINK_FONTE'})
                # df_filtrado = df[['NOME', 'IDADE','DATA_FALECIMENTO','ANO_NASCIMENTO_ESTIMADO', 'LINK','DATA_CAPTURA','ANO_NASCIMENTO_INFORMADO','CIDADE','FAMILIARES_A','FAMILIARES_B','CONJUGE','FAMILIARES']].rename(columns={'LINK': 'LINK_FONTE'})
                dados_enviado = df_filtrado.reset_index(drop=True)
             
                dados.append(dados_enviado)

          
            df_final = pd.concat(dados, ignore_index=True)
            # print(df_final)
            contador[arquivo]["QTINSERT"] = len(df_final)
            dados_para_enviar = df_final.to_dict(orient="records")
            # print(df_final.to_string(index=False))

            print("COLUNA FINAL{}")

            print(dados_para_enviar)
            if 'dados_para_enviar' in locals():
                return dados_para_enviar
            else:
                return []
                    
        # return dados_para_enviar

    except Exception as e:
         ClassLogger.logging.error(f"Erro fatal na execução para normalizar: {e}", exc_info=True)       


def calcula_ano(idade_enviada):

        print(idade_enviada)
        if idade_enviada is None:
            return auxliares.IDADE

        if isinstance(idade_enviada, float) and pd.isna(idade_enviada):
            return auxliares.IDADE

        if isinstance(idade_enviada, (np.floating, np.integer)) and pd.isna(idade_enviada):
            return auxliares.IDADE

        if str(idade_enviada).strip().lower() in ['nan', '', 'none', '0', '{}']:
            return auxliares.IDADE

        try:
            nasc_str = int(idade_enviada)
        except (TypeError, ValueError):
            return auxliares.IDADE

        if nasc_str in [0]:
            return auxliares.IDADE
        try:
            ano_atual = datetime.now().strftime("%Y")
            return  int(ano_atual) - int(nasc_str)
        except Exception as e:
            ClassLogger.logging.info(f"nasc_str estou saindo aqui  no {e}")
            return auxliares.IDADE

def formatar_data(data_envida):
    
    if isinstance(data_envida, float) or data_envida is None or str(data_envida).lower() == 'nan' or str(data_envida) == auxliares.DATA_PARAO or str(data_envida) == auxliares.DATA_ENVIADA:
        return auxliares.DATA_PARAO

    if isinstance(data_envida, float) and pd.isna(data_envida):
         return auxliares.IDADE

    if data_envida in ['nan', '', 'none', '0', '{}','0000/00/00','0000-00-00']:
        return auxliares.DATA_PARAO

    data_str = str(data_envida).strip()
    data_str_formmat = re.sub(r'-', '', data_str)
    try:
        data_objeto = datetime.strptime(data_str_formmat, "%d/%m/%Y %H:%M")

        # DOIS TRATAMENTO PARA QUANDO NÃO TIVER HORA NA DATA

    except ValueError:
        try:
            
            data_objeto = datetime.strptime(data_str_formmat, "%d/%m/%Y")
            return data_objeto.strftime("%Y/%m/%d")
        
        except ValueError:
            try:
               
                data_objeto = datetime.strptime(data_str_formmat, "%d%m/%Y")
                return data_objeto.strftime("%Y/%m/%d")
            
            except ValueError as e:
                print(f"MEU ERRO: Formato desconhecido para a string '{data_str_formmat}' -> {e}")
                return auxliares.DATA_PARAO

    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data com o nan: {e}", exc_info=True)
        return auxliares.DATA_PARAO
def formatar_data_hora(data_envida):
    print(f"ESTOU SAINDO NO FORMATAR DATA  COM HORA ENVIADA :: {data_envida}")
    
    # 1. Verifica se é NaN do Pandas/Float ou se está na lista de inválidos
    if pd.isna(data_envida) or str(data_envida).lower().strip() in ['nan', '', 'none', '0', '{}', '0000/00/00', '0000-00-00']:
        return auxliares.DATA_PARAO
        
    # 2. Garante que o dado virou string antes do regex
    data_str = str(data_envida).strip()
    data_str_formmat = re.sub(r'-', '', data_str)
    
    try:
        data_objeto = datetime.strptime(data_str_formmat, "%d/%m/%Y %H:%M")
        data_formatada = data_objeto.strftime("%Y/%m/%d")
        return data_formatada
    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data: {e}", exc_info=True)
        return auxliares.DATA_PARA

    
def achar_idade(nasc, falec):

    try:
        if pd.isna(nasc) or pd.isna(falec):
            return None

        nasc_str = str(nasc).strip()
        falec_str = str(falec).strip()

        if nasc_str.lower() in ['nan', '', 'none', '0', '{}']:
            return None

        if falec_str.lower() in ['nan', '', 'none', '0', '{}']:
            return None

        data_nascimento = datetime.strptime(
            nasc_str,
            "%d/%m/%Y"
        )

        data_falecimento = datetime.strptime(
            falec_str,
            "%d/%m/%Y"
        )

        idade = (
            data_falecimento.year
            - data_nascimento.year
            - (
                (data_falecimento.month, data_falecimento.day)
                <
                (data_nascimento.month, data_nascimento.day)
            )
        )

        if idade < 0:
            return None

        return int(idade)

    except Exception as e:

        ClassLogger.logging.warning(
            f"Falha em achar os dados: {e}",
            exc_info=True
        )

        return None


def tratar_familiares_A(textos):
    
    dados_extraidos = []
    if textos is None or (isinstance(textos, float) and pd.isna(textos)):
        textos = ""
    elif not isinstance(textos, str):
        textos = str(textos)

    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.|Casado\.|casado\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)


    return ", ".join(conjuges_pais) if conjuges_pais else auxliares.TEXTO_P 


def tratar_familiares_B(textos):
    
    dados_extraidos = []
    if textos is None or (isinstance(textos, float) and pd.isna(textos)):
        textos = ""
    elif not isinstance(textos, str):
        textos = str(textos)

    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    # conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)
    # filhos_match = re.search(r'deixa (?:os filhos|as filhas|filhos)\s+(.*?)(?=\s*,\s*(?:os filhos)\s+(.*?))(?=\s*,\s*(?:familiares|amigos|conhecidos|parentes)\b|\s*$)', 
    # texto_limpo, 
    # flags=re.IGNORECASE) 

    filhos_match = re.search(
    r'deixa\s+(?:os\s+filhos|as\s+filhas|o\s+filho|filhos?)\s+(.*?)(?=\s*,\s*(?:familiares|amigos|conhecidos|parentes|neto|bisneto|deixando)\b|\s*$)',
    texto_limpo,
    flags=re.IGNORECASE)

    lista_filhos = []
    if filhos_match:
        trecho_filhos = filhos_match.group(1).strip()

        trecho_filhos = re.sub(
            r'\s*(?:\(\s*(?:In\s+Memoriam|neto|bisneto)\s*(?:[/*]\s*(?:neto|bisneto)\s*)*\)|\*\s*(?:neto|bisneto)\s*\*?)',
            '',
            trecho_filhos,
            flags=re.IGNORECASE
        )

        lista_filhos = [f.strip() for f in re.split(r',|\s+e\s+', trecho_filhos) if f.strip()]
    return ", ".join(lista_filhos) if lista_filhos else auxliares.TEXTO_P 

def tratar_familiares_A_old(textos):
    
    dados_extraidos = []
    conjue_pais = []
    if textos is None or (isinstance(textos, float) and pd.isna(textos)):
        textos = ""
    elif not isinstance(textos, str):
        textos = str(textos)

    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)
    filhos_match = re.search(r'deixa (?:os filhos|as filhas|filhos)\s+([^,]+?)(?=\s*,\s*familiares|\s*$)', texto_limpo)

    lista_filhos = []
    if filhos_match:
        trecho_filhos = filhos_match.group(1).strip()
         
        lista_filhos = [f.strip() for f in re.split(r',|\s+e\s+', trecho_filhos) if f.strip()]


    dados_extraidos.append({
            'CONJUGE||PAIS': ", ".join(conjuges_pais) if conjuges_pais else auxliares.TEXTO_P,
            'Filhos': ", ".join(lista_filhos) if lista_filhos else auxliares.TEXTO_P
    })

    for pessoa in dados_extraidos:
        print(pessoa['CONJUGE||PAIS'])


    # print(dados_extraidos['CONJUGE||PAIS'])

    info_conjuge = ", ".join(conjuges_pais) if conjuges_pais else auxliares.TEXTO_P
    
    if not info_conjuge or info_conjuge == auxliares.TEXTO_P:
        # print(f"estou saindo aqui {info_conjuge}")
        tipo_info = auxliares.TEXTO_P
    else:
        tipo_info = auxliares.TEXTO_CONJU


    return info_conjuge , tipo_info


def tratar_familiares_B_old(textos):
    
    dados_extraidos = []
    if textos is None or (isinstance(textos, float) and pd.isna(textos)):
        textos = ""
    elif not isinstance(textos, str):
        textos = str(textos)

    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    # conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)
    filhos_match = re.search(r'deixa (?:os filhos|as filhas|filhos)\s+([^,]+?)(?=\s*,\s*familiares|\s*$)', texto_limpo)
        
    lista_filhos = []
    if filhos_match:
        trecho_filhos = filhos_match.group(1).strip()
         
        lista_filhos = [f.strip() for f in re.split(r',|\s+e\s+', trecho_filhos) if f.strip()]


    info_ = ", ".join(lista_filhos) if lista_filhos else auxliares.TEXTO_P

    if not info_ or info_ == auxliares.TEXTO_P:
       
        tipo_info = auxliares.TEXTO_P
    else:
        tipo_info = auxliares.TEXTO_FILHO

   
    return info_ , tipo_info
    # return ", ".join(lista_filhos) if lista_filhos else auxliares.TEXTO_P 

def tratar_familiares_array(lista):
    print(f"LISTA ENVIADO ?{lista}")
    texto_limpo = re.sub(r'[\[\]]', '', lista).strip()
    texto_anos = re.sub(r'\s*\(\d+\s+anos\)', '', texto_limpo).strip()
    if not texto_anos:
        return auxliares.TEXTO_FAMILIARES

    texto_limpo_regex = re.sub(r'\..*', ".'", texto_anos)
    texto_limpo_regex = texto_limpo_regex.replace("'", "")
    # texto_limpo = texto_limpo.split('.')[0] + ".'"
    return remover(texto_limpo_regex)

    
    
    


def verificar_data(data):
  
    if isinstance(data, float) or data is None or str(data).lower() == 'nan' or str(data).strip() in ('', auxliares.DATA_PARAO) or str(data).strip() == auxliares.DATA_C:
        return auxliares.DATA_PARAO
    data_str = str(data).strip()

    if ',' in data_str:
        ClassLogger.logging.error(f"Múltiplas datas detectadas, rejeitando: {data_str}")
        return auxliares.DATA_PARAO
        
    # 3. Tratamento se já for a string zerada
    if data_str in (auxliares.DATA_PARAO, ''):
        return auxliares.DATA_PARAO

    try:
        formato = "%d/%m/%Y"
        data_convertida = datetime.strptime(data, formato)
        # print(f"Data válida! {data_convertida}")
        return data

    except ValueError as e:

        if '/-' in str(data):
            return auxliares.DATA_PARAO # AJUSTA ESTE RETORNO PRA TRAZER O RESULTADO CORRETO


    except Exception as e:
        print(f"Data inválida ou formato incorreto {data}")
        print("Data inválida ou formato incorreto.")
        ClassLogger.logging.info(f"Data inválida ou formato incorreto {e} {data}", exc_info=True)
        return auxliares.DATA_PARAO



def buscar_arquivo_antigo(arquivos,nome):
    pasta_old = Path(arquivos) / "old"

    if not pasta_old.exists():
        print("Pasta OLD não existe")
        return None

    arquivos_encontrados = []

    for arquivo in pasta_old.glob("*.csv"):

        print(f"Analisando arquivo: {arquivo.name}")
        
        if not arquivo.name.startswith(f"{nome}_"):
            continue

        try:

            data_str = arquivo.stem.replace(
                f"{nome}_",
                "",
                1
            )

            data = datetime.strptime(
                data_str,
                "%d-%m-%Y"
            ).date()

            arquivos_encontrados.append(
                (data, arquivo)
            )

        except ValueError:
            continue

    if not arquivos_encontrados:

        print("Nenhum arquivo com data encontrado.")
        return None

    # Ordena da data mais recente para a mais antiga
    arquivos_encontrados.sort(
        key=lambda x: x[0],
        reverse=True
    )

    arquivo_mais_recente = arquivos_encontrados[0][1]

    print(
        f"Arquivo mais recente: "
        f"{arquivo_mais_recente.name}"
    )

    return arquivo_mais_recente



def pegar_registros_novos(arquivo_atual, arquivo_antigo):

    df_atual = pd.read_csv(
        arquivo_atual,
        sep=";"
    )

    df_atual = df_atual.drop_duplicates()

    # Não existe arquivo anterior
    if arquivo_antigo is None:

        print("Não existe arquivo anterior.")
        print(f"Serão processados {len(df_atual)} registros.")

        return df_atual

    df_antigo = pd.read_csv(
        arquivo_antigo,
        sep=";"
    )

    print(f"Arquivo atual: {len(df_atual)} registros")
    print(f"Arquivo antigo: {len(df_antigo)} registros")

    # Se não aumentou
    if len(df_atual) <= len(df_antigo):

        print("Não houve crescimento.")

        return pd.DataFrame()
    df_atual.columns = df_atual.columns.str.strip().str.rstrip(':').str.strip().str.replace(' ', '_')
    df_antigo.columns = df_antigo.columns.str.strip().str.rstrip(':').str.strip().str.replace(' ', '_')
    df_atual.rename(columns={'FALECIMENTO': auxliares.TEXTO_FALECIMENTO, 'DATA_NASCIMENTO': 'DATA_NASCIMENTO'}, inplace=True)  
    df_antigo.rename(columns={'FALECIMENTO': auxliares.TEXTO_FALECIMENTO, 'DATA_NASCIMENTO': 'DATA_NASCIMENTO'}, inplace=True)  

    novos = df_atual[
    ~df_atual.set_index(["NOME", "DATA_FALECIMENTO"]).index.isin(
        df_antigo.set_index(["NOME", "DATA_FALECIMENTO"]).index
    )].copy()

    print(
        f"Novos registros encontrados: {len(novos)}"
    )

    return novos


def formatar_data_ontem(data_sepultamento):
    data_objeto = datetime.strptime(data_sepultamento, "%d/%m/%Y")
    data_anterior = data_objeto - timedelta(days=1)
    return data_anterior.strftime("%d/%m/%Y")
