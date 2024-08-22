from flask import Flask, request, send_file
import psycopg2
import pandas as pd
from io import BytesIO
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='API Receita Federal',
          description='Documentação da API Receita Federal')

# Configurações do banco de dados
DB_HOST = "postgresql-171633-0.cloudclusters.net"
DB_PORT = "18857"
DB_NAME = "Banco_Receita"
DB_USER = "Sandro"
DB_PASSWORD = "sandro01"

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def formatar_cpf(cpf):
    cpf = cpf.replace(".", "").replace("-", "").replace("/", "")
    if len(cpf) != 11:
        raise ValueError("CPF deve conter 11 dígitos")
    cpf_formatado = "***" + cpf[3:9] + "**"
    return cpf_formatado

def pesquisar_por_nome_e_nome_usuario(cursor, nome, cpf):
    resultados_totais = []
    for i in range(10):
        tabela = f"Socios{i}"
        query = f"SELECT * FROM \"public\".\"{tabela}\" WHERE \"Socios\" LIKE '%{nome}%' AND \"Socios\" LIKE '%{cpf}%'"
        cursor.execute(query)
        resultados = cursor.fetchall()
        if resultados:
            print(f"Resultados encontrados na tabela {tabela}: {resultados}")
            resultados_totais.extend(resultados)
    print(f"Resultados totais: {resultados_totais}")
    return resultados_totais

def pesquisar_cnpj_raiz_socios(cursor, cnpj_raiz_lista):
    resultados_totais = {}
    for i in range(10):
        tabela_socios = f"Socios{i}"
        for cnpj_raiz in cnpj_raiz_lista:
            query_socios = f"SELECT * FROM \"public\".\"{tabela_socios}\" WHERE \"Cnpj Raiz\" = '{cnpj_raiz}'"
            cursor.execute(query_socios)
            resultados_socios = cursor.fetchall()
            if resultados_socios:
                print(f"Resultados encontrados na tabela {tabela_socios}: {resultados_socios}")
                if cnpj_raiz not in resultados_totais:
                    resultados_totais[cnpj_raiz] = []
                resultados_totais[cnpj_raiz].extend([(resultado, tabela_socios) for resultado in resultados_socios])
    print(f"Resultados totais: {resultados_totais}")
    return resultados_totais

def pesquisar_cnpj_raiz_empresas(cursor, cnpj_raiz_lista):
    resultados_totais = {}
    for i in range(10):
        tabela_empresas = f"Empresas{i}"
        for cnpj_raiz in cnpj_raiz_lista:
            query_empresas = f"SELECT * FROM \"public\".\"{tabela_empresas}\" WHERE \"Cnpj Raiz\" = '{cnpj_raiz}'"
            cursor.execute(query_empresas)
            resultados_empresas = cursor.fetchall()
            if resultados_empresas:
                print(f"Resultados encontrados na tabela {tabela_empresas}: {resultados_empresas}")
                if cnpj_raiz not in resultados_totais:
                    resultados_totais[cnpj_raiz] = []
                resultados_totais[cnpj_raiz].extend([(resultado, tabela_empresas) for resultado in resultados_empresas])
    print(f"Resultados totais: {resultados_totais}")
    return resultados_totais

def pesquisar_cnpj_raiz_estabelecimentos(cursor, cnpj_raiz_lista):
    resultados_totais = {}
    for i in range(10):
        tabela_estabelecimentos = f"Estabelecimentos{i}"
        for cnpj_raiz in cnpj_raiz_lista:
            query_estabelecimentos = f"SELECT * FROM \"public\".\"{tabela_estabelecimentos}\" WHERE \"Cnpj Raiz\" = '{cnpj_raiz}'"
            cursor.execute(query_estabelecimentos)
            resultados_estabelecimentos = cursor.fetchall()
            if resultados_estabelecimentos:
                print(f"Resultados encontrados na tabela {tabela_estabelecimentos}: {resultados_estabelecimentos}")
                if cnpj_raiz not in resultados_totais:
                    resultados_totais[cnpj_raiz] = []
                resultados_totais[cnpj_raiz].extend([(resultado, tabela_estabelecimentos) for resultado in resultados_estabelecimentos])
    print(f"Resultados totais: {resultados_totais}")
    return resultados_totais

def limpar_cnpj(cnpj):
    return ''.join(filter(str.isdigit, cnpj))

# Modelos para a documentação Swagger
socio_model = api.model('Socio', {
    'nome': fields.String(required=True, description='Nome do sócio'),
    'cpf': fields.String(required=True, description='CPF do sócio')
})

result_model = api.model('Result', {
    'CNPJ_Raiz': fields.String(description='CNPJ Raiz'),
    'Nome_Empresa': fields.String(description='Nome da Empresa'),
    # Adicione outros campos conforme necessário
})

# Namespace para organizar as rotas
ns = api.namespace('api', description='Operações relacionadas à Receita Federal')

