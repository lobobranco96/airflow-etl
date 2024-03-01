# Projeto ETL (Extrair, Transformar e Carregar) - Airflow Data Pipeline
Este projeto consiste em um pipeline de dados para a extração de informações de produtos de hardware do site Kabum, a transformação desses dados em DataFrames formatados e, por fim, o carregamento dos DataFrames resultantes no Amazon S3.

Extrair
A etapa de extração é realizada em duas partes:

1. Scraping do Site Kabum
A função extract_kabum é responsável por fazer o scraping dos dados dos produtos de hardware de uma página específica do site Kabum e armazená-los em arquivos CSV. Essa função segue os seguintes passos:

- Construção da URL base para a categoria de hardware fornecida como parâmetro.
- Configuração do WebDriver para navegação headless, utilizando o Selenium WebDriver para Chrome.
- Acesso à página da categoria de hardware usando o WebDriver.
- Aguardo de 2 segundos para garantir que a página carregue completamente.
- Obtenção da data atual no formato YYYY-MM-DD.
- Parseamento HTML utilizando BeautifulSoup para analisar o HTML da página e extrair informações.
- Extração da quantidade total de itens na categoria.
- Criação de uma estrutura de dados para armazenar os resultados.
- Iteração sobre todas as páginas da categoria, extraindo os dados dos produtos em cada página.
- Encerramento da sessão do WebDriver após a conclusão da extração.
- Criação de um DataFrame Pandas com os dados extraídos e exportação para um arquivo CSV com um nome baseado na data atual e na categoria de hardware.

2. Listagem de Arquivos CSV
A função extrair_arquivos extrai os nomes dos arquivos CSV presentes em um diretório especificado. Seu funcionamento é resumido da seguinte forma:

- Verificação da existência do diretório especificado.
- Iteração sobre os arquivos no diretório, identificando arquivos CSV.
- Apresentação dos arquivos CSV encontrados.
- Retorno da lista de arquivos CSV.
- 
Transformar
A etapa de transformação é realizada pela função transformar_arquivo_csv, que tem como objetivo transformar os arquivos CSV em DataFrames formatados antes de enviá-los para o Amazon S3. Essa função segue os seguintes passos:

- Obtenção dos arquivos CSV extraídos na etapa anterior.
- Verificação da existência de arquivos CSV.
- Iteração sobre os arquivos CSV, aplicando transformações nos dados.
- Armazenamento dos DataFrames transformados em um dicionário.
- Envio dos DataFrames transformados como uma XCom para a próxima tarefa.
- 
Carregar
A etapa de carregamento é realizada pela função enviar_para_s3, responsável por enviar os DataFrames transformados para o Amazon S3. Seu funcionamento é resumido da seguinte forma:

- Obtenção dos DataFrames transformados.
- Verificação da existência de DataFrames.
- Envio dos DataFrames para o S3, onde cada DataFrame é salvo como um arquivo CSV separado.

Configuração
- Diretório de Origem: /opt/airflow/raw_excel_file/
- Bucket do S3: airflow-lobobranco
- Caminho no S3: excel_file/
  
Dependências
- Apache Airflow: Orquestração de tarefas.
- Pandas: Manipulação de dados em formato tabular.
- Boto3: Cliente da AWS para interagir com o Amazon S3.

Execução
A DAG está configurada para iniciar em 1º de março de 2024, com uma frequência de execução a cada 30 minutos (30 * * * *). O fluxo de execução segue a ordem: extrair arquivos -> transformar arquivos CSV -> enviar para S3.

Observações
- O código está configurado para lidar com possíveis erros durante o processamento e envio dos dados.
- Mensagens de log são fornecidas para informar o progresso e possíveis problemas durante a execução do pipeline.
  
Esta documentação fornece uma visão geral do projeto ETL Kabum Data Pipeline, descrevendo suas etapas, componentes principais e configurações necessárias para sua execução.





