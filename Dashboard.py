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
input[type="file"] { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# TELA INICIAL
# ------------------------------------------------------------
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Logo_Transparente.png/320px-Logo_Transparente.png", width=120)
st.title("📊 Dashboard Chamados")
st.info("Envie um arquivo CSV para visualizar o dashboard.")

# ------------------------------------------------------------
# UPLOAD
# ------------------------------------------------------------
uploaded_file = st.file_uploader("Selecione o arquivo", type=["csv"])
if uploaded_file is not None:

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
        titulo_dashboard = "📊 Chamados Consumer"
        relatorio_tipo = "consumer"
    else:
        titulo_dashboard = "📊 Chamados NMC Enterprise"
        relatorio_tipo = "enterprise"

    st.title(titulo_dashboard)

    # ------------------------------------------------------------
    # Mapear colunas
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
    if mapa['Histórico'] and mapa['Fechado por']:
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

    df_filtrado = df.copy()
    if responsavel_selecionado and mapa['Fechado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Fechado por']].isin(responsavel_selecionado)]
    if categoria_selecionada and mapa['Reclamação']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Reclamação']].isin(categoria_selecionada)]
    if criado_selecionado and mapa['Criado por']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Criado por']].isin(criado_selecionado)]
    if diagnostico_selecionado and mapa['Diagnóstico']:
        df_filtrado = df_filtrado[df_filtrado[mapa['Diagnóstico']].fillna("Não informado").isin(diagnostico_selecionado)]

    # ------------------------------------------------------------
    # DETERMINAR CHAMADOS FECHADOS
    # ------------------------------------------------------------
    if relatorio_tipo == "consumer":
        df_fechados = df_filtrado[
            df_filtrado['Situação'].astype(str).str.lower().str.contains('resolvido|completado')
        ].copy()
        total_chamados = len(df_filtrado)
        total_fechados = len(df_fechados)
        total_abertos = total_chamados - total_fechados
        pct_abertos = (total_abertos / total_chamados * 100) if total_chamados > 0 else 0
        pct_fechados = (total_fechados / total_chamados * 100) if total_chamados > 0 else 0
    else:
        status_col = mapa.get('Status')
        if status_col and status_col in df_filtrado.columns:
            total_chamados = len(df_filtrado)
            total_abertos = df_filtrado[df_filtrado[status_col].astype(str).str.strip().str.lower() == 'aberto'].shape[0]
            total_fechados = df_filtrado[df_filtrado[status_col].astype(str).str.strip().str.lower() == 'fechado'].shape[0]
            pct_abertos = (total_abertos / total_chamados * 100) if total_chamados > 0 else 0
            pct_fechados = (total_fechados / total_chamados * 100) if total_chamados > 0 else 0

    # ------------------------------------------------------------
    # TEMPO MÉDIO (Enterprise)
    # ------------------------------------------------------------
    tempo_medio = 0.0
    if relatorio_tipo == "enterprise" and mapa.get('Data de abertura') in df_filtrado.columns:
        df_encerrados = df_filtrado.copy()
        if mapa.get('Data de abertura') and mapa.get('Data de fechamento') and \
           mapa['Data de abertura'] in df_encerrados.columns and mapa['Data de fechamento'] in df_encerrados.columns:
            df_encerrados['DataHoraAbertura'] = pd.to_datetime(df_encerrados[mapa['Data de abertura']], errors='coerce')
            df_encerrados['DataHoraFechamento'] = pd.to_datetime(df_encerrados[mapa['Data de fechamento']], errors='coerce')
            df_encerrados['TempoAtendimentoMin'] = ((df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds()/60).clip(lower=0).dropna()
            if not df_encerrados['TempoAtendimentoMin'].empty:
                tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)

    # ------------------------------------------------------------
    # MAIOR OFENSOR
    # ------------------------------------------------------------
    maior_ofensor, qtd_ofensor, pct_ofensor = "-", 0, 0.0
    if mapa.get('Diagnóstico') in df_filtrado.columns:
        df_filtrado[mapa['Diagnóstico']] = df_filtrado[mapa['Diagnóstico']].fillna('Não informado')
        if not df_filtrado.empty:
            cont_diag = df_filtrado[mapa['Diagnóstico']].value_counts()
            maior_ofensor = cont_diag.idxmax()
            qtd_ofensor = cont_diag.max()
            pct_ofensor = round(qtd_ofensor / len(df_filtrado) * 100, 2)

    # ------------------------------------------------------------
    # EXIBIÇÃO DAS MÉTRICAS
    # ------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % dos chamados do maior ofensor", f"{pct_ofensor}%  ({qtd_ofensor})")

    st.write(f"### 📑 Total de chamados: **{total_chamados}**")
    st.write(f"🔵 **Chamados abertos:** {total_abertos} ({pct_abertos:.1f}%)")
    st.write(f"🔴 **Chamados fechados:** {total_fechados} ({pct_fechados:.1f}%)")

    # ------------------------------------------------------------
    # FUNÇÃO PARA TABELA + GRÁFICO
    # ------------------------------------------------------------
    def grafico_com_tabela(df_base, campo, titulo):
        if not campo or campo not in df_base.columns:
            return None, None
        col_table, col_graph = st.columns([1.4,3])
        df_base[campo] = df_base[campo].fillna("Não informado").astype(str)
        tabela = df_base.groupby(campo)['Criado por'].count().rename("Qtd de Chamados").reset_index()
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / tabela['Qtd de Chamados'].sum() * 100).round(2)
        with col_table:
            st.dataframe(tabela, height=400, use_container_width=True)
        fig = px.bar(tabela, x=campo, y="Qtd de Chamados", text="Qtd de Chamados",
                     color="Qtd de Chamados", color_continuous_scale="Blues", template="plotly_white")
        fig.update_traces(textposition="outside", marker_line_color="black", marker_line_width=1)
        with col_graph:
            st.plotly_chart(fig, use_container_width=True)
        return fig, tabela

    # ------------------------------------------------------------
    # GRÁFICOS PRINCIPAIS
    # ------------------------------------------------------------
    fig_abertos, tab_abertos = grafico_com_tabela(df_filtrado, mapa.get('Criado por'), "Chamados abertos por usuário")
    fig_reclamacao, tab_reclamacao = grafico_com_tabela(df_filtrado, mapa.get('Reclamação'), "Classificação por Reclamação")
    fig_diagnostico, tab_diagnostico = grafico_com_tabela(df_filtrado, mapa.get('Diagnóstico'), "Classificação por Diagnóstico")
    if relatorio_tipo == "enterprise":
        fig_fechado, tab_fechado = grafico_com_tabela(df_filtrado[df_filtrado[mapa['Status']].astype(str).str.strip().str.lower()=='fechado'], mapa.get('Fechado por'), "Chamados fechados por usuário")
    elif relatorio_tipo == "consumer":
        fig_fechado, tab_fechado = grafico_com_tabela(df_fechados, 'Caso modificado pela última vez por', "Chamados fechados")

    # ------------------------------------------------------------
    # EXPORTAÇÃO HTML
    # ------------------------------------------------------------
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write(f"""
        <html><head><meta charset='utf-8'><style>
        body {{ background:#f0f4f8; font-family:Arial; color:#000; margin:25px; }}
        h1 {{ text-align:center; }}
        h2 {{ margin-top:40px; }}
        table {{ border-collapse:collapse; width:100%; margin:15px 0; }}
        th,td {{ border:1px solid #ccc; padding:6px; background:#fafafa; }}
        th {{ background:#e2e2e2; }}
        .metric {{ margin:6px 0; font-weight:bold; }}
        .linha {{ display:flex; flex-direction:row; gap:40px; align-items:flex-start; }}
        .col-esq {{ width:45%; }}
        .col-dir {{ width:55%; }}
        </style></head><body>
        """)
        buffer.write(f"<h1>{titulo_dashboard}</h1>")
        buffer.write(f"<div class='metric'>⏱ Tempo médio total (min): {tempo_medio}</div>")
        buffer.write(f"<div class='metric'>📑 Total de chamados: {total_chamados}</div>")
        buffer.write(f"<div class='metric'>🔵 Abertos: {total_abertos} ({pct_abertos:.1f}%)</div>")
        buffer.write(f"<div class='metric'>🔴 Fechados: {total_fechados} ({pct_fechados:.1f}%)</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({pct_ofensor}%)</div>")

        figs = [fig_abertos, fig_reclamacao, fig_diagnostico, fig_fechado]
        tabs = [tab_abertos, tab_reclamacao, tab_diagnostico, tab_fechado]
        titulos = ["Chamados abertos por usuário", "Classificação por Reclamação", "Classificação por Diagnóstico", "Chamados fechados"]
        for titulo, fig, tab in zip(titulos, figs, tabs):
            if fig is None or tab is None:
                continue
            buffer.write(f"<h2>{titulo}</h2><div class='linha'><div class='col-esq'>{tab.to_html(index=False)}</div><div class='col-dir'>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div></div>")

        # Tabela completa filtrada
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
