import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import tempfile
import matplotlib.pyplot as plt
import io

# Simulação banco de dados simples usando CSV local
# No seu projeto, adapte para banco real ou outro meio persistente

USUARIOS_CSV = "usuarios.csv"
CADASTROS_CSV = "cadastros.csv"


def carregar_usuarios():
    try:
        return pd.read_csv(USUARIOS_CSV)
    except FileNotFoundError:
        return pd.DataFrame(columns=["usuario", "senha"])


def salvar_usuarios(df):
    df.to_csv(USUARIOS_CSV, index=False)


def verificar_login(usuario, senha):
    df = carregar_usuarios()
    user = df[(df['usuario'] == usuario) & (df['senha'] == senha)]
    return not user.empty


def criar_usuario(usuario, senha):
    df = carregar_usuarios()
    if usuario in df['usuario'].values:
        return False
    df = df.append({"usuario": usuario, "senha": senha}, ignore_index=True)
    salvar_usuarios(df)
    return True


def carregar_cadastros():
    try:
        return pd.read_csv(CADASTROS_CSV)
    except FileNotFoundError:
        # Colunas conforme o formulário
        cols = ['id', 'nome', 'cpf', 'nascimento', 'email', 'telefone', 'tipo', 'matricula',
                'classe', 'sala', 'ano_ingresso', 'cep', 'rua', 'numero', 'complemento',
                'bairro', 'cidade', 'estado']
        return pd.DataFrame(columns=cols)


def salvar_cadastros(df):
    df.to_csv(CADASTROS_CSV, index=False)


def cadastrar_pessoa(dados):
    df = carregar_cadastros()
    novo_id = 1 if df.empty else df['id'].max() + 1
    nova_linha = dict(zip(df.columns[1:], dados))  # Ignorar 'id' pois vai colocar novo
    nova_linha['id'] = novo_id
    df = df.append(nova_linha, ignore_index=True)
    salvar_cadastros(df)


def atualizar_pessoa(id_pessoa, dados):
    df = carregar_cadastros()
    if id_pessoa in df['id'].values:
        for i, col in enumerate(df.columns[1:]):
            df.loc[df['id'] == id_pessoa, col] = dados[i]
        salvar_cadastros(df)


def excluir_pessoa(id_pessoa):
    df = carregar_cadastros()
    df = df[df['id'] != id_pessoa]
    salvar_cadastros(df)


def gerar_pdf(df, titulo, path_imagem):
    # Usaremos reportlab para gerar PDF simples
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle, Paragraph, Image
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()
    styleH = styles['Heading1']

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, titulo)

    # Inserir imagem gráfico
    c.drawImage(path_imagem, 50, height - 250, width=500, height=150)

    # Tabela dados (limitar linhas para caber no PDF)
    data = [list(df.columns)]
    for idx, row in df.head(20).iterrows():
        data.append(list(row))

    table = Table(data, colWidths=[50] + [80]*(len(df.columns)-1))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,0), 10),
        ('BOTTOMPADDING', (0,0),(-1,0), 6),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    # Posicionar tabela um pouco abaixo da imagem
    table.wrapOn(c, width, height)
    table.drawOn(c, 30, height - 500)

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


# Inicialização da sessão
if 'login' not in st.session_state:
    st.session_state['login'] = False
    st.session_state['usuario'] = None

# Interface
st.title("📚 Sistema de Cadastro Simples")

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
                st.success(f"Bem-vindo {usuario}!")
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
    st.sidebar.title(f"Olá, {st.session_state['usuario']} 👋")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Menu", ["Cadastrar", "Visualizar", "Relatórios", "Gráficos", "Sair"])
    st.sidebar.markdown("---")

    if menu == "Cadastrar":
        st.subheader("📋 Cadastro de Pessoa")

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

        with st.expander("Selecionar Pessoa para Atualizar ou Excluir"):
            df = carregar_cadastros()
            if not df.empty:
                pessoa_selecionada = st.selectbox(
                    "Selecione a pessoa (pelo ID e nome):",
                    options=df.apply(lambda x: f"{x['id']} - {x['nome']}", axis=1)
                )
                id_selecionado = int(pessoa_selecionada.split(" - ")[0])
                dados_pessoa = df[df['id'] == id_selecionado].iloc[0]

                form_vars.update({
                    'id': dados_pessoa['id'],
                    'nome': dados_pessoa['nome'],
                    'cpf': dados_pessoa['cpf'],
                    'nascimento': pd.to_datetime(dados_pessoa['nascimento']) if pd.notna(dados_pessoa['nascimento']) else None,
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
            else:
                st.info("Nenhum cadastro para selecionar.")

        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                nome = st.text_input("Nome Completo", value=form_vars['nome'])
                cpf = st.text_input("CPF", value=form_vars['cpf'])
                nascimento = st.date_input(
                    "Data de Nascimento",
                    value=form_vars['nascimento'] if form_vars['nascimento'] else datetime(2000, 1, 1),
                    max_value=datetime.now()
                )
                email = st.text_input("Email", value=form_vars['email'])
                telefone = st.text_input("Telefone", value=form_vars['telefone'])
                tipo_options = ["Aluno", "Professor", "Funcionário", "Outro"]
                tipo_idx = tipo_options.index(form_vars['tipo']) if form_vars['tipo'] in tipo_options else 0
                tipo = st.selectbox("Tipo", options=tipo_options, index=tipo_idx)

            with col2:
                matricula = st.text_input("Matrícula", value=form_vars['matricula'])
                classe = st.text_input("Classe", value=form_vars['classe'])
                sala = st.text_input("Sala", value=form_vars['sala'])
                ano_ingresso = st.text_input("Ano de Ingresso", value=form_vars['ano_ingresso'])
                cep = st.text_input("CEP", value=form_vars['cep'])
                rua = st.text_input("Rua", value=form_vars['rua'])

            with col3:
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
            st.dataframe(df, use_container_width=True)

    elif menu == "Relatórios":
        st.subheader("📄 Gerar Relatório em PDF")
        df = carregar_cadastros()
        if df.empty:
            st.warning("Nenhum dado para gerar relatório.")
        else:
            if st.button("Gerar PDF"):
                plt.figure(figsize=(6, 3))
                tipo_counts = df['tipo'].value_counts()
                tipo_counts.plot(kind='bar', color='skyblue')
                plt.title("Quantidade por Tipo")
                plt.xlabel("Tipo")
                plt.ylabel("Quantidade")
                plt.tight_layout()

                grafico_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
                plt.savefig(grafico_path)
                plt.close()

                pdf_buffer = gerar_pdf(df, "Relatório de Cadastros", grafico_path)
                b64 = base64.b64encode(pdf_buffer.read()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_cadastros.pdf">Clique aqui para baixar o PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

    elif menu == "Gráficos":
        st.subheader("📈 Gráficos de Cadastros")
        df = carregar_cadastros()
        if df.empty:
            st.warning("Nenhum dado para gerar gráficos.")
        else:
            tipo_counts = df['tipo'].value_counts()
            st.bar_chart(tipo_counts)

    elif menu == "Sair":
        sair = st.button("Confirmar Logout")
        if sair:
            st.session_state['login'] = False
            st.session_state['usuario'] = None
            st.success("Logout realizado com sucesso!")
            st.experimental_rerun()
