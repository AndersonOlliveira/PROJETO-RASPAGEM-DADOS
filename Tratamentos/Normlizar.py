import os
import re
import numpy as np
import pandas as pd
from datetime import time,datetime
from pathlib import Path
from Logs import ClassLogger
from utils.unicode import remover
from services.crawler import iniciar




def arquivos_process(self):
    ClassLogger.logging.info("ACESSANDO PAGINA PARA PROCESSAR OS DADOS")
    ClassLogger.logging.info("REALIZAR A NORMALIZAR!!")


    # print(obter_servidores(self,[1, 7, 12]))

    # return
    # 
    registros = self.servidores.get(6)

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
            df = pd.read_csv(f"{arquivos}/{arquivo}", sep=";")
            # Ajusta cabeçalho 
            df.columns = df.columns.str.strip().str.rstrip(':').str.strip().str.replace(' ', '_')

            df.rename(columns={'FALECIMENTO': 'DATA_FALECIMENTO','DATA_NACIMENTO': 'DATA_NASCIMENTO'}, inplace=True)

            print(df.columns)
            # print(df)

            # VALIDAR A IDADE - Extrai apenas números de cada célula
            # match 'IDADE':
            #     case 200:
            #         print("Success")
            #     case 400:
            #         print("Bad Request")
            #     case 404:
            #         print("Not Found")
            #     case _:
            #         print("Unknown Status")  # Default case
            if 'NOME' in df.columns:


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
                    df['IDADE'] = df.apply(lambda row: achar_idade(row['DATA_NASCIMENTO'], row['DATA_FALECIMENTO']), axis=1)

                if 'FAMILIARES' in df.columns:
                    df['FAMILIARES_A'] =  df['FAMILIARES'].apply(tratar_familiares_A).str.upper()
                    df['FAMILIARES_B'] =  df['FAMILIARES'].apply(tratar_familiares_B).str.upper()
                else:
                    df['FAMILIARES_A'] = 'SEM FAMILIARES INFORMADO'
                    df['FAMILIARES_B'] = 'SEM FAMILIARES INFORMADO'
                # print(df['IDADE'])
                
                # Aplica as funções nas colunas
                df['ANO_NASCIMENTO_ESTIMADO'] = df['IDADE'].apply(calcula_ano)
                if 'DATA_NASCIMENTO' in df.columns:
                    df['ANO_NASCIMENTO_INFORMADO'] = df['DATA_NASCIMENTO'].apply(formatar_data)
                else:
                    df['ANO_NASCIMENTO_INFORMADO'] = "SEM DATA INFORMADA"
                if 'DATA_FALECIMENTO' in df.columns:
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].astype(str).str.strip("()', ")
                    df['DATA_FALECIMENTO'] = df['DATA_FALECIMENTO'].apply(formatar_data)
                else:
                    df['DATA_FALECIMENTO'] = "SEM DATA DE FALECIMENTO INFORMADA" # CASO NÃO TENHA DATA

                df['NOME'] = df['NOME'].apply(remover).str.upper()
                if 'DATA_CAPTURA' in df.columns:
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].astype(str).str.strip("()', ")
                    df['DATA_CAPTURA'] = df['DATA_CAPTURA'].apply(formatar_data_hora)
                else:
                    df['DATA_CAPTURA'] = "SEM DATA CAPTURA" # CASO NÃO TENHA DATA
                if 'LINK' in df.columns:
                    df['LINK'] = df['LINK']
                else:
                    df['LINK'] = registros['nome'] # PEGA O NOME QUANDO NÃO TIVER O LINK

                if 'CIDADE' in df.columns:
                    df['CIDADE'] = df['CIDADE'].str.upper()
                else:
                    df['CIDADE'] = 'CIDADE NÃO INFORMADA'
                
                # Filtra apenas as colunas desejadas para o resultado final
                df_filtrado = df[['NOME', 'IDADE','DATA_FALECIMENTO','ANO_NASCIMENTO_ESTIMADO', 'LINK','DATA_CAPTURA','ANO_NASCIMENTO_INFORMADO','CIDADE','FAMILIARES_A','FAMILIARES_B']].rename(columns={'LINK': 'LINK_FONTE'})
                
                # CORREÇÃO: Adiciona o DataFrame processado à lista DENTRO do laço 'for'
                dados.append(df_filtrado)

            # Concatena todos os arquivos processados em um único DataFrame final
            df_final = pd.concat(dados, ignore_index=True)
            # print(df_final)




            # print(dados)

            


    except Exception as e:
         ClassLogger.logging.error(f"Erro fatal na execução para normalizar: {e}", exc_info=True)       


def calcula_ano(idade_enviada):

        nasc_str = int(idade_enviada)
        if nasc_str in [0]:
            return 0 
        try:
            ano_atual = datetime.now().strftime("%Y")
            return  int(ano_atual) - int(nasc_str)
        except Exception as e:
            print(f"nasc_str estou saindo aqui  no {e}")
            return 0

def formatar_data(data_envida):
    print(f"minha data enviada {data_envida}")
    if isinstance(data_envida, float) or data_envida is None or str(data_envida).lower() == 'nan' or str(data_envida) == '0000/00/00':
        return '0000/00/00'
        
    data_str = str(data_envida).strip()
    
   
    try:
        data_objeto = datetime.strptime(data_str, "%d/%m/%Y %H:%M")

    except ValueError:
         
        data_objeto = datetime.strptime(data_str, "%d/%m/%Y")

        print(f"minha data data_objeto {data_objeto}")
        data_formatada = data_objeto.strftime("%Y/%m/%d")
        return data_formatada
    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data com o nan: {e}", exc_info=True)
        return '0000/00/00'

def formatar_data_hora(data_envida):
    # print(f"minha data enviada {data_envida}")
    try:
        data_objeto  = datetime.strptime(data_envida,"%d/%m/%Y %H:%M")
        data_formatada = data_objeto.strftime("%Y/%m/%d")
        return data_formatada
    except Exception as e:
        ClassLogger.logging.info(f"Erro em formatar a data: {e}", exc_info=True)
        return '0000/00/00'

def achar_idade(nasc,falec):
    nasc_str = str(nasc).strip().lower()
    falec_str = str(falec).strip().lower()
    
    # Verifica se os valores são nulos, vazios ou 'nan'
    if nasc_str in ['nan', '', 'none', '0'] or falec_str in ['nan', '', 'none', '0']:
        return 0 
        
    try:
        # datetime.strptime() funciona apenas em strings individuais
        data_objeto_nas = datetime.strptime(nasc_str, "%d/%m/%Y")
        data_objeto_falec = datetime.strptime(falec_str, "%d/%m/%Y")
        
        # Correção: Ano de Falecimento menos o Ano de Nascimento
        return data_objeto_falec.year - data_objeto_nas.year
    except Exception:
        # Caso alguma data venha em formato totalmente inválido que quebre o strptime
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

    return ", ".join(conjuges_pais) if conjuges_pais else "Não informado"


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

    return ", ".join(lista_filhos) if lista_filhos else "Não informado"