@ns.route('/pesquisar')
class Pesquisa(Resource):
    @ns.expect(socio_model)
    @ns.doc('pesquisar_por_nome_e_cpf')
    @ns.marshal_with(result_model)
    def post(self):
        '''Pesquisa por nome e CPF'''
        nome = request.json.get('nome').upper()
        cpf = request.json.get('cpf')
        try:
            cpf_formatado = formatar_cpf(cpf)
        except ValueError as e:
            return {'erro': str(e)}, 400
        
        conn = connect_to_db()
        if not conn:
            return {'erro': 'Erro ao conectar com o banco de dados'}, 500
        
        cursor = conn.cursor()
        resultados_combinados = []
        
        if nome and cpf:
            resultados_socios = pesquisar_por_nome_e_nome_usuario(cursor, nome, cpf_formatado)
            cnpj_raiz_lista = [resultado[0] for resultado in resultados_socios]
            resultados_socios_cnpj_raiz = pesquisar_cnpj_raiz_socios(cursor, cnpj_raiz_lista)
            resultados_empresas_cnpj_raiz = pesquisar_cnpj_raiz_empresas(cursor, cnpj_raiz_lista)
            resultados_estabelecimentos_cnpj_raiz = pesquisar_cnpj_raiz_estabelecimentos(cursor, cnpj_raiz_lista)
            
            for cnpj_raiz in cnpj_raiz_lista:
                entrada = {
                    "CNPJ_Raiz": cnpj_raiz,
                    "Nome_Empresa": resultados_empresas_cnpj_raiz.get(cnpj_raiz, [None])[0] or 
                                    resultados_estabelecimentos_cnpj_raiz.get(cnpj_raiz, [None])[0] or
                                    resultados_socios_cnpj_raiz.get(cnpj_raiz, [None])[0]
                }
                resultados_combinados.append(entrada)

        conn.close()
        print(f"JSON Resultante: {resultados_combinados}")
        return resultados_combinados

@ns.route('/init')
class InitColumns(Resource):
    @ns.doc('initialize_columns')
    def get(self):
        '''Inicializa as colunas do banco de dados'''
        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            for i in range(10):
                column_names[f'Socios{i}'] = get_column_names(cursor, f'Socios{i}')
                column_names[f'Empresas{i}'] = get_column_names(cursor, f'Empresas{i}')
                column_names[f'Estabelecimentos{i}'] = get_column_names(cursor, f'Estabelecimentos{i}')
            conn.close()
        return "Colunas inicializadas"

@ns.route('/export')
class ExportData(Resource):
    @ns.doc('export_data')
    def post(self):
        '''Exporta os dados para um arquivo Excel'''
        resultados = request.form.get('resultados')
        resultados_combinados = eval(resultados)

        data_dict = {}
        for cnpj_raiz, dados in resultados_combinados.items():
            if cnpj_raiz not in data_dict:
                data_dict[cnpj_raiz] = {}

            for resultado, origem_tabela in dados:
                prefixo = ''
                if 'Socios' in origem_tabela:
                    prefixo = 'Socio_'
                elif 'Empresas' in origem_tabela:
                    prefixo = 'Empresa_'
                elif 'Estabelecimentos' in origem_tabela:
                    prefixo = 'Estabelecimento_'

                for idx, value in enumerate(resultado):
                    nome_coluna = f"{prefixo}Coluna_{idx + 1}"
                    if nome_coluna not in data_dict[cnpj_raiz]:
                        data_dict[cnpj_raiz][nome_coluna] = value if value is not None else ''
                    else:
                        if value is not None and str(value) not in str(data_dict[cnpj_raiz][nome_coluna]):
                            data_dict[cnpj_raiz][nome_coluna] += f", {value}"

        df = pd.DataFrame.from_dict(data_dict, orient='index').reset_index()
        df.rename(columns={'index': 'CNPJ Raiz'}, inplace=True)

        column_mapping = {
            'Empresa_Coluna_2': 'Nome da Empresa',
            'Empresa_Coluna_3': 'Natureza Jurídica',
            'Empresa_Coluna_4': 'Qualificação do Responsável',
            'Empresa_Coluna_5': 'Capital Social',
            'Empresa_Coluna_6': 'Porte da Empresa',
            'Empresa_Coluna_7': 'Ente Federativo',
            'Estabelecimento_Coluna_2': 'Matriz/Filial',
            'Estabelecimento_Coluna_3': 'Nome Fantasia',
            'Estabelecimento_Coluna_4': 'Situação Cadastral',
            'Estabelecimento_Coluna_5': 'Data Situação Cadastral',
            'Estabelecimento_Coluna_6': 'Motivo Situação Cadastral',
            'Estabelecimento_Coluna_7': 'Nome da Cidade no Exterior',
            'Estabelecimento_Coluna_8': 'País da empresa',
            'Estabelecimento_Coluna_9': 'Data de Início de Atividade',
            'Estabelecimento_Coluna_10': 'CNAE Principal',
            'Estabelecimento_Coluna_11': 'CNAE Secundário',
            'Estabelecimento_Coluna_12': 'Correio Eletrônico',
            'Estabelecimento_Coluna_13': 'Situação Especial',
            'Estabelecimento_Coluna_14': 'Data Situação Especial',
            'Estabelecimento_Coluna_15': 'CNPJ Completo',
            'Estabelecimento_Coluna_16': 'Endereço',
            'Estabelecimento_Coluna_17': 'Telefones',
            'Socio_Coluna_2': 'País do Sócio',
            'Socio_Coluna_3': 'Representante Legal',
            'Socio_Coluna_4': 'Nome do Representante',
            'Socio_Coluna_5': 'Qualificação do Representante',
            'Socio_Coluna_6': 'Sócios'
        }

        df.rename(columns=column_mapping, inplace=True)

        if len(df.columns) > 25:
            df.drop(df.columns[[0, 1, 8, 25]], axis=1, inplace=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        output.seek(0)

        return send_file(output, as_attachment=True, download_name='resultados.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Registrando o namespace
api.add_namespace(ns)

def get_column_names(cursor, table_name):
    cursor.execute(f"SELECT * FROM \"public\".\"{table_name}\" LIMIT 0")
    return [desc[0] for desc in cursor.description]

column_names = {}

if __name__ == "__main__":
    app.run(debug=True)
