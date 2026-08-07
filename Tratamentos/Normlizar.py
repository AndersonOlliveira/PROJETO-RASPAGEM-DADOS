import os
import re
import numpy as np
import pandas as pd

from pathlib import Path
from Logs import ClassLogger
from utils.auxliares import auxliares
from utils.unicode import remover
from datetime import time,datetime
from services.crawler import iniciar





def arquivos_process(self):
    ClassLogger.logging.info("ACESSANDO PAGINA PARA PROCESSAR OS DADOS")
    ClassLogger.logging.info("REALIZAR A NORMALIZAR!!")


    # print(obter_servidores(self,[1, 7, 12]))

    # return
    # 
    registros = self.servidores.get(3)

    print(registros)
    arquivos = f"arquivos/{registros['nome']}"
    # print(arquivos)

    # return

    try:
        dados = []  # Lista para armazenar os DataFrames processados
        caminho = os.listdir(arquivos)
        for arquivo in caminho:
            print(arquivo)
            # Ignora arquivos temporários ou ocultos (como .DS_Store no Mac ou temporários do Windows)
            if arquivo.startswith('.'):
                continue

            if arquivo == 'old' or arquivo == 'estatisticas.csv':
                continue

            # if arquivo == registros['nome']:
                
            print(f"Processando: {arquivo}")
            
        #     # Lê o CSV atual
        # try:
            df = pd.read_csv(f"{arquivos}/{arquivo}", sep=";")
            # print(df)

        # except Exception as e:
        #     print(f"MEUS ERROS {e}")# Ajusta cabeçalho 
            df.columns = df.columns.str.strip().str.rstrip(':').str.strip().str.replace(' ', '_')

            df.rename(columns={'FALECIMENTO':  auxliares.TEXTO_FALECIMENTO ,'DATA_NACIMENTO': 'DATA_NASCIMENTO'}, inplace=True)
            # df.rename(columns={'FALECIMENTO':  auxliares.TEXTO_FALECIMENTO ,'DATA_NACIMENTO': 'DATA_NASCIMENTO','FILIACAO_A': 'FAMILIARES_A','FILIACAO_B': 'FAMILIARES_B'}, inplace=True)

            print(df.columns)

            
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
                        df['IDADE'] = 0

                #INICIA COMO SEM INFORMACAO
                df['FAMILIARES_A'] =  auxliares.TEXTO_FAMILIARES
                df['FAMILIARES_B'] =  auxliares.TEXTO_FAMILIARES

                if 'FAMILIARES' in df.columns:
                    df['FAMILIARES_A'] =  df['FAMILIARES'].apply(tratar_familiares_A).str.upper()
                    df['FAMILIARES_B'] =  df['FAMILIARES'].apply(tratar_familiares_B).str.upper()
                else:
                    # Se não tem a coluna unificada 'FAMILIARES', verifica as colunas individuais
                    if 'PAIS' in df.columns:
                        df['FAMILIARES_A'] = df['PAIS'].apply(tratar_familiares_array).str.upper()
                    if 'FILHOS' in df.columns:
                        df['FAMILIARES_B'] = df['FILHOS'].apply(tratar_familiares_array).str.upper()
                    if 'CONJUGE' in df.columns:
                        df['CONJUGE'] = df['CONJUGE'].str.upper()
                    else:
                        df['CONJUGE'] = auxliares.TEXTO_P
                    if 'FILIACAO_A' in df.columns:
                        df['FAMILIARES_A'] =  df['FILIACAO_A'].apply(remover).str.upper()
                        df['FAMILIARES_B'] =  df['FILIACAO_B'].apply(remover).str.upper()
                    else:
                        df['CONJUGE'] = auxliares.TEXTO_P

                    
            
                
                # Aplica as funções nas colunas
                df['ANO_NASCIMENTO_ESTIMADO'] = df['IDADE'].apply(calcula_ano)
                if 'DATA_NASCIMENTO' in df.columns:
                    df['ANO_NASCIMENTO_INFORMADO'] = df['DATA_NASCIMENTO'].apply(formatar_data)
                else:
                    df['ANO_NASCIMENTO_INFORMADO'] = auxliares.A_NASCIMENTO
                if 'DATA_FALECIMENTO' in df.columns:
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].astype(str).str.strip("()', ")
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].apply(formatar_data)
                else:
                    df['DATA_FALECIMENTO'] = auxliares.FALECIMENTO # CASO NÃO TENHA DATA

                df['NOME'] = df['NOME'].apply(remover).str.upper()
                if 'DATA_CAPTURA' in df.columns:
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].astype(str).str.strip("()', ")
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].apply(formatar_data_hora)
                else:
                    df['DATA_CAPTURA'] = auxliares.DATA_CAPTURA # CASO NÃO TENHA DATA
                if 'LINK' in df.columns:
                    df['LINK'] = df['LINK']
                else:
                    df['LINK'] = registros['nome'] # PEGA O NOME QUANDO NÃO TIVER O LINK

                if 'CIDADE' in df.columns:
                    df['CIDADE'] = df['CIDADE'].str.upper()
                else:
                    df['CIDADE'] = auxliares.TEXTO_P
                
                # Filtra apenas as colunas desejadas para o resultado final
                df_filtrado = df[['NOME', 'IDADE','DATA_FALECIMENTO','ANO_NASCIMENTO_ESTIMADO', 'LINK','DATA_CAPTURA','ANO_NASCIMENTO_INFORMADO','CIDADE','FAMILIARES_A','FAMILIARES_B','CONJUGE']].rename(columns={'LINK': 'LINK_FONTE'})
                
                # CORREÇÃO: Adiciona o DataFrame processado à lista DENTRO do laço 'for'
                dados.append(df_filtrado)

            # Concatena todos os arquivos processados em um único DataFrame final
            df_final = pd.concat(dados, ignore_index=True)
            # print(df_final)




            print(dados)

            


    except Exception as e:
         ClassLogger.logging.error(f"Erro fatal na execução para normalizar: {e}", exc_info=True)       


