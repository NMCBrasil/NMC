import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(
    page_title="Dashboard Chamados",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- ESTILO ----------------
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000 !important; font-size: 14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000 !important; background-color: #d9e4f5 !important; border: 1px solid #000 !important; padding: 6px 12px !important; border-radius: 5px !important; font-weight: bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000 !important; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000 !important; font-weight: bold !important; border: 1px solid #000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")
else:
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # ---------------- DETECTAR TIPO DE RELATÓRIO ----------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura", "Criado por",
        "Causa raiz", "Tipo de registro do caso", "Caso modificado pela última vez por"
    ]
    if all(col in df.columns for col in colunas_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    else:
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados NMC Enterprise"
    st.title(titulo_dashboard)

    # ---------------- NORMALIZAÇÃO ----------------
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")

    # ---------------- FLAG CHAMADOS FECHADOS ----------------
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df['Status'].str.lower() == "fechado"
    else:
        df['Fechado'] = df['Situação'].str.lower() == "resolvido ou completado"

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    if relatorio_tipo == "enterprise":
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df['Criado por'].unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df['Fechado por'].unique())
        filtro_categoria = st.sidebar.multiselect("Reclamação", df['Reclamação'].unique())
        filtro_diag = st.sidebar.multiselect("Diagnóstico", df['Diagnóstico'].unique())
    else:
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df['Criado por'].unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df['Caso modificado pela última vez por'].unique())
        filtro_categoria = st.sidebar.multiselect("Assunto", df['Assunto'].unique())
        filtro_diag = st.sidebar.multiselect("Causa raiz", df['Causa raiz'].unique())

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()
    if filtro_aberto:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]
    if filtro_fechado:
        col_fechado = 'Fechado por' if relatorio_tipo=="enterprise" else 'Caso modificado pela última vez por'
        df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
    if filtro_categoria:
        col_categoria = 'Reclamação' if relatorio_tipo=="enterprise" else 'Assunto'
        df_filtrado = df_filtrado[df_filtrado[col_categoria].isin(filtro_categoria)]
    if filtro_diag:
        col_diag = 'Diagnóstico' if relatorio_tipo=="enterprise" else 'Causa raiz'
        df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = df_filtrado['Fechado'].sum()
    pct_abertos = (total_abertos/total_chamados*100) if total_chamados else 0
    pct_fechados = (total_fechados/total_chamados*100) if total_chamados else 0

    campo_ofensor = 'Causa raiz' if relatorio_tipo=="consumer" else 'Diagnóstico'
    if campo_ofensor in df_filtrado.columns:
        cont_ofensor = df_filtrado[campo_ofensor].value_counts()
        if not cont_ofensor.empty:
            maior_ofensor = cont_ofensor.idxmax()
            qtd_ofensor = cont_ofensor.max()
            pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)
        else:
            maior_ofensor, qtd_ofensor, pct_ofensor = "-",0,0.0
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-",0,0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", "-")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({pct_fechados:.1f}%)")

    # ---------------- FUNÇÃO GRÁFICO ----------------
    def grafico_com_tabela(df_graf, coluna, titulo):
        df_graf = df_graf[df_graf[coluna].notna() & (df_graf[coluna]!="")]
        if df_graf.empty:
            st.info(f"Nenhum dado para {titulo}")
            return None,None
        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd de Chamados")
        tabela['% do Total'] = (tabela['Qtd de Chamados']/tabela['Qtd de Chamados'].sum()*100).round(2)
        st.subheader(titulo)
        col_table, col_graph = st.columns([1.4,3])
        with col_table:
            st.dataframe(tabela, height=550)
        fig = px.bar(tabela, x=coluna, y="Qtd de Chamados", text="Qtd de Chamados",
                     color="Qtd de Chamados", color_continuous_scale="Blues", template="plotly_white")
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)
        with col_graph:
            st.plotly_chart(fig, use_container_width=True)
        return fig, tabela

    # ---------------- GRÁFICOS ----------------
    # Chamados abertos por usuário
    fig_abertos, tab_abertos = grafico_com_tabela(df_filtrado[~df_filtrado['Fechado']], "Criado por", "Chamados abertos por usuário")
    # Chamados fechados por usuário
    col_fechado = 'Fechado por' if relatorio_tipo=="enterprise" else 'Caso modificado pela última vez por'
    df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado]!="")]
    fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário")
    # Categoria / Assunto
    col_categoria = 'Reclamação' if relatorio_tipo=="enterprise" else 'Assunto'
    fig_categoria, tab_categoria = grafico_com_tabela(df_filtrado, col_categoria, "Classificação por Categoria")
    # Diagnóstico / Causa raiz
    col_diag = 'Diagnóstico' if relatorio_tipo=="enterprise" else 'Causa raiz'
    fig_diag, tab_diag = grafico_com_tabela(df_filtrado, col_diag, "Classificação por Diagnóstico / Causa raiz")

    # ---------------- DOWNLOAD ----------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write(f"<html><head><meta charset='utf-8'><title>{titulo_dashboard}</title></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<p>Total de chamados: {total_chamados}</p>")
        buffer.write(f"<p>Chamados abertos: {total_abertos}</p>")
        buffer.write(f"<p>Chamados fechados: {total_fechados}</p>")
        buffer.write(f"<p>Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</p>")
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button("📥 Baixar Dashboard Completo", data=to_html_bonito(), file_name="dashboard.html", mime="text/html")
