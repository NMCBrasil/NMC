import streamlit as st
import pandas as pd
import plotly.express as px
import io
from plotly.subplots import make_subplots
import plotly.graph_objects as go

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

div.stDataFrame div.row_widget.stDataFrame {
    background-color: #f7f7f7 !important;
    color: #000 !important;
    font-size: 14px;
}

.plotly-graph-div { background-color: #f7f7f7 !important; }

.stDownloadButton button {
    color: #000 !important;
    background-color: #d9e4f5 !important;
    border: 1px solid #000 !important;
    padding: 6px 12px !important;
    border-radius: 5px !important;
    font-weight: bold !important;
}

section[data-testid="stSidebar"] {
    background-color: #e8e8e8 !important;
    color: #000 !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select {
    color: #000 !important;
    background-color: #f0f0f0 !important;
}

input[type="file"] {
    background-color: #d9e4f5 !important;
    color: #000 !important;
    font-weight: bold !important;
    border: 1px solid #000;
    border-radius: 5px;
    padding: 5px;
}

/* ------ MELHORIA NO FILTRO DE SATÉLITE ------- */
.sidebar-multiselect .stMultiSelect {
    max-height: 120px !important;
    overflow-y: auto !important;
}

.tela-inicial {
    background-color: #d9e4f5;
    padding: 20px;
    border-radius: 10px;
    color: #000;
    font-size: 18px;
    text-align: center;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.markdown('<div class="tela-inicial">Envie um arquivo CSV separado por vírgula para visualizar o dashboard. O sistema detecta automaticamente colunas de datas, usuários, causas e tipos.</div>', unsafe_allow_html=True)
else:

    # ---------------- LEITURA DO CSV ----------------
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    df = df.applymap(lambda x: str(x).strip())

    # ---------------- DETECTAR TIPO ----------------
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

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        def normaliza_satelite(valor):
            texto = str(valor).upper()
            if "E65" in texto:
                return "E65"
            if "63W" in texto or "T19" in texto:
                return "63W/T19"
            if "J3" in texto:
                return "J3"
            return "Não informado"

        df["Satélite"] = df["Assunto"].apply(normaliza_satelite)

    # ---------------- FLAG DE FECHADO ----------------
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df.get('Status', '').str.lower() == "fechado"
    else:
        col_modificado_por = "Caso modificado pela última vez por" if "Caso modificado pela última vez por" in df.columns else df.columns[-1]
        df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "")

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    if relatorio_tipo == "enterprise":
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df.get('Criado por', pd.Series()).unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df.get('Fechado por', pd.Series()).unique())
        filtro_categoria = st.sidebar.multiselect("Reclamação", df.get('Reclamação', pd.Series()).unique())
        filtro_diag = st.sidebar.multiselect("Diagnóstico", df.get('Diagnóstico', pd.Series()).unique())
    else:
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df.get('Criado por', pd.Series()).unique())
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df.get('Caso modificado pela última vez por', pd.Series()).unique())
        filtro_diag = st.sidebar.multiselect("Causa Raiz", df.get('Causa raiz', pd.Series()).unique())
        filtro_satelite = st.sidebar.multiselect("Satélite", df["Satélite"].unique())

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()

    if filtro_aberto:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]

    if filtro_fechado:
        col_fechado = "Fechado por" if relatorio_tipo == "enterprise" else "Caso modificado pela última vez por"
        df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]

    if relatorio_tipo == "enterprise" and filtro_categoria:
        df_filtrado = df_filtrado[df_filtrado["Reclamação"].isin(filtro_categoria)]

    if filtro_diag:
        col_diag = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
        df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]

    if relatorio_tipo == "consumer" and filtro_satelite:
        df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]

    # ---------------- LIMPEZA ----------------
    df_filtrado = df_filtrado.replace("", "Não informado")

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = len(df_filtrado[df_filtrado['Fechado']])

    col1, col2, col3 = st.columns(3)
    # ---------------- TEMPO MÉDIO ----------------
    if relatorio_tipo == "enterprise":
        # Detecta colunas de data e hora
        col_data_ab = next((c for c in df_filtrado.columns if "Data" in c and "abertura" in c.lower()), None)
        col_hora_ab = next((c for c in df_filtrado.columns if "Hora" in c and "abertura" in c.lower()), None)
        col_data_fc = next((c for c in df_filtrado.columns if "Data" in c and "fechamento" in c.lower()), None)
        col_hora_fc = next((c for c in df_filtrado.columns if "Hora" in c and "fechamento" in c.lower()), None)

        if all([col_data_ab, col_hora_ab, col_data_fc, col_hora_fc]):
            dt_inicio = pd.to_datetime(df_filtrado[col_data_ab] + " " + df_filtrado[col_hora_ab], errors='coerce')
            dt_fim = pd.to_datetime(df_filtrado[col_data_fc] + " " + df_filtrado[col_hora_fc], errors='coerce')
            tempo_min = (dt_fim - dt_inicio).dt.total_seconds().div(60)
            tempo_medio = round(tempo_min.mean(), 2)
        else:
            tempo_medio = 0
    else:
        tempo_medio = 0
    col1.metric("⏱ Tempo médio total (min)", tempo_medio)

    # ---------------- MAIOR OFENSOR ----------------
    coluna_ofensor = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
    df_valid_ofensor = df_filtrado[df_filtrado[coluna_ofensor] != "Não informado"]
    if not df_valid_ofensor.empty:
        contagem = df_valid_ofensor[coluna_ofensor].value_counts()
        maior_ofensor = contagem.index[0]
        qtd_maior = contagem.iloc[0]
        pct_maior = (qtd_maior / df_filtrado.shape[0] * 100)
    else:
        maior_ofensor, pct_maior = "-", 0
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(" ")

    if relatorio_tipo == "consumer":
        qtd_evento = (df_filtrado["Tipo de registro do caso"] == "Operações - Evento").sum()
        qtd_cm = (df_filtrado["Tipo de registro do caso"] == "Operações - CM").sum()
        st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
        st.write(f"🟪 Operações - CM: **{qtd_cm}**")

    st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100):.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100):.1f}%)")

    # ---------------- FUNÇÕES ----------------
    def tabela_limpa(df):
        df = df.replace("", "Não informado")
        df = df.dropna(how="all")
        return df

    def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
        df_graf = df_graf[df_graf[coluna] != "Não informado"]
        if df_graf.empty:
            return None, None
        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela = tabela[tabela["Qtd"] > 0]
        tabela["%"] = (tabela["Qtd"] / tabela["Qtd"].sum() * 100).round(2)
        tabela = tabela_limpa(tabela)
        if tabela.empty:
            return None, None
        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4,3])
        tabela_height = min(350, 50 + len(tabela)*35)
        with col_t:
            st.dataframe(tabela, height=tabela_height)
        fig = px.bar(
            tabela, x=coluna, y="Qtd", text="Qtd",
            color="Qtd", color_continuous_scale="Blues", template="plotly_white"
        )
        fig.update_traces(textposition="outside")
        with col_g:
            st.plotly_chart(fig, use_container_width=True)
        return fig, tabela

    # ---------------- GRÁFICOS ----------------
    figs_tabelas = []

    figs_tabelas.append(grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos por usuário", "🔵"))
    col_fechado = "Fechado por" if relatorio_tipo == "enterprise" else "Caso modificado pela última vez por"
    df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado] != "Não informado")]
    figs_tabelas.append(grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", "🔴"))

    if relatorio_tipo == "enterprise":
        figs_tabelas.append(grafico_com_tabela(df_filtrado, "Reclamação", "Reclamação", "📌"))

    col_diag = "Diagnóstico" if relatorio_tipo == "enterprise" else "Causa raiz"
    figs_tabelas.append(grafico_com_tabela(df_filtrado, col_diag, col_diag, "📌"))

    if relatorio_tipo == "consumer":
        st.subheader("🛰 Satélite")
        tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
        tabela_sat.columns = ["Satélite","Qtd"]
        tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
        tabela_sat = tabela_limpa(tabela_sat)
        col_t, col_g = st.columns([1.4,3])
        tabela_height = min(350, 50 + len(tabela_sat)*35)
        with col_t:
            st.dataframe(tabela_sat, height=tabela_height)
        fig_sat = px.bar(
            tabela_sat, x="Satélite", y="Qtd", text="Qtd",
            color="Qtd", color_continuous_scale="Blues", template="plotly_white"
        )
        fig_sat.update_traces(textposition="outside")
        with col_g:
            st.plotly_chart(fig_sat, use_container_width=True)
        figs_tabelas.append((fig_sat, tabela_sat))

    # ---------------- DOWNLOAD HTML ----------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write(f"<html><head><meta charset='utf-8'><title>{titulo_dashboard}</title></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<p>Tempo médio: {tempo_medio} min</p>")
        for fig, tabela in figs_tabelas:
            if fig is not None and tabela is not None:
                buffer.write(tabela.to_html(index=False))
                buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        "📥 Baixar Dashboard",
        data=to_html_bonito(),
        file_name="dashboard.html",
        mime="text/html"
    )
