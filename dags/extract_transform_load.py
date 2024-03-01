from datetime import datetime
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python_operator import PythonOperator
import os
import pandas as pd
import re
import os
import boto3
from datetime import datetime, timedelta

diretorio = '/opt/airflow/raw_excel_file/'

def extrair_arquivos(diretorio):
    """
    Esta função extrai arquivos CSV de um diretório específico.

    Parâmetros:
    - diretorio (str): O caminho do diretório onde os arquivos CSV estão localizados.

    Retorna:
    - arquivos_csv (list): Uma lista contendo os nomes dos arquivos CSV encontrados no diretório.
    """
    arquivos_csv = []

    if os.path.exists(diretorio):
        for arquivo in os.listdir(diretorio):
            if arquivo.endswith('.csv'):
                arquivos_csv.append(arquivo)
        print(f"Arquivos CSV encontrados: {arquivos_csv}")
    else:
        print(f"O diretório '{diretorio}' não existe.")
        
    return arquivos_csv

def transformar_arquivo_csv(ti):   
    """
    Esta função transforma arquivos CSV em DataFrames Pandas e realiza operações de limpeza nos dados.

    Parâmetros:
    - ti: O objeto de contexto do Airflow.
    
    Retorna:
    - lista_df (dict): Um dicionário contendo os DataFrames Pandas resultantes da transformação dos arquivos CSV.
    """

    arquivos_csv = ti.xcom_pull(task_ids='extrair_arquivos')
    diretorio = '/opt/airflow/raw_excel_file/'
    lista_df = {}  
    
    try:
        if not arquivos_csv:
            print("A lista de arquivos CSV está vazia.")
            return None

        for tipo_produto in arquivos_csv:
            nome_tabela = tipo_produto.replace('.csv', '').replace('-', '_').replace('.', '_').replace(' ', '_')
            caminho_arquivo = f'{diretorio}/{tipo_produto}'
            print(f"Transformando arquivo CSV: {caminho_arquivo}")
            
            try:
                df = pd.read_csv(caminho_arquivo, on_bad_lines='skip', sep=';', header=0, decimal=',')
            except Exception as e:
                print(f"Erro ao ler o arquivo CSV {caminho_arquivo}: {e}")
                continue  

            if df.empty:
                print(f"DataFrame vazio para o arquivo {tipo_produto}.")
                continue  

            df['Preço em R$'] = df['Preço em R$'].str.replace('R\$', '', regex=True).str.replace('\xa0', '', regex=True).str.replace('----', '0', regex=True)

            if 'ID' in df.columns:
                df.set_index('ID', inplace=True)
            
            df['Nome do produto'] = df['Descrição'].str.split(pat=',', n=1).str[0]
            df = df.reindex(columns=['Nome do produto', 'Descrição', 'Preço em R$'])
            df['Descrição'] = df.apply(lambda row: row['Descrição'].replace(row['Nome do produto'], '').strip(), axis=1)
            df['Preço em R$'] = df['Preço em R$'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Preço em R$'] = df['Preço em R$'].astype(float) / 100 * 100
            
            lista_df[nome_tabela] = df
        
        ti.xcom_push(key='lista_df', value=lista_df)

        return lista_df  
    except Exception as e:
        print(f"Erro ao processar os arquivos CSV: {e}")
        return None

def enviar_para_s3(ti, **kwargs):
    """
    Esta função envia DataFrames Pandas para o Amazon S3.

    Parâmetros:
    - ti: O objeto de contexto do Airflow.
    - **kwargs: Argumentos adicionais.

    Retorna:
    - None
    """
    try:
        lista_df = ti.xcom_pull(task_ids='transformar_arquivos_csv', key='lista_df')
        
        if not lista_df:
            raise ValueError("A lista de DataFrames está vazia. Não é possível enviar para o S3.")
        
        for tabela, df in lista_df.items():
            if df.empty:
                print(f"DataFrame vazio encontrado para a tabela '{tabela}'. Ignorando...")
                continue
            
            print(f"Enviando dados para a tabela '{tabela}' no S3...")
            hook = S3Hook(aws_conn_id='aws_default')
            arquivo_temporario = f'/tmp/{tabela}.csv'
            df.to_csv(arquivo_temporario, index=False)
            hook.load_file(
                filename=arquivo_temporario,
                key=f"{caminho_s3}/{tabela}.csv",
                bucket_name=bucket_name,
                replace=True
            )
            print(f"Dados da tabela '{tabela}' enviados com sucesso para o bucket '{bucket_name}' no caminho '{caminho_s3}'")
    except Exception as e:
        print(f"Erro ao enviar dados para o S3: {e}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('extrair_transformar_s3', default_args=default_args, schedule_interval='30 * * * *') as dag:
    """
    Esta DAG executa um fluxo de trabalho para extrair arquivos CSV de um diretório, transformá-los em DataFrames Pandas
    e enviá-los para o Amazon S3.

    Parâmetros:
    - 'extrair_transformar_s3': Nome da DAG.
    - default_args: Argumentos padrão para a DAG, como proprietário, horário de início, etc.
    - schedule_interval: Intervalo de agendamento para a execução da DAG.

    Retorna:
    - None
    """
    diretorio_arquivos = '/opt/airflow/raw_excel_file/'
    bucket_name = 'airflow-lobobranco'
    caminho_s3 = 'excel_file/'

    extrair_arquivos_task = PythonOperator(
        task_id='extrair_arquivos',
        python_callable=extrair_arquivos,
        op_kwargs={'diretorio': diretorio_arquivos}
    )

    transformar_arquivos_task = PythonOperator(
        task_id='transformar_arquivos_csv',
        python_callable=transformar_arquivo_csv,
        op_kwargs={'diretorio': diretorio_arquivos},
        provide_context=True
    )

    enviar_s3_task = PythonOperator(
        task_id='enviar_para_s3',
        python_callable=enviar_para_s3,
        op_kwargs={'bucket_name': bucket_name, 'caminho_s3': caminho_s3},
        provide_context=True
    )

    extrair_arquivos_task >> transformar_arquivos_task >> enviar_s3_task
