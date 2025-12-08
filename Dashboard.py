# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ------------------------------------------------------------
# CONFIGURAÇÃO DO APP
# ------------------------------------------------------------
st.set_page_config(
    page_title="Chamados Enterprise/Consumer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000 !important; font-size:14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000 !important; background-color: #d9e4f5 !important; border: 1px solid #000 !important; padding:6px 12px !important; border-radius:5px !important; font-weight:bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000 !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000 !important; background-color:#f0f0f0 !important; }
div[data-baseweb="select"] > div, div[data-baseweb="select"] input, div[data-baseweb="select"] span { background-color:#f0f0f0 !important; color:#000 !important; }
input[type="file"]::file-selector-button { background-color:#d9e4f5 !important; color:#000 !important; font-weight:bold !important; border:1px solid #000; border-radius:5px; padding:5px 10px; }
input[type="file"] { background-color:#d9e4f5 !important; color:#000 !important; font-weight:bold !important; border:1px solid #000; border-radius:5px; padding:5px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# TÍTULO INICIAL
# ------------------------------------------------------------
st.title("📊 Dashboard Chamados")
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ------------------------------------------------------------
# FUNÇÃO PARA CARREGAR CSV
# ------------------------------------------------------------
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    return df

# ------------------------------------------------------------
# ANTES DO UPLOAD
# ------------------------------------------------------------
if uploaded_file is None:
    st.info("Envie um arquivo CSV para visualizar o dashboard.")
else:
    df = carregar_dados(uploaded_file)

    # ------------------------------------------------------------
    # DETECÇÃO AUTOMÁTICA
    # ------------------------------------------------------------
    colunas_consumer = ["Situação", "Assunto", "Causa raiz", "Caso modificado pela última vez por"]
    colunas_enterprise = ["Status", "Reclamação", "Diagnóstico", "Fechado por"]

    if any(col in df.columns for col in colunas_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    elif any(col in df.columns for col in colunas_enterprise):
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados Enterprise"
    else:
        relatorio_tipo = "desconhecido"
        titulo_dashboard = "📊 Chamados (Tipo não identificado)"

    st.title(titulo_dashboard)

    # ------------------------------------------------------------
    # SEPARAÇÃO DE ABERTOS E FECHADOS
    # ------------------------------------------------------------
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df['Status'].astype(str).str.lower() == 'fechado'
        df_abertos = df[~df['Fechado']].copy()
        df_fechados = df[df['Fechado']].copy()
        campo_aberto = "Criado por"
        campo_fechado = "Fechado por"
        campo_categoria = "Reclamação"
        campo_diagnostico = "Diagnóstico"
    else:  # consumer
        df_abertos = df[df['Situação'].astype(str).str.lower() == 'aberto'].copy()
        df_fechados = df[
            df['Situação'].astype(str).str.lower().isin(['resolvido', 'completado']) &
            df['Caso modificado pela última vez por'].notna()
        ].copy()
        campo_aberto = "Criado por"
        campo_fechado = "Caso modificado pela última vez por"
        campo_categoria = "Assunto"
        campo_diagnostico = "Causa raiz"

    # ------------------------------------------------------------
    # MÉTRICAS
    # ------------------------------------------------------------
    total_chamados = len(df)
    total_abertos = len(df_abertos)
    total_fechados = len(df_fechados)
    pct_abertos = (total_abertos / total_chamados * 100) if total_chamados > 0 else 0
    pct_fechados = (total_fechados / total_chamados * 100) if total_chamados > 0 else 0

    # Tempo médio apenas enterprise
    if relatorio_tipo == "enterprise" and not df_fechados.empty:
        df_fechados['DataHoraAbertura'] = pd.to_datetime(
            df_fechados['Data de abertura'] + ' ' + df_fechados['Hora de abertura'], errors='coerce'
        )
        df_fechados['DataHoraFechamento'] = pd.to_datetime(
            df_fechados['Data de fechamento'] + ' ' + df_fechados['Hora de fechamento'], errors='coerce'
        )
        df_fechados['TempoAtendimentoMin'] = (
            (df_fechados['DataHoraFechamento'] - df_fechados['DataHoraAbertura']).dt.total_seconds() / 60
        ).clip(lower=0).dropna()
        tempo_medio = df_fechados['TempoAtendimentoMin'].mean().round(2)
    else:
        tempo_medio = 0.0

    # Maior ofensor
    if campo_diagnostico in df.columns:
        cont_diag = df[campo_diagnostico].dropna()
        if not cont_diag.empty:
            maior_ofensor = cont_diag.value_counts().idxmax()
            qtd_ofensor = cont_diag.value_counts().max()
            pct_ofensor = round(qtd_ofensor / len(cont_diag) * 100, 2)
        else:
            maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0

    # ------------------------------------------------------------
    # EXIBIÇÃO DE MÉTRICAS
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({pct_fechados:.1f}%)")

    # ------------------------------------------------------------
    # FUNÇÃO GRÁFICO + TABELA
    # ------------------------------------------------------------
    def grafico_com_tabela(df_graf, campo, titulo):
        st.subheader(f"📁 {titulo}")
        col_table, col_graph = st.columns([1.4, 3])
        df_graf[campo] = df_graf[campo].fillna("Não informado").astype(str)
        tabela = (
            df_graf.groupby(campo)['Situação']
            .count()
            .rename("Qtd de Chamados")
            .reset_index()
        )
        tabela = tabela[tabela[campo] != "Não informado"]  # remove linhas vazias
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)
        with col_table:
            st.dataframe(tabela, height=450 if relatorio_tipo=="enterprise" else 350, use_container_width=True)
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
    # GRÁFICOS PRINCIPAIS
    # ------------------------------------------------------------
    fig_abertos, tab_abertos = grafico_com_tabela(df_abertos, campo_aberto, f"Chamados abertos por usuário")
    fig_categoria, tab_categoria = grafico_com_tabela(df, campo_categoria, f"Classificação por {campo_categoria}")
    fig_diagnostico, tab_diagnostico = grafico_com_tabela(df, campo_diagnostico, f"Classificação por {campo_diagnostico}")

    if not df_fechados.empty:
        fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, campo_fechado, "Chamados fechados por usuário")

    # ------------------------------------------------------------
    # DOWNLOAD HTML
    # ------------------------------------------------------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("""
        <html><head><meta charset='utf-8'>
        <style>
        body { background:#f0f4f8; font-family:Arial; color:#000; margin:25px; }
        h1 { text-align:center; } h2 { margin-top:40px; }
        table { border-collapse:collapse; width:100%; margin:15px 0; }
        th,td { border:1px solid #ccc; padding:6px; background:#fafafa; }
        th { background:#e2e2e2; } .metric { margin:6px 0; font-weight:bold; }
        .linha { display:flex; flex-direction:row; gap:40px; align-items:flex-start; }
        .col-esq { width:45%; } .col-dir { width:55%; }
        </style></head><body>
        """)
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<div class='metric'>⏱ Tempo médio total (min): {tempo_medio}</div>")
        buffer.write(f"<div class='metric'>📑 Total de chamados: {total_chamados}</div>")
        buffer.write(f"<div class='metric'>🔵 Abertos: {total_abertos} ({pct_abertos:.1f}%)</div>")
        buffer.write(f"<div class='metric'>🔴 Fechados: {total_fechados} ({pct_fechados:.1f}%)</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</div>")

        nomes = [
            f"Chamados abertos por usuário",
            f"Classificação por {campo_categoria}",
            f"Classificação por {campo_diagnostico}"
        ]
        figs = [fig_abertos, fig_categoria, fig_diagnostico]
        tabs = [tab_abertos, tab_categoria, tab_diagnostico]

        if not df_fechados.empty:
            nomes.append("Chamados fechados por usuário")
            figs.append(fig_fechados)
            tabs.append(tab_fechados)

        for titulo, fig, tabela in zip(nomes, figs, tabs):
            buffer.write(f"<h2>{titulo}</h2><div class='linha'>")
            buffer.write("<div class='col-esq'>"); buffer.write(tabela.to_html(index=False)); buffer.write("</div>")
            buffer.write("<div class='col-dir'>"); buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn')); buffer.write("</div>")
            buffer.write("</div>")

        buffer.write("<h2>Tabela completa filtrada</h2>")
        buffer.write(df.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        label="📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name=f"{titulo_dashboard.replace('📊 ','').replace(' ','_')}.html",
        mime="text/html"
    )
