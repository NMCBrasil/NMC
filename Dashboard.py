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

/* ------ MELHORIA NO FILTRO DE SATÉLITE ------- */
.sidebar-multiselect .stMultiSelect {
    max-height: 120px !important;
    overflow-y: auto !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TÍTULO ----------------
st.title("📊 Dashboard Chamados")

# ---------------- UPLOAD ----------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------- TELA INICIAL ----------------
if uploaded_file is None:
    st.markdown("""
    <div style="background-color:#d9e4f5; padding:15px; border-radius:8px; color:#000;">
    <strong>Importante:</strong> Envie um arquivo <code>.csv</code> separado por vírgula para visualizar o dashboard.<br>
    O sistema detecta automaticamente colunas de datas, usuários, causas e tipos.
    </div>
    """, unsafe_allow_html=True)
else:

    # ---------------- LEITURA DO CSV ----------------
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    df = df.applymap(lambda x: str(x).strip())

    # ---------------- FUNÇÃO PARA LOCALIZAR COLUNA POR CHAVE ----------------
    def encontrar_coluna_por_chave(df, chave):
        for col in df.columns:
            if chave.lower() in col.lower():
                return col
        return None

    # ---------------- DETECTAR TIPO ----------------
    colunas_consumer = [
        "Situação", "Assunto", "Data/Hora de abertura", "Criado por",
        "Causa raiz", "Tipo de registro do caso", "Caso modificado pela última vez por"
    ]

    if all(encontrar_coluna_por_chave(df, c) is not None for c in colunas_consumer):
        relatorio_tipo = "consumer"
        titulo_dashboard = "📊 Chamados Consumer"
    else:
        relatorio_tipo = "enterprise"
        titulo_dashboard = "📊 Chamados Enterprise"

    st.title(titulo_dashboard)

    # ---------------- LOCALIZAÇÃO DE COLUNAS DINÂMICAS ----------------
    col_situacao = encontrar_coluna_por_chave(df, "Situação")
    col_assunto = encontrar_coluna_por_chave(df, "Assunto")
    col_criado_por = encontrar_coluna_por_chave(df, "Criado por")
    col_causa = encontrar_coluna_por_chave(df, "Causa raiz")
    col_tipo = encontrar_coluna_por_chave(df, "Tipo de registro")
    col_modificado_por = encontrar_coluna_por_chave(df, "Caso modificado")
    col_status = encontrar_coluna_por_chave(df, "Status")
    col_fechado_por = encontrar_coluna_por_chave(df, "Fechado por")
    col_reclamacao = encontrar_coluna_por_chave(df, "Reclamação")
    col_diagnostico = encontrar_coluna_por_chave(df, "Diagnóstico")
    col_data_abertura = encontrar_coluna_por_chave(df, "Data de abertura") or encontrar_coluna_por_chave(df, "Data/Hora de abertura")
    col_data_fechamento = encontrar_coluna_por_chave(df, "Data de fechamento") or encontrar_coluna_por_chave(df, "Data/Hora de fechamento")
    col_hora_abertura = encontrar_coluna_por_chave(df, "Hora de abertura")
    col_hora_fechamento = encontrar_coluna_por_chave(df, "Hora de fechamento")

    # ---------------- NORMALIZAÇÃO CONSUMER ----------------
    if relatorio_tipo == "consumer" and col_assunto is not None:
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

    # ---------------- FLAG DE FECHADO ----------------
    if relatorio_tipo == "enterprise" and col_status is not None:
        df['Fechado'] = df[col_status].str.lower() == "fechado"
    elif relatorio_tipo == "consumer" and col_modificado_por is not None:
        df['Fechado'] = df[col_modificado_por].apply(lambda x: str(x).strip() != "")
    else:
        df['Fechado'] = False

    # ---------------- FILTROS ----------------
    st.sidebar.header("🔎 Filtros")
    if relatorio_tipo == "enterprise":
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df[col_criado_por].unique() if col_criado_por else [])
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df[col_fechado_por].unique() if col_fechado_por else [])
        filtro_categoria = st.sidebar.multiselect("Reclamação", df[col_reclamacao].unique() if col_reclamacao else [])
        filtro_diag = st.sidebar.multiselect("Diagnóstico", df[col_diagnostico].unique() if col_diagnostico else [])
    else:
        filtro_aberto = st.sidebar.multiselect("Chamados abertos por usuário", df[col_criado_por].unique() if col_criado_por else [])
        filtro_fechado = st.sidebar.multiselect("Chamados fechados por usuário", df[col_modificado_por].unique() if col_modificado_por else [])
        filtro_diag = st.sidebar.multiselect("Causa Raiz", df[col_causa].unique() if col_causa else [])
        filtro_satelite = st.sidebar.multiselect("Satélite", df["Satélite"].unique() if "Satélite" in df.columns else [])

    # ---------------- APLICAR FILTROS ----------------
    df_filtrado = df.copy()
    if filtro_aberto and col_criado_por:
        df_filtrado = df_filtrado[df_filtrado[col_criado_por].isin(filtro_aberto)]
    if filtro_fechado:
        col_fechado = col_fechado_por if relatorio_tipo == "enterprise" else col_modificado_por
        if col_fechado:
            df_filtrado = df_filtrado[df_filtrado[col_fechado].isin(filtro_fechado)]
    if relatorio_tipo == "enterprise" and filtro_categoria and col_reclamacao:
        df_filtrado = df_filtrado[df_filtrado[col_reclamacao].isin(filtro_categoria)]
    if filtro_diag and col_diagnostico if relatorio_tipo=="enterprise" else col_causa:
        col_diag = col_diagnostico if relatorio_tipo=="enterprise" else col_causa
        if col_diag:
            df_filtrado = df_filtrado[df_filtrado[col_diag].isin(filtro_diag)]
    if relatorio_tipo == "consumer" and filtro_satelite and "Satélite" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Satélite"].isin(filtro_satelite)]

    # ---------------- LIMPEZA ----------------
    df_filtrado = df_filtrado.replace("", "Não informado")

    # ---------------- MÉTRICAS ----------------
    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = len(df_filtrado[df_filtrado['Fechado']])

    col1, col2, col3 = st.columns(3)

    # Tempo médio total
    if col_data_abertura and col_data_fechamento:
        df_filtrado['Data/Hora de abertura'] = pd.to_datetime(df_filtrado[col_data_abertura], errors='coerce')
        df_filtrado['Data/Hora de fechamento'] = pd.to_datetime(df_filtrado[col_data_fechamento], errors='coerce')
        tempo_medio = (df_filtrado['Data/Hora de fechamento'] - df_filtrado['Data/Hora de abertura']).dt.total_seconds().mean() / 60
        tempo_medio_display = f"{tempo_medio:.2f}" if not pd.isna(tempo_medio) else "0.00"
    else:
        tempo_medio_display = "0.00"
    col1.metric("⏱ Tempo médio total (min)", tempo_medio_display)

    # Maior ofensor
    coluna_ofensor = col_diagnostico if relatorio_tipo == "enterprise" else col_causa
    if coluna_ofensor and coluna_ofensor in df_filtrado.columns:
        df_valid_ofensor = df_filtrado[df_filtrado[coluna_ofensor] != "Não informado"]
        if not df_valid_ofensor.empty:
            contagem = df_valid_ofensor[coluna_ofensor].value_counts()
            maior_ofensor = contagem.index[0]
            qtd_maior = contagem.iloc[0]
            pct_maior = (qtd_maior / df_valid_ofensor.shape[0] * 100)
        else:
            maior_ofensor, pct_maior = "-", 0
    else:
        maior_ofensor, pct_maior = "-", 0
    col2.metric("📌 Maior ofensor", maior_ofensor)
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_maior:.2f}%")

    # ---------------- TOTAL ----------------
    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(" ")
    if relatorio_tipo == "consumer" and col_tipo:
        qtd_evento = (df_filtrado[col_tipo] == "Operações - Evento").sum()
        qtd_cm = (df_filtrado[col_tipo] == "Operações - CM").sum()
        st.write(f"🟦 Operações - Evento: **{qtd_evento}**")
        st.write(f"🟪 Operações - CM: **{qtd_cm}**")
    st.write(f"🔵 Chamados abertos: {total_abertos} ({(total_abertos/total_chamados*100 if total_chamados else 0):.1f}%)")
    st.write(f"🔴 Chamados fechados: {total_fechados} ({(total_fechados/total_chamados*100 if total_chamados else 0):.1f}%)")

    # ---------------- FUNÇÃO GRÁFICOS ----------------
    def tabela_limpa(df):
        df = df.replace("", "Não informado")
        df = df.dropna(how="all")
        return df

    def grafico_com_tabela(df_graf, coluna, titulo, icone="📁"):
        if coluna not in df_graf.columns:
            st.subheader(f"{icone} {titulo}")
            st.write("Nenhum dado disponível.")
            return None, None
        df_graf = df_graf[df_graf[coluna] != "Não informado"]
        if df_graf.empty:
            st.subheader(f"{icone} {titulo}")
            st.write("Nenhum dado disponível.")
            return None, None

        tabela = df_graf.groupby(coluna).size().reset_index(name="Qtd")
        tabela = tabela[tabela["Qtd"] > 0]
        tabela["%"] = (tabela["Qtd"] / tabela["Qtd"].sum() * 100).round(2)
        tabela = tabela_limpa(tabela)

        st.subheader(f"{icone} {titulo}")
        col_t, col_g = st.columns([1.4, 3])
        tabela_height = min(350, 50 + len(tabela) * 35)

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
    grafico_com_tabela(df_filtrado, col_criado_por, "Chamados abertos por usuário", "🔵")
    col_fechado = col_fechado_por if relatorio_tipo == "enterprise" else col_modificado_por
    if col_fechado:
        df_fechados = df_filtrado[df_filtrado['Fechado'] & (df_filtrado[col_fechado] != "Não informado")]
        grafico_com_tabela(df_fechados, col_fechado, "Chamados fechados por usuário", "🔴")
    if relatorio_tipo == "enterprise" and col_reclamacao:
        grafico_com_tabela(df_filtrado, col_reclamacao, "Reclamação", "📌")
    col_diag = col_diagnostico if relatorio_tipo == "enterprise" else col_causa
    grafico_com_tabela(df_filtrado, col_diag, col_diag, "📌")

    # ---------------- SATÉLITE ----------------
    if relatorio_tipo == "consumer" and "Satélite" in df_filtrado.columns:
        st.subheader("🛰 Satélite")
        tabela_sat = df_filtrado["Satélite"].value_counts().reset_index()
        tabela_sat.columns = ["Satélite", "Qtd"]
        tabela_sat["%"] = (tabela_sat["Qtd"] / tabela_sat["Qtd"].sum() * 100).round(2)
        tabela_sat = tabela_limpa(tabela_sat)

        col_t, col_g = st.columns([1.4, 3])
        tabela_height = min(350, 50 + len(tabela_sat) * 35)

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
