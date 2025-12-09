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
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000 !important; background-color: #f0f0f0 !important; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000 !important; font-weight: bold !important; border: 1px solid #000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.markdown("""
    <div style="
        background-color:#d9e4f5;
        padding:20px;
        border-radius:12px;
        margin-bottom:20px;
        font-size:15px;
        line-height:1.5;
        color:#000;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    ">
        <b>📌 Observação:</b><br>
        Para que o dashboard funcione corretamente, seu relatório precisa conter as seguintes colunas:<br><br>
        <b>Enterprise:</b> Status, Criado por, Fechado por, Reclamação, Diagnóstico, Data de abertura, Hora de abertura, Data de fechamento, Hora de fechamento, Id<br>
        <b>Consumer:</b> Situação, Criado por, Caso modificado pela última vez por, Assunto, Causa raiz, Tipo de registro do caso, Data/Hora de abertura
    </div>
    """, unsafe_allow_html=True)
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
        titulo_dashboard = "📊 Chamados Enterprise"
    st.title(titulo_dashboard)

    df = df.applymap(lambda x: str(x).strip())

    # ---------------- NORMALIZAÇÃO ESPECIAL CONSUMER ----------------
    if relatorio_tipo == "consumer":
        palavras_chave = ["E65", "63W/T19", "J3"]

        def normaliza_assunto(valor):
            texto = str(valor).upper()
            for chave in palavras_chave:
                if chave in texto:
                    return chave
            return valor

        df["Assunto_Normalizado"] = df["Assunto"].apply(normaliza_assunto)

    # ---------------- FLAG DE FECHAMENTO ----------------
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

    # ---------------- MÉTRICAS VISUAIS ----------------
    col1, col2, col3 = st.columns(3)

    col1.metric("⏱ Tempo médio total (min)", "0.00")

    # CALCULAR MAIOR OFENSOR
    coluna_ofensor = "Reclamação" if relatorio_tipo == "enterprise" else "Assunto"

    if not df_filtrado.empty:
        contagem = df_filtrado[coluna_ofensor].value_counts()
        maior_ofensor = contagem.index[0]
        qtd_maior = contagem.iloc[0]
        pct_maior = (qtd_maior / total_chamados * 100)
    else:
        maior_ofensor = "-"
        pct_maior = 0

    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.1f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")

    # ---------------- EXTRA CONSUMER ----------------
    if relatorio_tipo == "consumer":
        qtd_evento = (df_filtrado["Tipo de registro do caso"] == "Operações - Evento").sum()
        qtd_cm = (df_filtrado["Tipo de registro do caso"] == "Operações - CM").sum()

        st.write(" ")
        st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
        st.write(f"🟪 Operações - CM: **{qtd_cm}**")

    # ---------------- ABERTOS / FECHADOS ----------------
    st.write(f"🔵 Chamados abertos: {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({pct_fechados:.1f}%)")

    # ---------------- FUNÇÃO DE GRÁFICOS ----------------
    def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
        df_graf = df_graf[df_graf[coluna] != ""]
        if df_graf.empty:
            st.info(f"Nenhum dado para {titulo}")
            return None, None

        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela["%"] = (tabela["Qtd"] / tabela["Qtd"].sum() * 100).round(2)

        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4, 3])

        with col_t:
            st.dataframe(tabela, height=550)

        fig = px.bar(
            tabela,
            x=coluna, y="Qtd", text="Qtd",
            color="Qtd", color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)

        with col_g:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # ---------------- GRÁFICOS GERAIS ----------------
    fig_abertos, tab_abertos = grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos por usuário", icone="🔵")

    col_fechado = 'Fechado por' if relatorio_tipo=="enterprise" else 'Caso modificado pela última vez por'
    df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado]!="")]
    fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", icone="🔴")

    col_categoria = 'Reclamação' if relatorio_tipo=="enterprise" else 'Assunto'
    fig_categoria, tab_categoria = grafico_com_tabela(df_filtrado[df_filtrado[col_categoria]!=""], col_categoria, col_categoria, icone="📌")

    col_diag = 'Diagnóstico' if relatorio_tipo=="enterprise" else 'Causa raiz'
    fig_diag, tab_diag = grafico_com_tabela(df_filtrado[df_filtrado[col_diag]!=""], col_diag, col_diag, icone="📌")

    # ---------------- GRÁFICO EXCLUSIVO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        st.subheader("🔧 Ocorrências de E65 / 63W/T19 / J3")

        df_chaves = df_filtrado.copy()
        df_chaves["Assunto_Normalizado"] = df_chaves["Assunto"].apply(normaliza_assunto)

        tabela_chaves = df_chaves["Assunto_Normalizado"].value_counts().reset_index()
        tabela_chaves.columns = ["Assunto", "Qtd"]
        tabela_chaves["%"] = (tabela_chaves["Qtd"] / tabela_chaves["Qtd"].sum() * 100).round(2)

        col_t, col_g = st.columns([1.4, 3])
        with col_t:
            st.dataframe(tabela_chaves, height=300)

        fig_chaves = px.bar(
            tabela_chaves,
            x="Assunto",
            y="Qtd",
            text="Qtd",
            color="Qtd",
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig_chaves.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)

        with col_g:
            st.plotly_chart(fig_chaves, use_container_width=True)

    # ---------------- DOWNLOAD HTML ----------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><title>{}</title>".format(titulo_dashboard))
        buffer.write("</head><body>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button("📥 Baixar Dashboard Completo", data=to_html_bonito(), file_name="dashboard.html", mime="text/html")
