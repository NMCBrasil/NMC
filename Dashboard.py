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

.mensagem-inicial {
    font-size: 18px;
    color: #000080;
    background-color: #d9e4f5;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #000080;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FUNÇÃO AUXILIAR PARA LOCALIZAR COLUNAS ----------------
def encontrar_coluna_por_chave(df, lista_chaves):
    for chave in lista_chaves:
        for col in df.columns:
            if chave.lower() in col.lower():
                return col
    return None

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.markdown(
        '<div class="mensagem-inicial">'
        '📄 Envie um arquivo CSV separado por vírgula para visualizar o dashboard.<br>'
        'O sistema detecta automaticamente colunas de datas, usuários, causas e tipos, '
        'e exibirá gráficos e métricas de forma automática.'
        '</div>',
        unsafe_allow_html=True
    )
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
    relatorio_tipo = "consumer" if all(encontrar_coluna_por_chave(df, [c]) for c in colunas_consumer) else "enterprise"
    titulo_dashboard = "📊 Chamados Consumer" if relatorio_tipo=="consumer" else "📊 Chamados Enterprise"
    st.title(titulo_dashboard)

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer":
        col_assunto = encontrar_coluna_por_chave(df, ["Assunto"])
        if col_assunto:
            def normaliza_satelite(valor):
                texto = str(valor).upper()
                if "E65" in texto:
                    return "E65"
                if "63W" in texto or "T19" in texto:
                    return "63W/T19"
                if "J3" in texto:
                    return "J3"
                return "Não informado"
            df["Satélite"] = df[col_assunto].apply(normaliza_satelite)
        else:
            df["Satélite"] = "Não informado"

    # ---------------- FLAG DE FECHADO ----------------
    col_situacao = encontrar_coluna_por_chave(df, ["Situação"])
    col_status = encontrar_coluna_por_chave(df, ["Status"])
    col_modificado_por = encontrar_coluna_por_chave(df, ["Caso modificado pela última vez por"])
    col_fechado_por = encontrar_coluna_por_chave(df, ["Fechado por"])

    if relatorio_tipo == "enterprise" and col_status:
        df['Fechado'] = df[col_status].str.lower() == "fechado"
    elif col_situacao:
        df['Fechado'] = df[col_situacao].str.lower() == "resolvido ou completado"
    else:
        df['Fechado'] = False

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    filtro_aberto = []
    filtro_fechado = []
    filtro_categoria = []
    filtro_diag = []
    filtro_satelite = []

    col_criado_por = encontrar_coluna_por_chave(df, ["Criado por"])
    col_reclamacao = encontrar_coluna_por_chave(df, ["Reclamação"])
    col_diagnostico = encontrar_coluna_por_chave(df, ["Diagnóstico"])
    col_causa_raiz = encontrar_coluna_por_chave(df, ["Causa raiz"])

    if col_criado_por:
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df[col_criado_por].unique())
    if relatorio_tipo == "enterprise" and col_fechado_por:
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df[col_fechado_por].unique())
    elif relatorio_tipo == "consumer" and col_modificado_por:
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df[col_modificado_por].unique())
    if relatorio_tipo == "enterprise" and col_reclamacao:
        filtro_categoria = st.sidebar.multiselect("Reclamação", df[col_reclamacao].unique())
    if col_diagnostico:
        filtro_diag = st.sidebar.multiselect("Causa / Diagnóstico", df[col_diagnostico].unique())
    if relatorio_tipo == "consumer" and col_causa_raiz:
        filtro_diag = st.sidebar.multiselect("Causa raiz", df[col_causa_raiz].unique())
    if relatorio_tipo == "consumer":
        filtro_satelite = st.sidebar.multiselect("Satélite", df["Satélite"].unique())

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()
    if filtro_aberto and col_criado_por:
        df_filtrado = df_filtrado[df_filtrado[col_criado_por].isin(filtro_aberto)]
    if filtro_fechado:
        col_fechado = col_fechado_por if relatorio_tipo=="enterprise" else col_modificado_por
        if col_fechado:
            df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
    if filtro_categoria and col_reclamacao:
        df_filtrado = df_filtrado[df_filtrado[col_reclamacao].isin(filtro_categoria)]
    if filtro_diag:
        col_diag = col_diagnostico if relatorio_tipo=="enterprise" else col_causa_raiz
        if col_diag:
            df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]
    if filtro_satelite:
        df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]

    # ---------------- LIMPEZA ----------------
    df_filtrado = df_filtrado.replace("", "Não informado")

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = len(df_filtrado[df_filtrado['Fechado']])
    col1, col2, col3 = st.columns(3)

    # Tempo médio Enterprise
    col_data_abertura = encontrar_coluna_por_chave(df_filtrado, ["Data/Hora de abertura", "Data de abertura"])
    col_data_fechamento = encontrar_coluna_por_chave(df_filtrado, ["Data/Hora de fechamento", "Data de fechamento"])
    tempo_medio = 0
    if relatorio_tipo=="enterprise" and col_data_abertura and col_data_fechamento:
        try:
            df_filtrado[col_data_abertura] = pd.to_datetime(df_filtrado[col_data_abertura], errors='coerce')
            df_filtrado[col_data_fechamento] = pd.to_datetime(df_filtrado[col_data_fechamento], errors='coerce')
            df_filtrado['Delta'] = (df_filtrado[col_data_fechamento] - df_filtrado[col_data_abertura]).dt.total_seconds() / 60
            tempo_medio = df_filtrado['Delta'].mean()
        except:
            tempo_medio = 0
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")

    # ---------------- MAIOR OFENSOR ----------------
    coluna_ofensor = col_diagnostico if relatorio_tipo=="enterprise" else col_causa_raiz
    pct_maior = 0
    maior_ofensor = "-"
    if coluna_ofensor and coluna_ofensor in df_filtrado.columns:
        df_valid_ofensor = df_filtrado[df_filtrado[coluna_ofensor] != "Não informado"]
        if not df_valid_ofensor.empty:
            contagem = df_valid_ofensor[coluna_ofensor].value_counts()
            maior_ofensor = contagem.index[0]
            qtd_maior = contagem.iloc[0]
            pct_maior = (qtd_maior / df_valid_ofensor.shape[0] * 100)
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(" ")
    if relatorio_tipo=="consumer":
        col_tipo_registro = encontrar_coluna_por_chave(df_filtrado, ["Tipo de registro do caso"])
        if col_tipo_registro:
            qtd_evento = (df_filtrado[col_tipo_registro]=="Operações - Evento").sum()
            qtd_cm = (df_filtrado[col_tipo_registro]=="Operações - CM").sum()
            st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
            st.write(f"🟪 Operações - CM: **{qtd_cm}**")

    st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100 if total_chamados>0 else 0):.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100 if total_chamados>0 else 0):.1f}%)")

    # ---------------- FUNÇÃO GRÁFICOS ----------------
    def tabela_limpa(df):
        df = df.replace("", "Não informado")
        df = df.dropna(how="all")
        return df

    def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
        if coluna not in df_graf.columns:
            return None, None
        df_graf = df_graf[df_graf[coluna] != "Não informado"]
        if df_graf.empty:
            return None, None

        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela = tabela[tabela["Qtd"]>0]
        tabela["%"] = (tabela["Qtd"]/tabela["Qtd"].sum()*100).round(2)
        tabela = tabela_limpa(tabela)
        if tabela.empty:
            return None, None

        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4,3])
        tabela_height = min(350, 50+len(tabela)*35)
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
    if col_criado_por:
        grafico_com_tabela(df_filtrado, col_criado_por, "Chamados abertos por usuário", "🔵")
    if col_fechado_por or col_modificado_por:
        col_fechado = col_fechado_por if relatorio_tipo=="enterprise" else col_modificado_por
        df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado] != "Não informado")]
        grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", "🔴")
    if relatorio_tipo=="enterprise" and col_reclamacao:
        grafico_com_tabela(df_filtrado, col_reclamacao, "Reclamação", "📌")
    if coluna_ofensor:
        grafico_com_tabela(df_filtrado, coluna_ofensor, coluna_ofensor, "📌")
    if relatorio_tipo=="consumer":
        st.subheader("🛰 Satélite")
        if "Satélite" in df_filtrado.columns:
            tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
            tabela_sat.columns = ["Satélite","Qtd"]
            tabela_sat["%"] = (tabela_sat["Qtd"]/tabela_sat["Qtd"].sum()*100).round(2)
            tabela_sat = tabela_limpa(tabela_sat)
            col_t, col_g = st.columns([1.4,3])
            tabela_height = min(350, 50+len(tabela_sat)*35)
            with col_t:
                st.dataframe(tabela_sat, height=tabela_height)
            fig_sat = px.bar(
                tabela_sat, x="Satélite", y="Qtd", text="Qtd",
                color="Qtd", color_continuous_scale="Blues", template="plotly_white"
            )
            fig_sat.update_traces(textposition="outside")
            with col_g:
                st.plotly_chart(fig_sat, use_container_width=True)

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
