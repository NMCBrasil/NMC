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
.inicio-box {background-color: #d9e4f5; padding: 20px; border-radius: 10px; color: #000; font-size: 18px; font-weight: bold; text-align: center;}
</style>
""", unsafe_allow_html=True)

# ---------------- TELA INICIAL ----------------
if not st.session_state.get("arquivo_carregado", False):
    st.title("📊 Dashboard Chamados")
    st.markdown('<div class="inicio-box">Envie um arquivo CSV separado por vírgula para visualizar o dashboard.<br>O sistema detecta automaticamente colunas de datas, usuários, causas e tipos.</div>', unsafe_allow_html=True)

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

if uploaded_file:
    st.session_state["arquivo_carregado"] = True
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    df = df.applymap(lambda x: str(x).strip())

    # ---------------- DETECTAR TIPO ----------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura", "Criado por",
        "Causa raiz", "Tipo de registro do caso", "Caso modificado pela última vez por"
    ]

    relatorio_tipo = "consumer" if all(col in df.columns for col in colunas_consumer) else "enterprise"
    titulo_dashboard = "📊 Chamados Consumer" if relatorio_tipo == "consumer" else "📊 Chamados Enterprise"
    st.title(titulo_dashboard)

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        def normaliza_satelite(valor):
            texto = str(valor).upper()
            if "E65" in texto: return "E65"
            if "63W" in texto or "T19" in texto: return "63W/T19"
            if "J3" in texto: return "J3"
            return "Não informado"
        df["Satélite"] = df["Assunto"].apply(normaliza_satelite)

    # ---------------- FLAG DE FECHADO ----------------
    col_modificado_por = next((c for c in df.columns if "Caso modificado" in c), None)
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df.get('Status', '').str.lower() == "fechado"
    else:
        df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "") if col_modificado_por else False

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df.get('Criado por', '').unique())
    col_fechado = "Fechado por" if relatorio_tipo == "enterprise" else col_modificado_por
    filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df.get(col_fechado, '').unique()) if col_fechado else []
    filtro_diag = st.sidebar.multiselect("Causa Raiz" if relatorio_tipo == "consumer" else "Diagnóstico", df.get("Causa raiz" if relatorio_tipo=="consumer" else "Diagnóstico", '').unique())
    filtro_satelite = st.sidebar.multiselect("Satélite", df["Satélite"].unique()) if relatorio_tipo=="consumer" else []

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()
    if filtro_aberto: df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]
    if filtro_fechado and col_fechado: df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
    if filtro_diag:
        col_diag = "Causa raiz" if relatorio_tipo=="consumer" else "Diagnóstico"
        df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]
    if relatorio_tipo=="consumer" and filtro_satelite: df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]
    df_filtrado = df_filtrado.replace("", "Não informado")

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = len(df_filtrado[df_filtrado['Fechado']])

    # ---------------- TEMPO MÉDIO ----------------
    def calcular_tempo_medio(df):
        col_ab = next((c for c in df.columns if "Data/Hora de abertura" in c or "Data de abertura" in c), None)
        col_hab = next((c for c in df.columns if "Hora de abertura" in c), None)
        col_f = next((c for c in df.columns if "Data/Hora de fechamento" in c or "Data de fechamento" in c), None)
        col_hf = next((c for c in df.columns if "Hora de fechamento" in c), None)
        if not col_ab or not col_f: return 0
        ab = pd.to_datetime(df[col_ab].astype(str) + (" " + df[col_hab].astype(str) if col_hab else ""), errors='coerce')
        fe = pd.to_datetime(df[col_f].astype(str) + (" " + df[col_hf].astype(str) if col_hf else ""), errors='coerce')
        return round(((fe - ab).dt.total_seconds()/60).mean(),2)

    tempo_medio = calcular_tempo_medio(df_filtrado)

    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio}")
    # Maior ofensor
    col_ofensor = "Causa raiz" if relatorio_tipo=="consumer" else "Diagnóstico"
    df_valid = df_filtrado[df_filtrado[col_ofensor] != "Não informado"]
    if not df_valid.empty:
        contagem = df_valid[col_ofensor].value_counts()
        maior_ofensor = contagem.index[0]
        pct_maior = contagem.iloc[0]/len(df_filtrado)*100
    else:
        maior_ofensor, pct_maior = "-",0
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    if relatorio_tipo=="consumer":
        qtd_evento = (df_filtrado["Tipo de registro do caso"]=="Operações - Evento").sum()
        qtd_cm = (df_filtrado["Tipo de registro do caso"]=="Operações - CM").sum()
        st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
        st.write(f"🟪 Operações - CM: **{qtd_cm}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100):.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100):.1f}%)")

    # ---------------- FUNÇÕES GRÁFICOS ----------------
    def grafico_com_tabela(df_graf,coluna,titulo,icone="📁"):
        df_graf = df_graf[df_graf[coluna]!="Não informado"]
        if df_graf.empty: return None,None
        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela["%"] = (tabela["Qtd"]/tabela["Qtd"].sum()*100).round(2)
        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4,3])
        tabela_height = min(350,50+len(tabela)*35)
        with col_t: st.dataframe(tabela,height=tabela_height)
        fig = px.bar(tabela,x=coluna,y="Qtd",text="Qtd",color="Qtd",color_continuous_scale="Blues",template="plotly_white")
        fig.update_traces(textposition="outside")
        with col_g: st.plotly_chart(fig,use_container_width=True)
        return fig,tabela

    grafico_com_tabela(df_filtrado,"Criado por","Chamados abertos por usuário","🔵")
    if col_fechado: df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado]!="Não informado")]
    else: df_fechados = pd.DataFrame()
    if not df_fechados.empty: grafico_com_tabela(df_fechados,col_fechado,"Chamados fechados por usuário","🔴")
    if relatorio_tipo=="enterprise": grafico_com_tabela(df_filtrado,"Reclamação","Reclamação","📌")
    grafico_com_tabela(df_filtrado,col_ofensor,col_ofensor,"📌")

    if relatorio_tipo=="consumer":
        st.subheader("🛰 Satélite")
        tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
        tabela_sat.columns=["Satélite","Qtd"]
        tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
        col_t,col_g = st.columns([1.4,3])
        tabela_height = min(350,50+len(tabela_sat)*35)
        with col_t: st.dataframe(tabela_sat,height=tabela_height)
        fig_sat = px.bar(tabela_sat,x="Satélite",y="Qtd",text="Qtd",color="Qtd",color_continuous_scale="Blues",template="plotly_white")
        fig_sat.update_traces(textposition="outside")
        with col_g: st.plotly_chart(fig_sat,use_container_width=True)

    # ---------------- DOWNLOAD HTML FIEL ----------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><title>"+titulo_dashboard+"</title></head><body>")
        # Capturar gráficos e tabelas como imagens
        for fig in st.session_state._children.copy().values():
            try:
                if hasattr(fig,'_repr_html_'):
                    buffer.write(fig._repr_html_())
            except: pass
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        "📥 Baixar Dashboard",
        data=to_html_bonito(),
        file_name="dashboard.html",
        mime="text/html"
    )
