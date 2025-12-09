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

.sidebar-multiselect .stMultiSelect {
    max-height: 120px !important;
    overflow-y: auto !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TELA INICIAL ----------------
st.title("📊 Dashboard Chamados")
st.info("Envie um arquivo CSV separado por vírgula para visualizar o dashboard. O sistema detecta automaticamente colunas de datas, usuários, causas e tipos.")

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

if uploaded_file is None:
    st.stop()

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
        if "E65" in texto: return "E65"
        if "63W" in texto or "T19" in texto: return "63W/T19"
        if "J3" in texto: return "J3"
        return "Não informado"
    if "Assunto" in df.columns:
        df["Satélite"] = df["Assunto"].apply(normaliza_satelite)
    else:
        df["Satélite"] = "Não informado"

# ---------------- FLAG DE FECHADO ----------------
if relatorio_tipo == "enterprise":
    if "Status" in df.columns:
        df['Fechado'] = df['Status'].str.lower() == "fechado"
    else:
        df['Fechado'] = False
else:
    col_modificado_por = "Caso modificado pela última vez por" if "Caso modificado pela última vez por" in df.columns else None
    if col_modificado_por:
        df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "")
    else:
        df['Fechado'] = False

# ---------------- FILTROS ----------------
st.sidebar.header("🔎 Filtros")
if relatorio_tipo == "enterprise":
    filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df["Criado por"].unique() if "Criado por" in df.columns else [])
    filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df["Fechado por"].unique() if "Fechado por" in df.columns else [])
    filtro_categoria = st.sidebar.multiselect("Reclamação", df["Reclamação"].unique() if "Reclamação" in df.columns else [])
    filtro_diag = st.sidebar.multiselect("Diagnóstico", df["Diagnóstico"].unique() if "Diagnóstico" in df.columns else [])
else:
    filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df["Criado por"].unique() if "Criado por" in df.columns else [])
    filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df[col_modificado_por].unique() if col_modificado_por else [])
    filtro_diag = st.sidebar.multiselect("Causa Raiz", df["Causa raiz"].unique() if "Causa raiz" in df.columns else [])
    filtro_satelite = st.sidebar.multiselect("Satélite", df["Satélite"].unique() if "Satélite" in df.columns else [])

# ---------------- APLICAR FILTROS ----------------
df_filtrado = df.copy()
if filtro_aberto: df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]
if filtro_fechado:
    col_fechado = "Fechado por" if relatorio_tipo=="enterprise" else col_modificado_por
    df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
if relatorio_tipo=="enterprise" and filtro_categoria: df_filtrado = df_filtrado[df_filtrado["Reclamação"].isin(filtro_categoria)]
if filtro_diag:
    col_diag = "Diagnóstico" if relatorio_tipo=="enterprise" else "Causa raiz"
    df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]
if relatorio_tipo=="consumer" and filtro_satelite: df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]

df_filtrado = df_filtrado.replace("", "Não informado")

# ---------------- MÉTRICAS ----------------
total_chamados = len(df_filtrado)
total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
total_fechados = len(df_filtrado[df_filtrado['Fechado']])

col1, col2, col3 = st.columns(3)

# Tempo médio total (Enterprise)
tempo_medio = 0.0
if relatorio_tipo=="enterprise" and "Data/Hora de abertura" in df_filtrado.columns and "Data/Hora de fechamento" in df_filtrado.columns:
    df_filtrado['Data/Hora de abertura'] = pd.to_datetime(df_filtrado['Data/Hora de abertura'], errors='coerce')
    df_filtrado['Data/Hora de fechamento'] = pd.to_datetime(df_filtrado['Data/Hora de fechamento'], errors='coerce')
    df_filtrado['Dif_min'] = (df_filtrado['Data/Hora de fechamento'] - df_filtrado['Data/Hora de abertura']).dt.total_seconds()/60
    tempo_medio = df_filtrado['Dif_min'].dropna().mean()
col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")

# Maior ofensor (preciso)
coluna_ofensor = "Diagnóstico" if relatorio_tipo=="enterprise" else "Causa raiz"
df_valid_ofensor = df_filtrado[df_filtrado[coluna_ofensor] != "Não informado"]
if not df_valid_ofensor.empty:
    contagem = df_valid_ofensor[coluna_ofensor].value_counts()
    maior_ofensor = contagem.idxmax()
    qtd_maior = contagem.max()
    pct_maior = (qtd_maior / df_valid_ofensor.shape[0] * 100)
else:
    maior_ofensor, pct_maior = "-", 0
col2.metric("📌 Maior ofensor", maior_ofensor)
col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

# Total
st.write(f"### 📑 Total de chamados: **{total_chamados}**")
if relatorio_tipo=="consumer":
    qtd_evento = (df_filtrado["Tipo de registro do caso"]=="Operações - Evento").sum() if "Tipo de registro do caso" in df_filtrado.columns else 0
    qtd_cm = (df_filtrado["Tipo de registro do caso"]=="Operações - CM").sum() if "Tipo de registro do caso" in df_filtrado.columns else 0
    st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
    st.write(f"🟪 Operações - CM: **{qtd_cm}**")
st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100 if total_chamados else 0):.1f}%)")
st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100 if total_chamados else 0):.1f}%)")

# ---------------- FUNÇÕES GRÁFICOS ----------------
def tabela_limpa(df):
    df = df.replace("", "Não informado")
    df = df.dropna(how="all")
    return df

