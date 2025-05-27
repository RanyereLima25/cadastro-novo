import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import tempfile
from io import BytesIO
from fpdf import FPDF
import base64

# --- Configuração da página ---
st.set_page_config(page_title="Sistema Completo de Cadastro", layout="wide")
st.title("🔐 Sistema de Cadastro - Streamlit")

# --- Conexão com banco ---
conn = sqlite3.connect('cadastro.db', check_same_thread=False)
cursor = conn.cursor()

# --- Criar tabelas se não existem ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    nascimento TEXT,
    email TEXT,
    telefone TEXT,
    tipo TEXT,
    matricula TEXT,
    classe TEXT,
    sala TEXT,
    ano_ingresso TEXT,
    cep TEXT,
    rua TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    estado TEXT,
    data_cadastro TEXT
);
""")
conn.commit()

# --- Funções Auxiliares ---

def criar_usuario(login, senha):
    try:
        senha_hash = generate_password_hash(senha)
        cursor.execute("INSERT INTO usuarios (login, senha_hash) VALUES (?, ?)", (login, senha_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_login(login, senha):
    cursor.execute("SELECT senha_hash FROM usuarios WHERE login = ?", (login,))
    resultado = cursor.fetchone()
    if resultado and check_password_hash(resultado[0], senha):
        return True
    return False

def cadastrar_pessoa(dados):
    data_cadastro = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO pessoas (
            nome, cpf, nascimento, email, telefone, tipo, matricula, classe,
            sala, ano_ingresso, cep, rua, numero, complemento, bairro, cidade, estado, data_cadastro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (*dados, data_cadastro))
    conn.commit()

def atualizar_pessoa(id, dados):
    cursor.execute("""
        UPDATE pessoas SET
        nome=?, cpf=?, nascimento=?, email=?, telefone=?, tipo=?, matricula=?, classe=?,
        sala=?, ano_ingresso=?, cep=?, rua=?, numero=?, complemento=?, bairro=?, cidade=?, estado=?
        WHERE id=?
    """, (*dados, id))
    conn.commit()

def excluir_pessoa(id):
    cursor.execute("DELETE FROM pessoas WHERE id=?", (id,))
    conn.commit()

def carregar_cadastros():
    return pd.read_sql_query("SELECT * FROM pessoas", conn)

# --- Função para gerar PDF com cabeçalho, tabela e gráfico ---
def gerar_pdf(df, titulo="Relatório", grafico_path=None):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.ln(10)

    # Tabela (limitar colunas para visualização no PDF)
    pdf.set_font("Arial", 'B', 10)
    colunas = ['id', 'nome', 'cpf', 'email', 'tipo', 'classe', 'ano_ingresso', 'data_cadastro']
    espacamento = [10, 45, 25, 50, 15, 15, 20, 30]

    # Cabeçalho tabela
    for i, col in enumerate(colunas):
        pdf.cell(espacamento[i], 8, col.upper(), border=1, align='C')
    pdf.ln()

    # Linhas da tabela (limitar até 30 linhas para o PDF não ficar gigante)
    pdf.set_font("Arial", '', 9)
    for i, row in df[colunas].head(30).iterrows():
        for j, col in enumerate(colunas):
            texto = str(row[col]) if pd.notna(row[col]) else ""
            pdf.cell(espacamento[j], 7, texto, border=1)
        pdf.ln()

    pdf.ln(10)

    # Inserir gráfico (se houver)
    if grafico_path:
        pdf.image(grafico_path, x=30, w=150)

    # Salvar em buffer
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- Função para limpar campos do formulário ---
def limpar_form(form_vars):
    for key in form_vars:
        form_vars[key] = None

# --- Sistema de Navegação ---

if 'login' not in st.session_state:
    st.session_state['login'] = False

if not st.session_state['login']:
    st.subheader("🔑 Login")
    aba = st.radio("Selecione:", ["Entrar", "Criar Conta"])

    if aba == "Entrar":
        usuario = st.text_input("Usuário", key="login_usuario")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            if verificar_login(usuario, senha):
                st.session_state['login'] = True
                st.session_state['usuario'] = usuario
                st.success(f"Bem-vindo {usuario}")
                st.experimental_rerun()
            else:
                st.error("Login ou senha incorretos.")

    elif aba == "Criar Conta":
        novo_usuario = st.text_input("Novo Usuário", key="novo_usuario")
        nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha")
        if st.button("Cadastrar Usuário"):
            if criar_usuario(novo_usuario, nova_senha):
                st.success("Usuário criado com sucesso! Faça login.")
            else:
                st.error("Erro: Usuário já existe.")

else:
    st.sidebar.success(f"Logado como {st.session_state['usuario']}")
    menu = st.sidebar.radio("Menu", ["Cadastrar", "Visualizar", "Relatórios", "Gráficos", "Sair"])

    if menu == "Cadastrar":
        st.subheader("📋 Cadastro de Pessoa")

        # Variáveis para controle do formulário (para limpar e atualizar)
        form_vars = {
            'id': None,
            'nome': None,
            'cpf': None,
            'nascimento': None,
            'email': None,
            'telefone': None,
            'tipo': None,
            'matricula': None,
            'classe': None,
            'sala': None,
            'ano_ingresso': None,
            'cep': None,
            'rua': None,
            'numero': None,
            'complemento': None,
            'bairro': None,
            'cidade': None,
            'estado': None
        }

        # Se quiser atualizar, primeiro escolher registro para edição
        with st.expander("Selecionar Pessoa para Atualizar ou Excluir"):
            df = carregar_cadastros()
            if not df.empty:
                pessoa_selecionada = st.selectbox(
                    "Selecione a pessoa (pelo ID e nome):",
                    options=df.apply(lambda x: f"{x['id']} - {x['nome']}", axis=1)
                )
                id_selecionado = int(pessoa_selecionada.split(" - ")[0])
                dados_pessoa = df[df['id'] == id_selecionado].iloc[0]

                # Mostrar dados preenchidos para edição
                form_vars.update({
                    'id': dados_pessoa['id'],
                    'nome': dados_pessoa['nome'],
                    'cpf': dados_pessoa['cpf'],
                    'nascimento': pd.to_datetime(dados_pessoa['nascimento']) if dados_pessoa['nascimento'] else None,
                    'email': dados_pessoa['email'],
                    'telefone': dados_pessoa['telefone'],
                    'tipo': dados_pessoa['tipo'],
                    'matricula': dados_pessoa['matricula'],
                    'classe': dados_pessoa['classe'],
                    'sala': dados_pessoa['sala'],
                    'ano_ingresso': dados_pessoa['ano_ingresso'],
                    'cep': dados_pessoa['cep'],
                    'rua': dados_pessoa['rua'],
                    'numero': dados_pessoa['numero'],
                    'complemento': dados_pessoa['complemento'],
                    'bairro': dados_pessoa['bairro'],
                    'cidade': dados_pessoa['cidade'],
                    'estado': dados_pessoa['estado'],
                })

                if st.button("Excluir Cadastro"):
                    excluir_pessoa(id_selecionado)
                    st.success("Cadastro excluído com sucesso!")
                    st.experimental_rerun()

        with st.form("form_cadastro", clear_on_submit=False):
            nome = st.text_input("Nome Completo", value=form_vars['nome'])
            cpf = st.text_input("CPF", value=form_vars['cpf'])
            nascimento = st.date_input("Data de Nascimento", value=form_vars['nascimento'] if form_vars['nascimento'] else datetime(2000,1,1))
            email = st.text_input("Email", value=form_vars['email'])
            telefone = st.text_input("Telefone", value=form_vars['telefone'])
            tipo = st.selectbox("Tipo", options=["Aluno", "Professor", "Funcionário", "Outro"], index=["Aluno", "Professor", "Funcionário", "Outro"].index(form_vars['tipo']) if form_vars['tipo'] in ["Aluno", "Professor", "Funcionário", "Outro"] else 0)
            matricula = st.text_input("Matrícula", value=form_vars['matricula'])
            classe = st.text_input("Classe", value=form_vars['classe'])
            sala = st.text_input("Sala", value=form_vars['sala'])
            ano_ingresso = st.text_input("Ano de Ingresso", value=form_vars['ano_ingresso'])
            cep = st.text_input("CEP", value=form_vars['cep'])
            rua = st.text_input("Rua", value=form_vars['rua'])
            numero = st.text_input("Número", value=form_vars['numero'])
            complemento = st.text_input("Complemento", value=form_vars['complemento'])
            bairro = st.text_input("Bairro", value=form_vars['bairro'])
            cidade = st.text_input("Cidade", value=form_vars['cidade'])
            estado = st.text_input("Estado", value=form_vars['estado'])

            enviar = st.form_submit_button("Salvar")

            if enviar:
                dados = (nome, cpf, nascimento.strftime('%Y-%m-%d'), email, telefone, tipo, matricula, classe,
                         sala, ano_ingresso, cep, rua, numero, complemento, bairro, cidade, estado)

                if form_vars['id'] is None:
                    cadastrar_pessoa(dados)
                    st.success("Cadastro realizado com sucesso!")
                else:
                    atualizar_pessoa(form_vars['id'], dados)
                    st.success("Cadastro atualizado com sucesso!")

                st.experimental_rerun()

    elif menu == "Visualizar":
        st.subheader("📊 Visualizar Cadastros")
        df = carregar_cadastros()
        if df.empty:
            st.warning("Nenhum cadastro encontrado.")
        else:
            st.dataframe(df)

    elif menu == "Relatórios":
        st.subheader("📄 Gerar Relatório em PDF")
        df = carregar_cadastros()
        if df.empty:
            st.warning("Nenhum dado para gerar relatório.")
        else:
            if st.button("Gerar PDF"):
                # Gerar gráfico simples para o relatório
                plt.figure(figsize=(6,3))
                tipo_counts = df['tipo'].value_counts()
                tipo_counts.plot(kind='bar', color='skyblue')
                plt.title("Quantidade por Tipo")
                plt.xlabel("Tipo")
                plt.ylabel("Quantidade")
                plt.tight_layout()

                # Salvar gráfico temporariamente
                grafico_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
                plt.savefig(grafico_path)
                plt.close()

                pdf_buffer = gerar_pdf(df, "Relatório de Cadastros", grafico_path)
                b64 = base64.b64encode(pdf_buffer.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio.pdf">⬇️ Clique para baixar o PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

    elif menu == "Gráficos":
        st.subheader("📈 Gráficos dos Cadastros")
        df = carregar_cadastros()
        if df.empty:
            st.warning("Nenhum dado para gerar gráfico.")
        else:
            st.bar_chart(df['tipo'].value_counts())

    elif menu == "Sair":
        st.session_state['login'] = False
        st.session_state.pop('usuario', None)
        st.experimental_rerun()
