import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ------------------------------------------------------------
# CONFIGURAÇÃO
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Chamados",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000000 !important; font-size: 14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000000 !important; background-color: #d9e4f5 !important; border: 1px solid #000000 !important; padding: 6px 12px !important; border-radius: 5px !important; font-weight: bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000000 !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000000 !important; background-color: #f0f0f0 !important; }
div[data-baseweb="select"] > div, div[data-baseweb="select"] input, div[data-baseweb="select"] span { background-color: #f0f0f0 !important; color: #000000 !important; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# SIDEBAR – Upload
# ------------------------------------------------------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# Antes do upload
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")

# ------------------------------------------------------------
# Processamento após upload
# ------------------------------------------------------------
if uploaded_file is not None:

    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()

    # ------------------------------------------------------------
    # DETECÇÃO DO TIPO DE RELATÓRIO
    # ------------------------------------------------------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura", "Criado por",
        "Causa raiz", "Tipo de registro do caso", "Caso modificado pela última vez por"
    ]
    if all(col in df.columns for col in colunas_consumer):
        titulo_dashboard = "📊 Chamados Consumer"
        relatorio_tipo = "consumer"
    else:
        titulo_dashboard = "📊 Chamados NMC Enterprise"
        relatorio_tipo = "enterprise"

    # Título após upload
    st.title(titulo_dashboard)

    # ------------------------------------------------------------
    # MAPEAMENTO DE COLUNAS
    # ------------------------------------------------------------
    mapa = {
        'Status': None if relatorio_tipo == "consumer" else 'Status',
        'Fechado por': None if relatorio_tipo == "consumer" else 'Fechado por',
        'Histórico': None if relatorio_tipo == "consumer" else 'Histórico',
        'Reclamação': 'Assunto' if relatorio_tipo == "consumer" else 'Reclamação',
        'Criado por': 'Criado por',
        'Diagnóstico': 'Causa raiz' if relatorio_tipo == "consumer" else 'Diagnóstico',
        'Data de abertura': 'Data/Hora de abertura' if relatorio_tipo == "consumer" else 'Data de abertura',
        'Hora de abertura': None if relatorio_tipo == "consumer" else 'Hora de abertura',
        'Data de fechamento': None if relatorio_tipo == "consumer" else 'Data de fechamento',
        'Hora de fechamento': None if relatorio_tipo == "consumer" else 'Hora de fechamento',
    }

    # ------------------------------------------------------------
    # Substituir NMC Auto (Enterprise)
    # ------------------------------------------------------------
    if mapa['Histórico'] and mapa['Fechado por']:
        df_fe = df[df[mapa['Status']].astype(str).str.strip().str.lower() == 'fechado'].copy()
        def substituir_fechado_por(row):
            historico = str(row.get(mapa['Histórico'], ''))
            if 'Usuário efetuando abertura:' in historico and row.get(mapa['Fechado por'], '') == 'NMC Auto':
                try:
                    nome = historico.split("Usuário efetuando abertura:")[1].strip()
                    row[mapa['Fechado por']] = nome
                except:
                    pass
            return row
        df_fe = df_fe.apply(substituir_fechado_por, axis=1)
        df.update(df_fe)

    # ------------------------------------------------------------
    # FILTROS
    # ------------------------------------------------------------
    st.sidebar.header("🔎 Filtros")
    def filtro_multiselect(campo_nome, label):
        if mapa.get(campo_nome) and mapa[campo_nome] in df.columns:
            opcoes = df[mapa[campo_nome]].dropna().unique()
            return st.sidebar.multiselect(label, opcoes)
        else:
            return []

    responsavel_selecionado = filtro_multiselect('Fechado por', "Fechado por")
    categoria_selecionada = filtro_multiselect('Reclamação', "Reclamação")
    criado_selecionado = filtro_multiselect('Criado por', "Criado por")
    diagnostico_selecionado = filtro_multiselect('Diagnóstico', "Diagnóstico")

    # ------------------------------------------------------------
    # FILTRAGEM DE DADOS
    # ------------------------------------------------------------
    df_filtrado = df.copy()

    if relatorio_tipo == "consumer":
        # Chamados fechados: situação = "Resolvido" ou "Completado"
        df_filtrado['Fechado'] = df_filtrado['Situação'].isin(['Resolvido', 'Completado'])
    else:
        df_filtrado['Fechado'] = df_filtrado[mapa['Status']].astype(str).str.strip().str.lower() == 'fechado'

    if responsavel_selecionado and mapa['Fechado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Fechado por']].isin(responsavel_selecionado)]
    if categoria_selecionada and mapa['Reclamação']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Reclamação']].isin(categoria_selecionada)]
    if criado_selecionado and mapa['Criado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Criado por']].isin(criado_selecionado)]
    if diagnostico_selecionado and mapa['Diagnóstico']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Diagnóstico']].fillna("Não informado").isin(diagnostico_selecionado)]

    # ------------------------------------------------------------
    # CÁLCULO DE MÉTRICAS
    # ------------------------------------------------------------
    total_chamados = len(df_filtrado)
    total_fechados = df_filtrado['Fechado'].sum()
    total_abertos = total_chamados - total_fechados
    pct_fechados = round(total_fechados / total_chamados * 100, 1) if total_chamados else 0
    pct_abertos = round(total_abertos / total_chamados * 100, 1) if total_chamados else 0

    # ------------------------------------------------------------
    # EXIBIÇÃO DE MÉTRICAS
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Chamados abertos", total_abertos)
    col2.metric("Chamados fechados", total_fechados)
    col3.metric("% fechados", f"{pct_fechados}%")

    # ------------------------------------------------------------
    # FUNÇÃO DE GRÁFICOS + TABELAS LADO A LADO
    # ------------------------------------------------------------
    def grafico_com_tabela(campo, titulo):
        st.subheader(f"{titulo}")
        col_table, col_graph = st.columns([1.4, 3])
        df_filtrado[campo] = df_filtrado[campo].fillna("Não informado").astype(str)
        tabela = df_filtrado.groupby(campo)['Fechado'].count().rename("Qtd de Chamados").reset_index()
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)

        with col_table:
            st.dataframe(tabela, height=400, use_container_width=True)

        fig = px.bar(tabela, x=campo, y="Qtd de Chamados", text="Qtd de Chamados",
                     color="Qtd de Chamados", color_continuous_scale="Blues", template="plotly_white")
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)
        with col_graph:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # Exemplo de gráficos
    grafico_com_tabela('Criado por', 'Chamados por Criador')
    if relatorio_tipo == "enterprise":
        grafico_com_tabela('Fechado por', 'Chamados fechados por usuário')
    grafico_com_tabela('Reclamação' if relatorio_tipo == "enterprise" else 'Assunto', 'Classificação por Reclamação/Assunto')
    grafico_com_tabela('Diagnóstico' if relatorio_tipo == "enterprise" else 'Causa raiz', 'Classificação por Diagnóstico/Causa raiz')

    # ------------------------------------------------------------
    # EXPORTAÇÃO HTML
    # ------------------------------------------------------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><style>")
        buffer.write("body { font-family:Arial; color:#000; margin:25px; }")
        buffer.write("table { border-collapse:collapse; width:100%; margin:15px 0; }")
        buffer.write("th,td { border:1px solid #ccc; padding:6px; background:#fafafa; }")
        buffer.write("th { background:#e2e2e2; }")
        buffer.write("</style></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button("📥 Baixar Dashboard HTML", to_html_bonito(), "dashboard.html", "text/html")