def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
    df_graf = df_graf[df_graf[coluna] != "Não informado"]
    if df_graf.empty: return None, None
    tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
    tabela["%"] = (tabela["Qtd"]/tabela["Qtd"].sum()*100).round(2)
    tabela = tabela_limpa(tabela)
    if tabela.empty: return None, None
    st.subheader(f"{icone} {titulo}")
    col_t, col_g = st.columns([1.4,3])
    tabela_height = min(350, 50 + len(tabela)*35)
    with col_t: st.dataframe(tabela, height=tabela_height)
    fig = px.bar(tabela, x=coluna, y="Qtd", text="Qtd", color="Qtd", color_continuous_scale="Blues", template="plotly_white")
    fig.update_traces(textposition="outside")
    with col_g: st.plotly_chart(fig, use_container_width=True)
    return fig, tabela

# ---------------- GRÁFICOS ----------------
grafico_com_tabela(df_filtrado, "Criado por", "Chamados abertos por usuário", "🔵")
col_fechado = "Fechado por" if relatorio_tipo=="enterprise" else col_modificado_por
df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado] != "Não informado")] if col_fechado else pd.DataFrame()
if not df_fechados.empty:
    grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", "🔴")
if relatorio_tipo=="enterprise":
    if "Reclamação" in df_filtrado.columns: grafico_com_tabela(df_filtrado, "Reclamação", "Reclamação", "📌")
grafico_com_tabela(df_filtrado, coluna_ofensor, coluna_ofensor, "📌")

# ---------------- SATÉLITE ----------------
if relatorio_tipo=="consumer" and "Satélite" in df_filtrado.columns:
    st.subheader("🛰 Satélite")
    tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
    tabela_sat.columns = ["Satélite","Qtd"]
    tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
    tabela_sat = tabela_limpa(tabela_sat)
    col_t, col_g = st.columns([1.4,3])
    tabela_height = min(350, 50 + len(tabela_sat)*35)
    with col_t: st.dataframe(tabela_sat, height=tabela_height)
    fig_sat = px.bar(tabela_sat, x="Satélite", y="Qtd", text="Qtd", color="Qtd", color_continuous_scale="Blues", template="plotly_white")
    fig_sat.update_traces(textposition="outside")
    with col_g: st.plotly_chart(fig_sat, use_container_width=True)

# ---------------- DOWNLOAD HTML COMPLETO ----------------
def gerar_dashboard_html(df_filtrado, relatorio_tipo, titulo_dashboard, 
                         col_criado_por, col_fechado_por, col_modificado_por,
                         col_reclamacao, coluna_ofensor):

    html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>{titulo_dashboard}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f7f7f7; }}
            h2 {{ color: #000080; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #999; padding: 8px; text-align: left; }}
            th {{ background-color: #d9e4f5; }}
        </style>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>{titulo_dashboard}</h1>
    """

    html += f"<h2>📑 Total de chamados: {len(df_filtrado)}</h2>"

    if col_criado_por:
        tabela_aberto = df_filtrado.groupby(col_criado_por).size().reset_index(name="Qtd")
        tabela_aberto["%"] = (tabela_aberto["Qtd"]/tabela_aberto["Qtd"].sum()*100).round(2)
        html += f"<h2>🔵 Chamados abertos por usuário</h2>{tabela_aberto.to_html(index=False)}"

    col_fechado = col_fechado_por if relatorio_tipo=="enterprise" else col_modificado_por
    if col_fechado:
        df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado]!="Não informado")]
        tabela_fechado = df_fechados.groupby(col_fechado).size().reset_index(name="Qtd")
        tabela_fechado["%"] = (tabela_fechado["Qtd"]/tabela_fechado["Qtd"].sum()*100).round(2)
        html += f"<h2>🔴 Chamados fechados por usuário</h2>{tabela_fechado.to_html(index=False)}"

    def fig_to_html(df_graf, coluna, titulo):
        df_graf = df_graf[df_graf[coluna]!="Não informado"]
        if df_graf.empty: return ""
        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela = tabela[tabela["Qtd"]>0]
        fig = px.bar(tabela, x=coluna, y="Qtd", text="Qtd", color="Qtd", color_continuous_scale="Blues", template="plotly_white")
        fig.update_traces(textposition="outside")
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    if col_criado_por: html += "<h2>🔵 Gráfico - Chamados abertos por usuário</h2>" + fig_to_html(df_filtrado, col_criado_por, "Chamados abertos")
    if col_fechado: html += "<h2>🔴 Gráfico - Chamados fechados por usuário</h2>" + fig_to_html(df_fechados, col_fechado, "Chamados fechados")
    if coluna_ofensor: html += f"<h2>📌 Gráfico - {coluna_ofensor}</h2>" + fig_to_html(df_filtrado, coluna_ofensor, coluna_ofensor)

    if relatorio_tipo=="consumer" and "Satélite" in df_filtrado.columns:
        html += "<h2>🛰 Satélite</h2>"
        tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
        tabela_sat.columns = ["Satélite","Qtd"]
        tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
        html += tabela_sat.to_html(index=False)
        fig_sat = px.bar(tabela_sat, x="Satélite", y="Qtd", text="Qtd", color="Qtd", color_continuous_scale="Blues", template="plotly_white")
        fig_sat.update_traces(textposition="outside")
        html += fig_sat.to_html(include_plotlyjs='cdn', full_html=False)

    html += "</body></html>"
    return html

html_dashboard = gerar_dashboard_html(
    df_filtrado, relatorio_tipo, titulo_dashboard,
    "Criado por" if "Criado por" in df_filtrado.columns else None,
    "Fechado por" if "Fechado por" in df_filtrado.columns else None,
    col_modificado_por,
    "Reclamação" if "Reclamação" in df_filtrado.columns else None,
    coluna_ofensor
)

st.download_button(
    "📥 Baixar Dashboard",
    data=html_dashboard,
    file_name="dashboard_completo.html",
    mime="text/html"
)
