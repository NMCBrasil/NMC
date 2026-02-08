import streamlit as st
import pandas as pd
import plotly.express as px
import io
import base64

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
    st.info("Envie um arquivo CSV para visualizar o dashboard.")

else:
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")

    # Detectar tipo relatório
    colunas_consumer = [
        "Situação","Assunto","Data/Hora de abertura","Criado por",
        "Causa raiz","Tipo de registro do caso","Caso modificado pela última vez por"
    ]

    if all(col in df.columns for col in colunas_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    else:
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados Enterprise"

    st.title(titulo_dashboard)

    # Normalização
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")

    # Normalização Consumer
    if relatorio_tipo == "consumer":
        palavras_chave = ["E65","63W/T19","J3"]

        def normaliza_assunto(valor):
            texto = str(valor).upper()
            for chave in palavras_chave:
                if chave in texto:
                    return chave
            return "Não informado"

        df["Assunto_Normalizado"] = df["Assunto"].apply(normaliza_assunto)

    # Flag fechado
    if relatorio_tipo == "enterprise":
        df['Fechado'] = df['Status'].str.lower() == "fechado"
    else:
        df['Fechado'] = df['Situação'].str.lower() == "resolvido ou completado"

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")

    filtro_aberto = st.sidebar.multiselect(
        "Chamados abertos por usuário", df['Criado por'].unique()
    )

    col_fechado = 'Fechado por' if relatorio_tipo=="enterprise" else 'Caso modificado pela última vez por'

    filtro_fechado = st.sidebar.multiselect(
        "Chamados fechados por usuário", df[col_fechado].unique()
    )

    col_categoria = 'Reclamação' if relatorio_tipo=="enterprise" else 'Assunto'
    filtro_categoria = st.sidebar.multiselect(col_categoria, df[col_categoria].unique())

    col_diag = 'Diagnóstico' if relatorio_tipo=="enterprise" else 'Causa raiz'
    filtro_diag = st.sidebar.multiselect(col_diag, df[col_diag].unique())

    # Aplicar filtros
    df_filtrado = df.copy()

    if filtro_aberto:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(filtro_aberto)]

    if filtro_fechado:
        df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]

    if filtro_categoria:
        df_filtrado = df_filtrado[df_filtrado[col_categoria].isin(filtro_categoria)]

    if filtro_diag:
        df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = df_filtrado['Fechado'].sum()

    pct_abertos = (total_abertos/total_chamados*100) if total_chamados else 0
    pct_fechados = (total_fechados/total_chamados*100) if total_chamados else 0

    # Maior ofensor
    campo_ofensor = col_diag
    df_valid_ofensor = df_filtrado[df_filtrado[campo_ofensor]!=""]

    if not df_valid_ofensor.empty:
        cont_ofensor = df_valid_ofensor[campo_ofensor].value_counts()
        maior_ofensor = cont_ofensor.idxmax()
        qtd_ofensor = cont_ofensor.max()
        pct_ofensor = round(qtd_ofensor/len(df_valid_ofensor)*100,2)
    else:
        maior_ofensor,qtd_ofensor,pct_ofensor="-",0,0

    # Tempo médio enterprise
    tempo_medio = 0.0
    if relatorio_tipo=="enterprise":
        try:
            df_enc = df_filtrado[df_filtrado['Fechado']].copy()
            df_enc['DataHoraAbertura'] = pd.to_datetime(
                df_enc['Data de abertura']+" "+df_enc['Hora de abertura'],
                errors='coerce'
            )
            df_enc['DataHoraFechamento'] = pd.to_datetime(
                df_enc['Data de fechamento']+" "+df_enc['Hora de fechamento'],
                errors='coerce'
            )
            df_enc['TempoAtendimentoMin'] = (
                df_enc['DataHoraFechamento'] - df_enc['DataHoraAbertura']
            ).dt.total_seconds()/60

            tempo_medio = round(df_enc['TempoAtendimentoMin'].mean(),2)
        except:
            pass

    # Mostrar métricas
    col1,col2,col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)",f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor",maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor",f"{pct_ofensor}% ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({pct_fechados:.1f}%)")

    # ---------------- FUNÇÃO GRÁFICO ----------------
    def grafico_com_tabela(df_graf,coluna,titulo):
        tabela=df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela=tabela.sort_values("Qtd",ascending=False)

        st.subheader(titulo)
        col_t,col_g=st.columns([1.4,3])

        with col_t:
            st.dataframe(tabela,height=500)

        fig=px.bar(tabela,x=coluna,y="Qtd",text="Qtd",template="plotly_white")

        with col_g:
            st.plotly_chart(fig,use_container_width=True)

        return fig,tabela

    fig_abertos,tab_abertos=grafico_com_tabela(df_filtrado,"Criado por","Chamados abertos por usuário")
    fig_fechados,tab_fechados=grafico_com_tabela(df_filtrado[df_filtrado['Fechado']],col_fechado,"Chamados fechados")
    fig_categoria,tab_categoria=grafico_com_tabela(df_filtrado,col_categoria,col_categoria)
    fig_diag,tab_diag=grafico_com_tabela(df_filtrado,col_diag,col_diag)

    # ---------------- EXPORTAR HTML ----------------
    def to_html_bonito():

        buffer=io.StringIO()
        buffer.write(f"<html><head><meta charset='utf-8'><title>{titulo_dashboard}</title></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")

        # 🔥 BOTÃO DOWNLOAD CSV FUNCIONAL NO HTML
        csv_bytes=df_filtrado.to_csv(index=False).encode("utf-8")
        b64=base64.b64encode(csv_bytes).decode()

        buffer.write(f"""
        <div style="margin:20px 0;">
            <a download="dados_filtrados.csv"
               href="data:text/csv;base64,{b64}"
               style="background:#d9e4f5;padding:10px 18px;
               border-radius:6px;border:1px solid #000;
               text-decoration:none;color:#000;font-weight:bold;">
               📥 Baixar dados CSV
            </a>
        </div>
        """)

        for titulo,tabela,fig in [
            ("Chamados abertos",tab_abertos,fig_abertos),
            ("Chamados fechados",tab_fechados,fig_fechados),
            (col_categoria,tab_categoria,fig_categoria),
            (col_diag,tab_diag,fig_diag)
        ]:
            buffer.write(f"<h2>{titulo}</h2>")
            buffer.write(tabela.to_html(index=False))
            buffer.write(fig.to_html(full_html=False,include_plotlyjs='cdn'))

        buffer.write("</body></html>")

        return buffer.getvalue().encode("utf-8")

    st.download_button(
        "📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name="dashboard.html",
        mime="text/html"
    )
