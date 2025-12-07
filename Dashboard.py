import streamlit as st
import pandas as pd
import plotly.express as px
import io

# ------------------------------------------------------------
# CONFIGURAÇÃO
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Chamados",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# SIDEBAR – Upload
# ------------------------------------------------------------
st.sidebar.header("📂 Importar arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo", type=["csv"])

# ------------------------------------------------------------
# Antes do upload
# ------------------------------------------------------------
if uploaded_file is None:
    st.title("📊 Dashboard Chamados")
    st.info("Envie um arquivo CSV para visualizar o dashboard.")

# ------------------------------------------------------------
# Depois do upload
# ------------------------------------------------------------
if uploaded_file is not None:
    # Carregar dados
    df = pd.read_csv(uploaded_file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()

    # ------------------------------------------------------------
    # DETECÇÃO DO TIPO DE RELATÓRIO
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # MAPEAMENTO DE COLUNAS
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Substituir NMC Auto (Enterprise)
    # ------------------------------------------------------------
    if relatorio_tipo == "enterprise" and mapa['Histórico'] and mapa['Fechado por']:
        df_fe = df[df[mapa['Status']].astype(str).str.strip().str.lower() == 'fechado'].copy()
        def substituir_fechado_por(row):
            historico = str(row.get(mapa['Histórico'], ''))
            if 'Usuário efetuando abertura:' in historico and row.get(mapa['Fechado por'], '') == 'NMC Auto':
                try:
                    nome = historico.split("Usuário efetuando abertura:")[1].strip()
                    row[mapa['Fechado por']] = nome
                except:
                    pass
            return row
        df_fe = df_fe.apply(substituir_fechado_por, axis=1)
        df.update(df_fe)

    # ------------------------------------------------------------
    # FILTROS
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # FILTRAGEM DE DADOS
    # ------------------------------------------------------------
    df_filtrado = df.copy()

    if relatorio_tipo == "consumer":
        df_filtrado['Fechado'] = df_filtrado['Situação'] == "Resolvido ou Completado"
    else:
        df_filtrado['Fechado'] = df_filtrado[mapa['Status']].astype(str).str.strip().str.lower() == 'fechado'

    if responsavel_selecionado and mapa['Fechado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Fechado por']].isin(responsavel_selecionado)]
    if categoria_selecionada and mapa['Reclamação']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Reclamação']].isin(categoria_selecionada)]
    if criado_selecionado and mapa['Criado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Criado por']].isin(criado_selecionado)]
    if diagnostico_selecionado and mapa['Diagnóstico']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Diagnóstico']].fillna("Não informado").isin(diagnostico_selecionado)]

    # ------------------------------------------------------------
    # CÁLCULOS DE MÉTRICAS
    # ------------------------------------------------------------
    if relatorio_tipo == "enterprise" and mapa['Data de abertura'] and mapa['Hora de abertura'] and mapa['Data de fechamento'] and mapa['Hora de fechamento']:
        df_encerrados = df_filtrado[df_filtrado['Fechado']].copy()
        df_encerrados['DataHoraAbertura'] = pd.to_datetime(
            df_encerrados[mapa['Data de abertura']] + ' ' + df_encerrados[mapa['Hora de abertura']], errors='coerce'
        )
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(
            df_encerrados[mapa['Data de fechamento']] + ' ' + df_encerrados[mapa['Hora de fechamento']], errors='coerce'
        )
        df_encerrados['TempoAtendimentoMin'] = ((df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60).clip(lower=0).dropna()
        tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)
    else:
        tempo_medio = 0.0

    total_chamados = len(df_filtrado)
    total_abertos = len(df_filtrado) - df_filtrado['Fechado'].sum()
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

    # ------------------------------------------------------------
    # MÉTRICAS NA TELA
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 **Chamados abertos:** {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 **Chamados fechados:** {total_fechados} ({pct_fechados:.1f}%)")

    # ------------------------------------------------------------
    # FUNÇÃO DE GRÁFICOS + TABELAS
    # ------------------------------------------------------------
    def grafico_com_tabela(df_graf, campo, titulo):
        st.subheader(f"📁 {titulo}")
        col_table, col_graph = st.columns([1.4, 3])

        # Remover linhas nulas ou vazias
        df_graf = df_graf[df_graf[campo].notna() & (df_graf[campo].astype(str).str.strip() != '')].copy()
        if df_graf.empty:
            st.info(f"Nenhum dado válido para '{titulo}'.")
            return None, None

        df_graf[campo] = df_graf[campo].astype(str).str.strip()

        tabela = df_graf.groupby(campo)['Situação'].count().rename("Qtd de Chamados").reset_index()
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)

        with col_table:
            st.dataframe(tabela, height=550, use_container_width=True)

        fig = px.bar(tabela, x=campo, y="Qtd de Chamados", text="Qtd de Chamados",
                     color="Qtd de Chamados", color_continuous_scale="Blues", template="plotly_white")
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)

        with col_graph:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # ------------------------------------------------------------
    # GRÁFICOS PRINCIPAIS
    # ------------------------------------------------------------
    df_abertos = df_filtrado[~df_filtrado['Fechado']].copy()
    fig_abertos_por, tab_abertos = grafico_com_tabela(df_abertos, "Criado por", "Chamados abertos por usuário")
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    fig_reclamacao, tab_reclamacao = grafico_com_tabela(df_filtrado, mapa['Reclamação'], "Classificação por Reclamação")
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    fig_diagnostico, tab_diagnostico = grafico_com_tabela(df_filtrado, mapa['Diagnóstico'], "Classificação por Diagnóstico")
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------
    # Chamados fechados por usuário (Consumer)
    # ------------------------------------------------------------
    if relatorio_tipo == "consumer":
        df_fechados = df_filtrado[df_filtrado['Situação'] == "Resolvido ou Completado"].copy()
        # Remover linhas sem info relevante
        df_fechados = df_fechados[df_fechados['Caso modificado pela última vez por'].notna() & 
                                  (df_fechados['Caso modificado pela última vez por'].astype(str).str.strip() != '')]
        if not df_fechados.empty:
            fig_fechados, tab_fechados = grafico_com_tabela(
                df_fechados,
                "Caso modificado pela última vez por",
                "Chamados fechados por usuário"
            )
            st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum chamado fechado com informação válida para exibir.")
