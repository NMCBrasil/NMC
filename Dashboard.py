# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ------------------------------------------------------------
# CONFIGURAÇÃO DO APP
# ------------------------------------------------------------
st.set_page_config(
    page_title="Chamados Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aparência geral
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000000 !important; font-size: 14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000000 !important; background-color: #d9e4f5 !important; border: 1px solid #000000 !important; padding: 6px 12px !important; border-radius: 5px !important; font-weight: bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000000 !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000000 !important; background-color: #f0f0f0 !important; }
div[data-baseweb="select"] > div, div[data-baseweb="select"] input, div[data-baseweb="select"] span { background-color: #f0f0f0 !important; color: #000000 !important; }
input[type="file"]::file-selector-button { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px 10px; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# FUNÇÃO PARA CARREGAMENTO DO CSV
# ------------------------------------------------------------
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    return df

# ------------------------------------------------------------
# SIDEBAR – Upload
# ------------------------------------------------------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# Título inicial antes do upload
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")
else:
    df = carregar_dados(uploaded_file)

    # ------------------------------------------------------------
    # DETECÇÃO AUTOMÁTICA DO TIPO DE RELATÓRIO
    # ------------------------------------------------------------
    colunas_chave_consumer = ["Situação", "Assunto", "Causa raiz", "Caso modificado pela última vez por"]
    if any(col in df.columns for col in colunas_chave_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    else:
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados Enterprise"

    st.title(titulo_dashboard)

    # ------------------------------------------------------------
    # FUNÇÕES PARA CALCULAR CHAMADOS ABERTOS E FECHADOS
    # ------------------------------------------------------------
    def calcular_chamados(df, tipo):
        df_copy = df.copy()
        if tipo == "consumer":
            # Normalizar letras maiúsculas/minúsculas
            df_copy['Situação'] = df_copy['Situação'].astype(str).str.lower()
            df_copy['Fechado'] = df_copy['Situação'].isin(['resolvido', 'completado'])
            df_copy['Aberto'] = ~df_copy['Fechado']
        else:
            df_copy['Status'] = df_copy['Status'].astype(str).str.lower()
            df_copy['Fechado'] = df_copy['Status'] == 'fechado'
            df_copy['Aberto'] = df_copy['Status'] == 'aberto'
        return df_copy

    df = calcular_chamados(df, relatorio_tipo)

    # ------------------------------------------------------------
    # FILTROS
    # ------------------------------------------------------------
    st.sidebar.header("🔎 Filtros")
    filtros = {}

    if relatorio_tipo == "enterprise":
        if 'Fechado por' in df.columns:
            responsaveis = df['Fechado por'].dropna().unique()
            filtros['Fechado por'] = st.sidebar.multiselect("Fechado por", responsaveis)
        if 'Reclamação' in df.columns:
            categorias = df['Reclamação'].dropna().unique()
            filtros['Reclamação'] = st.sidebar.multiselect("Reclamação", categorias)
        if 'Criado por' in df.columns:
            criados = df['Criado por'].dropna().unique()
            filtros['Criado por'] = st.sidebar.multiselect("Criado por", criados)
        if 'Diagnóstico' in df.columns:
            diagnosticos = df['Diagnóstico'].fillna("Não informado").unique()
            filtros['Diagnóstico'] = st.sidebar.multiselect("Diagnóstico", diagnosticos)
    else:  # consumer
        if 'Caso modificado pela última vez por' in df.columns:
            responsaveis = df['Caso modificado pela última vez por'].dropna().unique()
            filtros['Fechado por'] = st.sidebar.multiselect("Fechado por", responsaveis)
        if 'Assunto' in df.columns:
            categorias = df['Assunto'].dropna().unique()
            filtros['Assunto'] = st.sidebar.multiselect("Assunto", categorias)
        if 'Criado por' in df.columns:
            criados = df['Criado por'].dropna().unique()
            filtros['Criado por'] = st.sidebar.multiselect("Criado por", criados)
        if 'Causa raiz' in df.columns:
            diagnosticos = df['Causa raiz'].fillna("Não informado").unique()
            filtros['Causa Raiz'] = st.sidebar.multiselect("Causa Raiz", diagnosticos)

    # Aplicar filtros
    df_filtrado = df.copy()
    for chave, valores in filtros.items():
        if valores:
            df_filtrado = df_filtrado[df_filtrado[chave].isin(valores)]

    # ------------------------------------------------------------
    # MÉTRICAS
    # ------------------------------------------------------------
    total_chamados = len(df_filtrado)
    total_abertos = df_filtrado['Aberto'].sum() if 'Aberto' in df_filtrado.columns else 0
    total_fechados = df_filtrado['Fechado'].sum() if 'Fechado' in df_filtrado.columns else 0
    pct_abertos = (total_abertos / total_chamados * 100) if total_chamados > 0 else 0
    pct_fechados = (total_fechados / total_chamados * 100) if total_chamados > 0 else 0

    if relatorio_tipo == "enterprise" and 'Diagnóstico' in df_filtrado.columns:
        cont_diag = df_filtrado['Diagnóstico'].fillna("Não informado").value_counts()
        maior_ofensor = cont_diag.idxmax()
        qtd_ofensor = cont_diag.max()
        pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)
    elif relatorio_tipo == "consumer" and 'Causa raiz' in df_filtrado.columns:
        cont_diag = df_filtrado['Causa raiz'].fillna("Não informado").value_counts()
        maior_ofensor = cont_diag.idxmax()
        qtd_ofensor = cont_diag.max()
        pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0

    # ------------------------------------------------------------
    # EXIBIÇÃO DE MÉTRICAS
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", "-")  # Calcular se quiser
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({pct_fechados:.1f}%)")

    # ------------------------------------------------------------
    # TABELAS E GRÁFICOS (Exemplo: Chamados abertos por usuário)
    # ------------------------------------------------------------
    def grafico_com_tabela(df_graf, campo, titulo):
        st.subheader(f"📁 {titulo}")
        col_table, col_graph = st.columns([1.4, 3])

        if campo not in df_graf.columns:
            st.warning(f"Coluna '{campo}' não existe neste relatório.")
            return None, None

        df_graf[campo] = df_graf[campo].fillna("Não informado").astype(str)
        tabela = df_graf.groupby(campo)['Aberto'].count().rename("Qtd de Chamados").reset_index()
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)

        # Remover linhas vazias
        tabela = tabela[tabela[campo].str.strip() != ""]

        with col_table:
            st.dataframe(tabela, height=350, use_container_width=True)

        fig = px.bar(
            tabela,
            x=campo,
            y="Qtd de Chamados",
            text="Qtd de Chamados",
            color="Qtd de Chamados",
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)

        with col_graph:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # Chamados abertos por usuário
    if 'Criado por' in df_filtrado.columns:
        fig_abertos, tab_abertos = grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos por usuário")

    # Chamados fechados por usuário
    if relatorio_tipo == "enterprise" and 'Fechado por' in df_filtrado.columns:
        df_fechados = df_filtrado[df_filtrado['Fechado']]
        fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, "Fechado por", "Chamados fechados por usuário")
    elif relatorio_tipo == "consumer" and 'Caso modificado pela última vez por' in df_filtrado.columns:
        df_fechados = df_filtrado[df_filtrado['Fechado']]
        fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, "Caso modificado pela última vez por", "Chamados fechados por usuário")

    # ------------------------------------------------------------
    # DOWNLOAD HTML
    # ------------------------------------------------------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("""
        <html>
        <head>
        <meta charset='utf-8'>
        <style>
            body { background:#f0f4f8; font-family:Arial; color:#000; margin:25px; }
            h1 { text-align:center; }
            h2 { margin-top:40px; }
            table { border-collapse:collapse; width:100%; margin:15px 0; }
            th,td { border:1px solid #ccc; padding:6px; background:#fafafa; }
            th { background:#e2e2e2; }
            .metric { margin:6px 0; font-weight:bold; }
            .linha { display:flex; flex-direction:row; gap:40px; align-items:flex-start; }
            .col-esq { width:45%; }
            .col-dir { width:55%; }
        </style>
        </head>
        <body>
        """)
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<div class='metric'>📑 Total de chamados: {total_chamados}</div>")
        buffer.write(f"<div class='metric'>🔵 Abertos: {total_abertos} ({pct_abertos:.1f}%)</div>")
        buffer.write(f"<div class='metric'>🔴 Fechados: {total_fechados} ({pct_fechados:.1f}%)</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</div>")

        # Gráficos e tabelas
        figs_tabs = [
            (fig_abertos, tab_abertos, "Chamados abertos por usuário"),
            (fig_fechados, tab_fechados, "Chamados fechados por usuário")
        ]
        for fig, tabela, titulo in figs_tabs:
            if fig is not None and tabela is not None:
                buffer.write(f"<h2>{titulo}</h2>")
                buffer.write("<div class='linha'>")
                buffer.write("<div class='col-esq'>")
                buffer.write(tabela.to_html(index=False))
                buffer.write("</div>")
                buffer.write("<div class='col-dir'>")
                buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                buffer.write("</div>")
                buffer.write("</div>")

        buffer.write("<h2>Tabela completa filtrada</h2>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        label="📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name=f"{titulo_dashboard.replace('📊 ', '').replace(' ', '_').lower()}.html",
        mime="text/html"
    )
