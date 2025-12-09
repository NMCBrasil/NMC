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
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select { color: #000 !important; background-color: #f0f0f0 !important; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000 !important; font-weight: bold !important; border: 1px solid #000; border-radius: 5px; padding: 5px; }
.sidebar-multiselect .stMultiSelect { max-height: 120px !important; overflow-y: auto !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- OBSERVAÇÕES INICIAIS ----------------
st.title("📊 Dashboard Chamados")
st.info("Envie um arquivo CSV para visualizar o dashboard. Observe que o sistema detecta automaticamente colunas de datas, usuários, causas e tipos.")

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
consumer_cols = ["Situação", "Assunto", "Criado por", "Causa raiz", "Tipo de registro do caso"]
relatorio_tipo = "consumer" if all(col in df.columns for col in consumer_cols) else "enterprise"
titulo_dashboard = "📊 Chamados Consumer" if relatorio_tipo=="consumer" else "📊 Chamados Enterprise"
st.title(titulo_dashboard)

# ---------------- FUNÇÃO DINÂMICA PARA ENCONTRAR COLUNAS ----------------
def encontrar_coluna_por_chave(df, chaves):
    for chave in chaves:
        for col in df.columns:
            if chave.lower() in col.lower():
                return col
    return None

col_abertura_data = encontrar_coluna_por_chave(df, ["data de abertura", "data/hora de abertura"])
col_abertura_hora = encontrar_coluna_por_chave(df, ["hora de abertura"])
col_fechamento_data = encontrar_coluna_por_chave(df, ["data de fechamento"])
col_fechamento_hora = encontrar_coluna_por_chave(df, ["hora de fechamento"])
col_criado_por = encontrar_coluna_por_chave(df, ["criado por", "usuario abertura"])
col_fechado_por = encontrar_coluna_por_chave(df, ["fechado por", "usuario fechamento"])
col_modificado_por = encontrar_coluna_por_chave(df, ["modificado por", "última modificação"])
col_causa = encontrar_coluna_por_chave(df, ["causa raiz", "diagnóstico", "reclamação"])
col_tipo = encontrar_coluna_por_chave(df, ["tipo de registro", "reclamação"])
col_assunto = encontrar_coluna_por_chave(df, ["assunto"])

# ---------------- COMBINAR DATETIME ----------------
def combinar_data_hora(df, col_data, col_hora):
    if col_data is None: return None
    if col_hora is None: return pd.to_datetime(df[col_data], errors="coerce")
    return pd.to_datetime(df[col_data] + " " + df[col_hora], errors="coerce")

df['dt_abertura'] = combinar_data_hora(df, col_abertura_data, col_abertura_hora)
df['dt_fechamento'] = combinar_data_hora(df, col_fechamento_data, col_fechamento_hora)

# ---------------- FLAG DE FECHADO ----------------
if relatorio_tipo == "enterprise":
    df['Fechado'] = df[col_fechado_por].apply(lambda x: str(x).strip() != "") if col_fechado_por in df.columns else False
else:
    df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "") if col_modificado_por in df.columns else False

# ---------------- FILTROS DINÂMICOS ----------------
st.sidebar.header("🔎 Filtros")
filtros = {}
if col_criado_por: filtros['aberto'] = st.sidebar.multiselect("Chamados abertos por usuário", df[col_criado_por].unique())
if col_fechado_por: filtros['fechado'] = st.sidebar.multiselect("Chamados fechados por usuário", df[col_fechado_por].unique())
if col_tipo: filtros['tipo'] = st.sidebar.multiselect("Tipo / Reclamação", df[col_tipo].unique())
if col_causa: filtros['causa'] = st.sidebar.multiselect("Causa / Diagnóstico", df[col_causa].unique())
if relatorio_tipo == "consumer" and col_assunto:
    df["Satélite"] = df[col_assunto].apply(lambda x: "E65" if "E65" in x.upper() else ("63W/T19" if "63W" in x.upper() or "T19" in x.upper() else ("J3" if "J3" in x.upper() else "Não informado")))
    filtros['satelite'] = st.sidebar.multiselect("Satélite", df["Satélite"].unique())

# ---------------- APLICAR FILTROS ----------------
df_filtrado = df.copy()
if 'aberto' in filtros and filtros['aberto']: df_filtrado = df_filtrado[df_filtrado[col_criado_por].isin(filtros['aberto'])]
if 'fechado' in filtros and filtros['fechado']: df_filtrado = df_filtrado[df_filtrado[col_fechado_por].isin(filtros['fechado'])]
if 'tipo' in filtros and filtros['tipo']: df_filtrado = df_filtrado[df_filtrado[col_tipo].isin(filtros['tipo'])]
if 'causa' in filtros and filtros['causa']: df_filtrado = df_filtrado[df_filtrado[col_causa].isin(filtros['causa'])]
if 'satelite' in filtros and filtros['satelite']: df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtros['satelite'])]

