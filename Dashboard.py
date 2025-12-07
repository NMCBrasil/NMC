# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ------------------------------------------------------------
# CONFIGURAÇÃO DO APP
# ------------------------------------------------------------
st.set_page_config(
    page_title="Chamados NMC Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aparência geral (tema claro + melhorias visuais)
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

st.title("📊 Chamados NMC Enterprise")

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

if uploaded_file is not None:

    df = carregar_dados(uploaded_file)

    # ------------------------------------------------------------
    # SUBSTITUIÇÃO DO "NMC Auto" PELO USUÁRIO DO HISTÓRICO
    # ------------------------------------------------------------
    if 'Histórico' in df.columns and 'Fechado por' in df.columns:

        df_fe = df[df['Status'].str.strip().str.lower() == 'fechado'].copy()

        def substituir_fechado_por(row):
            historico = str(row.get('Histórico', ''))
            if 'Usuário efetuando abertura:' in historico and row.get('Fechado por', '') == 'NMC Auto':
                try:
                    nome = historico.split("Usuário efetuando abertura:")[1].strip()
                    row['Fechado por'] = nome
                except:
                    pass
            return row

        df_fe = df_fe.apply(substituir_fechado_por, axis=1)
        df.update(df_fe)

    # ------------------------------------------------------------
    # SIDEBAR – Filtros
    # ------------------------------------------------------------
    st.sidebar.header("🔎 Filtros")

    responsaveis = df['Fechado por'].dropna().unique()
    responsavel_selecionado = st.sidebar.multiselect("Fechado por", responsaveis)

    categorias = df['Reclamação'].dropna().unique()
    categoria_selecionada = st.sidebar.multiselect("Reclamação", categorias)

    if 'Criado por' in df.columns:
        criados = df['Criado por'].dropna().unique()
        criado_selecionado = st.sidebar.multiselect("Criado por", criados)
    else:
        criado_selecionado = []

    if 'Diagnóstico' in df.columns:
        diagnosticos = df['Diagnóstico'].fillna("Não informado").unique()
        diagnostico_selecionado = st.sidebar.multiselect("Diagnóstico", diagnosticos)
    else:
        diagnostico_selecionado = []

    # ------------------------------------------------------------
    # APLICAÇÃO DOS FILTROS
    # ------------------------------------------------------------
    df_filtrado = df.copy()

    if responsavel_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Fechado por'].isin(responsavel_selecionado)]

    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Reclamação'].isin(categoria_selecionada)]

    if criado_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(criado_selecionado)]

    if diagnostico_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Diagnóstico'].fillna("Não informado").isin(diagnostico_selecionado)]

    # ------------------------------------------------------------
    # CÁLCULOS DE MÉTRICAS
    # ------------------------------------------------------------
    df_encerrados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].copy()

    if not df_encerrados.empty:
        df_encerrados['DataHoraAbertura'] = pd.to_datetime(
            df_encerrados['Data de abertura'] + ' ' + df_encerrados['Hora de abertura'], errors='coerce'
        )
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(
            df_encerrados['Data de fechamento'] + ' ' + df_encerrados['Hora de fechamento'], errors='coerce'
        )
        df_encerrados['TempoAtendimentoMin'] = (
            (df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura'])
            .dt.total_seconds() / 60
        ).clip(lower=0).dropna()
        tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)
    else:
        tempo_medio = 0.0

    total_chamados = len(df_filtrado)
    total_abertos = df_filtrado[df_filtrado['Status'].str.lower() == 'aberto'].shape[0]
    total_fechados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].shape[0]

    # Maior ofensor
    df_filtrado['Diagnóstico'] = df_filtrado['Diagnóstico'].fillna('Não informado')
    if not df_filtrado.empty:
        cont_diag = df_filtrado['Diagnóstico'].value_counts()
        maior_ofensor = cont_diag.idxmax()
        qtd_ofensor = cont_diag.max()
        pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0

    # ------------------------------------------------------------
    # MÉTRICAS NA TELA
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(
        f"### 📑 Total de chamados: **{total_chamados}**   🔵 Abertos: **{total_abertos}**   🔴 Fechados: **{total_fechados}**"
    )

    # ------------------------------------------------------------
    # FUNÇÃO DOS GRÁFICOS + TABELA
    # ------------------------------------------------------------
    def grafico_com_tabela(campo, titulo):

        st.subheader(f"📁 {titulo}")

        col_table, col_graph = st.columns([1.4, 3])

        df_filtrado[campo] = df_filtrado[campo].fillna("Não informado").astype(str)

        tabela = (
            df_filtrado.groupby(campo)['Id']
            .count()
            .rename("Qtd de Chamados")
            .reset_index()
        )

        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)

        with col_table:
            st.dataframe(
                tabela,
                height=550 if campo in ["Reclamação", "Diagnóstico"] else 350,
                use_container_width=True
            )

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

    # ------------------------------------------------------------
    # GRÁFICOS PRINCIPAIS (AGORA COM ESPAÇAMENTO ENTRE SEÇÕES)
    # ------------------------------------------------------------
    fig_abertos_por, tab_abertos = grafico_com_tabela("Criado por", "Chamados abertos por")

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    fig_reclamacao, tab_reclamacao = grafico_com_tabela("Reclamação", "Classificação por Reclamação")

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    fig_diagnostico, tab_diagnostico = grafico_com_tabela("Diagnóstico", "Classificação por Diagnóstico")

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    fig_fechado_por, tab_fechado = grafico_com_tabela("Fechado por", "Chamados fechados por")

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------
    # EXPORTAÇÃO HTML (Tabelas + Gráficos)
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
        h2 { margin-top:30px; }
        table { border-collapse:collapse; width:100%; margin:15px 0; }
        th,td { border:1px solid #ccc; padding:6px; background:#fafafa; }
        th { background:#e2e2e2; }
        .metric { margin:6px 0; font-weight:bold; }
        </style>
        </head>
        <body>
        """)

        buffer.write("<h1>Chamados NMC Enterprise</h1>")
        buffer.write(f"<div class='metric'>⏱ Tempo médio total (min): {tempo_medio}</div>")
        buffer.write(f"<div class='metric'>📑 Total de chamados: {total_chamados} — Abertos: {total_abertos} — Fechados: {total_fechados}</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</div>")

        figs = [fig_abertos_por, fig_reclamacao, fig_diagnostico, fig_fechado_por]
        tabs = [tab_abertos, tab_reclamacao, tab_diagnostico, tab_fechado]
        nomes = ["Abertos por", "Reclamação", "Diagnóstico", "Fechado por"]

        for titulo, fig, tabela in zip(nomes, figs, tabs):
            buffer.write(f"<h2>{titulo}</h2>")
            buffer.write(tabela.to_html(index=False))
            buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))

        buffer.write("<h2>Tabela completa filtrada</h2>")
        buffer.write(df_filtrado.to_html(index=False))

        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        label="📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name="dashboard_nmc.html",
        mime="text/html"
    )

else:
    st.info("Envie um arquivo CSV para visualizar o dashboard.")