def calcula_ano(idade_enviada):

        nasc_str = int(idade_enviada)
        if nasc_str in [0]:
            return auxliares.IDADE
        try:
            ano_atual = datetime.now().strftime("%Y")
            return  int(ano_atual) - int(nasc_str)
        except Exception as e:
            print(f"nasc_str estou saindo aqui  no {e}")
            return auxliares.IDADE

def formatar_data(data_envida):
    # print(f"ESTOU SAINDO NO FORMATAR DATA  SEM A HORA ENVIADA :: {data_envida}")
    if isinstance(data_envida, float) or data_envida is None or str(data_envida).lower() == 'nan' or str(data_envida) == auxliares.DATA_PARAO:
        return auxliares.DATA_PARAO
    
        
    data_str = str(data_envida).strip()
    data_str_formmat = re.sub(r'-', '', data_str)
    try:
        data_objeto = datetime.strptime(data_str_formmat, "%d/%m/%Y %H:%M")

        # DOIS TRATAMENTO PARA QUANDO NÃO TIVER HORA NA DATA

    except ValueError:
         
        data_objeto = datetime.strptime(data_str_formmat, "%d/%m/%Y")

        # print(f"minha data data_objeto {data_objeto}")
        data_formatada = data_objeto.strftime("%Y/%m/%d")
        return data_formatada
    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data com o nan: {e}", exc_info=True)
        return auxliares.DATA_PARAO

def formatar_data_hora(data_envida):
    # print(f"ESTOU SAINDO NO FORMATAR DATA  COM HORA ENVIADA :: {data_envida}")
    data_str_formmat = re.sub(r'-', '', data_envida)
    try:
        data_objeto  = datetime.strptime(data_str_formmat,"%d/%m/%Y %H:%M")
        data_formatada = data_objeto.strftime("%Y/%m/%d")
        return data_formatada
    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data: {e}", exc_info=True)
        return auxliares.DATA_PARAO

def achar_idade(nasc,falec):
    nasc_str = str(nasc).strip().lower()
    falec_str = str(falec).strip().lower()


    falec_str = re.sub(r'-', '', falec_str)
    nasc_str = re.sub(r'-', '', nasc_str)
    
    # Verifica se os valores são nulos, vazios ou 'nan'
    if nasc_str in ['nan', '', 'none', '0'] or falec_str in ['nan', '', 'none', '0']:
        return 0 
        
    try:
        # datetime.strptime() funciona apenas em strings individuais
        data_objeto_nas = datetime.strptime(nasc_str, "%d/%m/%Y")
        data_objeto_falec = datetime.strptime(falec_str, "%d/%m/%Y")
        
        # Correção: Ano de Falecimento menos o Ano de Nascimento
        return data_objeto_falec.year - data_objeto_nas.year
    except Exception as e:
        ClassLogger.logging.warning(f'Falha em achar os dados {e}' ,exc_info=True)
        return 0

def tratar_familiares_A(textos):
    
    dados_extraidos = []
    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)
    # filhos_match = re.search(r'deixa (?:os filhos|as filhas|filhos)\s+([^,]+?)(?=\s*,\s*familiares|\s*$)', texto_limpo)
        
    # lista_filhos = []
    # if filhos_match:
    #     trecho_filhos = filhos_match.group(1).strip()
         
    #     lista_filhos = [f.strip() for f in re.split(r',|\s+e\s+', trecho_filhos) if f.strip()]
        
    #     dados_extraidos.append({
    #         'Cônjuge ou Pais': ", ".join(conjuges_pais) if conjuges_pais else "Não informado",
    #         'Filhos': ", ".join(lista_filhos) if lista_filhos else "Não informado"
    #     })

    return ", ".join(conjuges_pais) if conjuges_pais else auxliares.TEXTO_P 


def tratar_familiares_B(textos):
    
    dados_extraidos = []
    texto_limpo = re.sub(r'\(In Memoriam\)', '', textos, flags=re.IGNORECASE)
    # conjuges_pais = re.findall(r'(?:Sr\.|Sra\.|esposa Sra\.|esposo\.|Viúvo\.|Viúva\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)', texto_limpo)
    filhos_match = re.search(r'deixa (?:os filhos|as filhas|filhos)\s+([^,]+?)(?=\s*,\s*familiares|\s*$)', texto_limpo)
        
    lista_filhos = []
    if filhos_match:
        trecho_filhos = filhos_match.group(1).strip()
         
        lista_filhos = [f.strip() for f in re.split(r',|\s+e\s+', trecho_filhos) if f.strip()]
        
    #     dados_extraidos.append({
    #         'Cônjuge ou Pais': ", ".join(conjuges_pais) if conjuges_pais else "Não informado",
    #         'Filhos': ", ".join(lista_filhos) if lista_filhos else "Não informado"
    #     })

    return ", ".join(lista_filhos) if lista_filhos else auxliares.TEXTO_P 

def tratar_familiares_array(lista):
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
    except Exception as e:
            print(f"Data inválida ou formato incorreto {data}")
            print("Data inválida ou formato incorreto.")
            ClassLogger.logging.info(f"Data inválida ou formato incorreto {e} {data}", exc_info=True)
            return auxliares.DATA_PARAO