df_filtrado = df_filtrado.replace("", "Não informado")

# ---------------- MÉTRICAS ----------------
total_chamados = len(df_filtrado)
total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
total_fechados = len(df_filtrado[df_filtrado['Fechado']])

col1, col2, col3 = st.columns(3)

# Tempo médio
if df_filtrado['dt_abertura'].notna().any() and df_filtrado['dt_fechamento'].notna().any():
    tempo_medio = (df_filtrado['dt_fechamento'] - df_filtrado['dt_abertura']).dt.total_seconds().mean()/60
else:
    tempo_medio = 0
col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")

# Maior ofensor
if col_causa:
    df_valid_ofensor = df_filtrado[df_filtrado[col_causa] != "Não informado"]
    if not df_valid_ofensor.empty:
        contagem = df_valid_ofensor[col_causa].value_counts()
        maior_ofensor = contagem.idxmax()
        pct_maior = (contagem.max()/len(df_valid_ofensor)*100)
    else:
        maior_ofensor, pct_maior = "-", 0
else:
    maior_ofensor, pct_maior = "-", 0
col2.metric("📌 Maior ofensor", maior_ofensor)
col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

# ---------------- TOTAIS ----------------
st.write(f"### 📑 Total de chamados: **{total_chamados}**")
st.write(" ")
st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100):.1f}%)")
st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100):.1f}%)")

# ---------------- FUNÇÕES DE GRÁFICO ----------------
def tabela_limpa(df): return df.replace("", "Não informado").dropna(how="all")

def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
    df_graf = df_graf[df_graf[coluna] != "Não informado"]
    if df_graf.empty: return None, None
    tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
    tabela = tabela[tabela["Qtd"] > 0]
    tabela["%"] = (tabela["Qtd"]/tabela["Qtd"].sum()*100).round(2)
    tabela = tabela_limpa(tabela)
    if tabela.empty: return None, None
    st.subheader(f"{icone} {titulo}")
    col_t, col_g = st.columns([1.4, 3])
    tabela_height = min(350, 50 + len(tabela)*35)
    with col_t: st.dataframe(tabela, height=tabela_height)
    fig = px.bar(tabela, x=coluna, y="Qtd", text="Qtd", color="Qtd", color_continuous_scale="Blues", template="plotly_white")
    fig.update_traces(textposition="outside")
    with col_g: st.plotly_chart(fig, use_container_width=True)
    return fig, tabela

# ---------------- GRÁFICOS ----------------
if col_criado_por: grafico_com_tabela(df_filtrado, col_criado_por, "Chamados abertos por usuário", "🔵")
if col_fechado_por:
    df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado_por] != "Não informado")]
    grafico_com_tabela(df_fechados, col_fechado_por, "Chamados fechados por usuário", "🔴")
if col_tipo and relatorio_tipo=="enterprise": grafico_com_tabela(df_filtrado, col_tipo, "Reclamação / Tipo", "📌")
if col_causa: grafico_com_tabela(df_filtrado, col_causa, "Causa / Diagnóstico", "📌")
if relatorio_tipo=="consumer" and 'satelite' in filtros:
    st.subheader("🛰 Satélite")
    tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
    tabela_sat.columns = ["Satélite","Qtd"]
    tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
    tabela_sat = tabela_limpa(tabela_sat)
    col_t,col_g = st.columns([1.4,3])
    tabela_height = min(350,50+len(tabela_sat)*35)
    with col_t: st.dataframe(tabela_sat,height=tabela_height)
    fig_sat = px.bar(tabela_sat,x="Satélite",y="Qtd",text="Qtd",color="Qtd",color_continuous_scale="Blues",template="plotly_white")
    fig_sat.update_traces(textposition="outside")
    with col_g: st.plotly_chart(fig_sat,use_container_width=True)

# ---------------- DOWNLOAD HTML ----------------
def to_html_bonito():
    buffer = io.StringIO()
    buffer.write(f"<html><head><meta charset='utf-8'><title>{titulo_dashboard}</title></head><body>")
    buffer.write(df_filtrado.to_html(index=False))
    buffer.write("</body></html>")
    return buffer.getvalue().encode("utf-8")

st.download_button(
    "📥 Baixar Dashboard Completo",
    data=to_html_bonito(),
    file_name="dashboard.html",
    mime="text/html"
)
