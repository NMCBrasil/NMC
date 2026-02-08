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
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select { color: #000 !important; background-color: #f0f0f0 !important; }
input[type="file"] {
    background-color: #d9e4f5 !important;
    color: #000 !important;
    font-weight: bold !important;
    border: 1px solid #000;
    border-radius: 5px;
    padding: 5px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")

else:
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # ---------------- DETECTAR TIPO ----------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura",
        "Criado por", "Causa raiz",
        "Tipo de registro do caso",
        "Caso modificado pela última vez por"
    ]

    if all(col in df.columns for col in colunas_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    else:
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados Enterprise"

    st.title(titulo_dashboard)

    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        palavras_chave = ["E65", "63W/T19", "J3"]

        def normaliza_assunto(valor):
            texto = str(valor).upper()
            for chave in palavras_chave:
                if chave in texto:
                    return chave
            return "Não informado"

        df["Assunto_Normalizado"] = df["Assunto"].apply(normaliza_assunto)

    # ---------------- FECHADOS ----------------
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
        filtro_diag = st.sidebar.multiselect("Causa Raiz", df['Causa raiz'].unique())

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
    df_valid = df_filtrado[df_filtrado[campo_ofensor]!=""]

    if not df_valid.empty:
        cont = df_valid[campo_ofensor].value_counts()
        maior_ofensor = cont.idxmax()
        qtd_ofensor = cont.max()
        pct_ofensor = round(qtd_ofensor/len(df_valid)*100,2)
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-",0,0

    col1,col2,col3 = st.columns(3)
    col1.metric("📑 Total", total_chamados)
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("% do maior", f"{pct_ofensor}% ({qtd_ofensor})")

    # ---------------- FUNÇÃO GRÁFICO ORDENADO ----------------
    def grafico_com_tabela(df_graf, coluna, titulo, icone="📊"):
        df_graf = df_graf[df_graf[coluna]!=""]

        if df_graf.empty:
            return None,None

        tabela = (
            df_graf.groupby(coluna)
            .size()
            .reset_index(name="Qtd de Chamados")
            .sort_values("Qtd de Chamados", ascending=False)
        )

        tabela['% do Total'] = (
            tabela['Qtd de Chamados'] /
            tabela['Qtd de Chamados'].sum()*100
        ).round(2)

        st.subheader(f"{icone} {titulo}")

        col_t, col_g = st.columns([1.4,3])
        with col_t:
            st.dataframe(tabela, height=550)

        fig = px.bar(
            tabela,
            x=coluna,
            y="Qtd de Chamados",
            text="Qtd de Chamados",
            color="Qtd de Chamados",
            color_continuous_scale="Blues",
            template="plotly_white"
        )

        fig.update_traces(textposition="outside")

        with col_g:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # ---------------- GRÁFICOS ----------------
    fig_abertos, tab_abertos = grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos")
    col_fechado = 'Fechado por' if relatorio_tipo=="enterprise" else 'Caso modificado pela última vez por'
    fig_fechados, tab_fechados = grafico_com_tabela(df_filtrado[df_filtrado['Fechado']], col_fechado, "Chamados fechados")

    col_categoria = 'Reclamação' if relatorio_tipo=="enterprise" else 'Assunto'
    fig_categoria, tab_categoria = grafico_com_tabela(df_filtrado, col_categoria, col_categoria)

    col_diag = 'Diagnóstico' if relatorio_tipo=="enterprise" else 'Causa raiz'
    fig_diag, tab_diag = grafico_com_tabela(df_filtrado, col_diag, col_diag)

    # ---------------- GRÁFICO ESPECIAL CONSUMER ----------------
    if relatorio_tipo == "consumer":
        st.subheader("🛰️ Satélite")

        tabela_chaves = (
            df_filtrado["Assunto_Normalizado"]
            .value_counts()
            .reset_index()
            .rename(columns={"index":"Assunto","Assunto_Normalizado":"Qtd"})
            .sort_values("Qtd", ascending=False)
        )

        tabela_chaves["% do Total"] = (
            tabela_chaves["Qtd"]/tabela_chaves["Qtd"].sum()*100
        ).round(2)

        col_t,col_g = st.columns([1.4,3])
        col_t.dataframe(tabela_chaves)

        fig_chaves = px.bar(
            tabela_chaves,
            x="Assunto",
            y="Qtd",
            text="Qtd",
            color="Qtd",
            color_continuous_scale="Blues",
            template="plotly_white"
        )

        col_g.plotly_chart(fig_chaves, use_container_width=True)

    # ---------------- EXPORTAÇÃO HTML ----------------
    def to_html_bonito():
        buffer = io.StringIO()

        buffer.write("<html><head><meta charset='utf-8'>")
        buffer.write("<style>body{font-family:Arial}</style></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")

        for titulo, tabela, fig in [
            ("Chamados abertos", tab_abertos, fig_abertos),
            ("Chamados fechados", tab_fechados, fig_fechados),
            (col_categoria, tab_categoria, fig_categoria),
            (col_diag, tab_diag, fig_diag)
        ]:
            if tabela is not None:
                buffer.write(f"<h2>{titulo}</h2>")
                buffer.write(tabela.to_html(index=False))
                buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))

        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        "📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name="dashboard.html",
        mime="text/html"
    )
