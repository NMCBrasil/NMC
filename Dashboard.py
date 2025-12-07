import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ---------------------- CONFIGURAÇÃO ----------------------
st.set_page_config(
    page_title="Dashboard Chamados",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- ESTILO ----------------------
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000000 !important; font-size: 14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000000 !important; background-color: #d9e4f5 !important; border: 1px solid #000000 !important; padding: 6px 12px !important; border-radius: 5px !important; font-weight: bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000000 !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000000 !important; background-color: #f0f0f0 !important; }
div[data-baseweb="select"] > div, div[data-baseweb="select"] input, div[data-baseweb="select"] span { background-color: #f0f0f0 !important; color: #000000 !important; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------- SIDEBAR UPLOAD ----------------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ---------------------- ANTES DO UPLOAD ----------------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")

# ---------------------- DEPOIS DO UPLOAD ----------------------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()

    # ---------------------- DETECTAR TIPO DE RELATÓRIO ----------------------
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

    # ---------------------- MAPEAMENTO DE COLUNAS ----------------------
    mapa = {
        'Status': None if relatorio_tipo == "consumer" else 'Status',
        'Fechado por': None if relatorio_tipo == "consumer" else 'Fechado por',
        'Histórico': None if relatorio_tipo == "consumer" else 'Histórico',
        'Reclamação': 'Assunto' if relatorio_tipo == "consumer" else 'Reclamação',
        'Criado por': 'Criado por',
        'Diagnóstico': 'Causa raiz' if relatorio_tipo == "consumer" else 'Diagnóstico',
        'Data de abertura': 'Data/Hora de abertura' if relatorio_tipo == "consumer" else 'Data de abertura',
        'Hora de abertura': None if relatorio_tipo == "consumer" else 'Hora de abertura',
        'Data de fechamento': None if relatorio_tipo == "consumer" else 'Data de fechamento',
        'Hora de fechamento': None if relatorio_tipo == "consumer" else 'Hora de fechamento',
    }

    # ---------------------- ENTERPRISE: substituir NMC Auto ----------------------
    if relatorio_tipo == "enterprise" and mapa['Histórico'] and mapa['Fechado por']:
        df_fe = df[df[mapa['Status']].astype(str).str.strip().str.lower() == 'fechado'].copy()
        def substituir_fechado_por(row):
            historico = str(row.get(mapa['Histórico'], ''))
            if 'usuário efetuando abertura:' in historico.lower() and row.get(mapa['Fechado por'], '') == 'NMC Auto':
                try:
                    nome = historico.split("Usuário efetuando abertura:")[1].strip()
                    row[mapa['Fechado por']] = nome
                except:
                    pass
            return row
        df_fe = df_fe.apply(substituir_fechado_por, axis=1)
        df.update(df_fe)

    # ---------------------- NORMALIZAR CAMPOS DE TEXTO ----------------------
    for col in ['Criado por', 'Reclamação', 'Diagnóstico', 'Fechado por']:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # ---------------------- FILTROS ----------------------
    st.sidebar.header("🔎 Filtros")
    def filtro_multiselect(campo_nome, label):
        if mapa.get(campo_nome) and mapa[campo_nome] in df.columns:
            opcoes = df[mapa[campo_nome]].dropna().unique()
            return st.sidebar.multiselect(label, opcoes)
        else:
            return []

    responsavel_selecionado = filtro_multiselect('Fechado por', "Fechado por")
    categoria_selecionada = filtro_multiselect('Reclamação', "Reclamação")
    criado_selecionado = filtro_multiselect('Criado por', "Criado por")
    diagnostico_selecionado = filtro_multiselect('Diagnóstico', "Diagnóstico")

    # ---------------------- FILTRAGEM DE DADOS ----------------------
    df_filtrado = df.copy()
    if relatorio_tipo == "enterprise":
        df_filtrado['Fechado'] = df_filtrado[mapa['Status']].fillna("").str.strip().str.lower() == "fechado"
    else:
        df_filtrado['Fechado'] = df_filtrado['Situação'].fillna("").str.strip().str.lower() == "resolvido ou completado"

    if responsavel_selecionado and mapa['Fechado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Fechado por']].isin(responsavel_selecionado)]
    if categoria_selecionada and mapa['Reclamação']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Reclamação']].isin(categoria_selecionada)]
    if criado_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(criado_selecionado)]
    if diagnostico_selecionado and mapa['Diagnóstico']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Diagnóstico']].fillna("Não informado").isin(diagnostico_selecionado)]

    # ---------------------- CÁLCULOS DE MÉTRICAS ----------------------
    tempo_medio = 0.0
    if relatorio_tipo == "enterprise":
        df_encerrados = df_filtrado[df_filtrado['Fechado']].copy()
        if mapa['Data de abertura'] in df_encerrados.columns and mapa['Data de fechamento'] in df_encerrados.columns:
            df_encerrados['DataHoraAbertura'] = pd.to_datetime(
                df_encerrados[mapa['Data de abertura']] + ' ' +
                df_encerrados[mapa['Hora de abertura']].fillna('00:00'), errors='coerce'
            ) if mapa['Hora de abertura'] else pd.to_datetime(df_encerrados[mapa['Data de abertura']], errors='coerce')
            df_encerrados['DataHoraFechamento'] = pd.to_datetime(
                df_encerrados[mapa['Data de fechamento']] + ' ' +
                df_encerrados[mapa['Hora de fechamento']].fillna('00:00'), errors='coerce'
            ) if mapa['Hora de fechamento'] else pd.to_datetime(df_encerrados[mapa['Data de fechamento']], errors='coerce')
            df_encerrados['TempoAtendimentoMin'] = ((df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60).clip(lower=0)
            tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)

    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado[~df_filtrado['Fechado']])
    total_fechados = df_filtrado['Fechado'].sum()
    pct_abertos = (total_abertos / total_chamados * 100) if total_chamados else 0
    pct_fechados = (total_fechados / total_chamados * 100) if total_chamados else 0

    df_filtrado['Diagnóstico'] = df_filtrado.get(mapa['Diagnóstico'], pd.Series(["Não informado"]*len(df_filtrado))).fillna("Não informado")
    if not df_filtrado.empty:
        cont_diag = df_filtrado['Diagnóstico'].value_counts()
        maior_ofensor = cont_diag.idxmax()
        qtd_ofensor = cont_diag.max()
        pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)
    else:
        maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0

    # ---------------------- MÉTRICAS NA TELA ----------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 **Chamados abertos:** {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 **Chamados fechados:** {total_fechados} ({pct_fechados:.1f}%)")

    # ---------------------- FUNÇÃO DE GRÁFICOS ----------------------
    def grafico_com_tabela(df_graf, campo, titulo):
        st.subheader(f"📁 {titulo}")
        col_table, col_graph = st.columns([1.4, 3])
        df_graf = df_graf[df_graf[campo].notna() & (df_graf[campo].astype(str).str.strip() != '')].copy()
        if df_graf.empty:
            st.info(f"Nenhum dado válido para '{titulo}'.")
            return None, None
        df_graf[campo] = df_graf[campo].astype(str).str.strip()
        tabela = df_graf.groupby(campo).size().reset_index(name="Qtd de Chamados")
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)
        with col_table:
            st.dataframe(tabela, height=550, use_container_width=True)
        fig = px.bar(
            tabela,
            x=campo,
            y="Qtd de Chamados",
            text="Qtd de Chamados",
            color="Qtd de Chamados",
            color_continuous_scale="Blues",
            template="plotly_white"
        )
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)
        with col_graph:
            st.plotly_chart(fig, use_container_width=True)
        return fig, tabela

    # ---------------------- GRÁFICOS ----------------------
    df_abertos = df_filtrado.copy()
    fig_abertos_por, tab_abertos = grafico_com_tabela(df_abertos, "Criado por", "Chamados abertos por usuário")

    campo_reclamacao = mapa['Reclamação'] if relatorio_tipo == "enterprise" else "Assunto"
    fig_reclamacao, tab_reclamacao = grafico_com_tabela(df_filtrado, campo_reclamacao, "Classificação por Reclamação/Assunto")

    campo_diag = mapa['Diagnóstico'] if relatorio_tipo == "enterprise" else "Causa raiz"
    fig_diagnostico, tab_diagnostico = grafico_com_tabela(df_filtrado, campo_diag, "Classificação por Diagnóstico/Causa raiz")

    if relatorio_tipo == "enterprise":
        df_fechados = df_filtrado[df_filtrado['Fechado']].copy()
        campo_fechado = "Fechado por"
    else:
        df_fechados = df_filtrado[df_filtrado['Fechado']].copy()
        df_fechados = df_fechados[df_fechados["Caso modificado pela última vez por"].notna() & (df_fechados["Caso modificado pela última vez por"].str.strip() != "")]
        campo_fechado = "Caso modificado pela última vez por"

    fig_fechados, tab_fechados = grafico_com_tabela(df_fechados, campo_fechado, "Chamados fechados por usuário")

    # ---------------------- EXPORTAÇÃO HTML ----------------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><style>")
        buffer.write("body { background:#f0f4f8; font-family:Arial; color:#000; margin:25px; }")
        buffer.write("h1 { text-align:center; } h2 { margin-top:40px; } table { border-collapse:collapse; width:100%; margin:15px 0; }")
        buffer.write("th,td { border:1px solid #ccc; padding:6px; background:#fafafa; } th { background:#e2e2e2; }")
        buffer.write(".metric { margin:6px 0; font-weight:bold; } .linha { display:flex; flex-direction:row; gap:40px; align-items:flex-start; }")
        buffer.write(".col-esq { width:45%; } .col-dir { width:55%; }")
        buffer.write("</style></head><body>")
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<div class='metric'>⏱ Tempo médio total (min): {tempo_medio}</div>")
        buffer.write(f"<div class='metric'>📑 Total de chamados: {total_chamados}</div>")
        buffer.write(f"<div class='metric'>🔵 Abertos: {total_abertos} ({pct_abertos:.1f}%)</div>")
        buffer.write(f"<div class='metric'>🔴 Fechados: {total_fechados} ({pct_fechados:.1f}%)</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</div>")

        nomes = [
            "Chamados abertos por usuário",
            "Classificação por Reclamação/Assunto",
            "Classificação por Diagnóstico/Causa raiz",
            "Chamados fechados por usuário"
        ]
        figs = [fig_abertos_por, fig_reclamacao, fig_diagnostico, fig_fechados]
        tabs = [tab_abertos, tab_reclamacao, tab_diagnostico, tab_fechados]

        for titulo, fig, tabela in zip(nomes, figs, tabs):
            if tabela is None:
                continue
            buffer.write(f"<h2>{titulo}</h2>")
            buffer.write("<div class='linha'>")
            buffer.write("<div class='col-esq'>")
            buffer.write(tabela.to_html(index=False))
            buffer.write("</div>")
            buffer.write("<div class='col-dir'>")
            buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            buffer.write("</div></div>")

        buffer.write("<h2>Tabela completa filtrada</h2>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode("utf-8")

    st.download_button(
        label="📥 Baixar Dashboard Completo",
        data=to_html_bonito(),
        file_name="dashboard_nmc.html",
        mime="text/html"
    )
