# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Configuração do app
st.set_page_config(
    page_title="Chamados NMC Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tema claro e letras pretas
st.markdown("""
<style>
.stMetricLabel, .stMetricValue { color: #000000 !important; }
div.stDataFrame div.row_widget.stDataFrame { background-color: #f7f7f7 !important; color: #000000 !important; font-size: 14px; }
.plotly-graph-div { background-color: #f7f7f7 !important; }
.stDownloadButton button { color: #000000 !important; background-color: #d9e4f5 !important; border: 1px solid #000000 !important; padding: 6px 12px !important; border-radius: 5px !important; font-weight: bold !important; }
section[data-testid="stSidebar"] { background-color: #e8e8e8 !important; color: #000000 !important; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] select { color: #000000 !important; background-color: #f0f0f0 !important; }
div[data-baseweb="select"] > div, div[data-baseweb="select"] input, div[data-baseweb="select"] span { background-color: #f0f0f0 !important; color: #000000 !important; }
input[type="file"]::file-selector-button { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px 10px; }
input[type="file"] { background-color: #d9e4f5 !important; color: #000000 !important; font-weight: bold !important; border: 1px solid #000000; border-radius: 5px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

st.title("Chamados NMC Enterprise")

# Função para carregar dados
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    return df

# Sidebar
st.sidebar.header("Upload de CSV")
uploaded_file = st.sidebar.file_uploader("Escolha o arquivo CSV", type=["csv"])

if uploaded_file is not None:
    df = carregar_dados(uploaded_file)

    # ===============================
    # Substituir NMC Auto pelo usuário do histórico (somente fechados)
    # ===============================
    if 'Histórico' in df.columns:
        def substituir_nmc_auto_fechar(row):
            if str(row.get('Status','')).strip().lower() != 'fechado':
                return row

    if 'Histórico' in df.columns and 'Fechado por' in df.columns:
        df_fe = df[df['Status'].str.strip().str.lower() == 'fechado'].copy()

        def substituir_fechado_por(row):
            historico = str(row.get('Histórico',''))
            if 'Usuário efetuando abertura:' in historico and row.get('Fechado por','') == 'NMC Auto':
                try:
                    nome = historico.split('Usuário efetuando abertura:')[1].strip()
                    row['Fechado por'] = nome
                except:
                    pass

            fechado_por = str(row.get('Fechado por',''))
            if 'Usuário efetuando abertura:' in historico and fechado_por.strip().lower() == 'nmc auto':
                nome = historico.split('Usuário efetuando abertura:')[1].strip()
                row['Fechado por'] = nome
            return row

        df = df.apply(substituir_nmc_auto_fechar, axis=1)
        df_fe = df_fe.apply(substituir_fechado_por, axis=1)
        df.update(df_fe)

    # ===============================
    # Filtros
    # ===============================
    st.sidebar.header("Filtros")

    # filtro Fechado por
    responsaveis = df['Fechado por'].dropna().unique()
    responsavel_selecionado = st.sidebar.multiselect("Responsável pelo fechamento", responsaveis)

    # filtro Reclamação
    categorias = df['Reclamação'].dropna().unique()
    categoria_selecionada = st.sidebar.multiselect("Categoria de Reclamação", categorias)

    # 🔥 NOVO: Filtro Abertos por (Criado por)
    if 'Criado por' in df.columns:
        criados = df['Criado por'].dropna().unique()
        criado_selecionado = st.sidebar.multiselect("Abertos por", criados)
    else:
        criado_selecionado = []

    # 🔥 NOVO: Filtro Diagnóstico
    if 'Diagnóstico' in df.columns:
        diagnosticos = df['Diagnóstico'].fillna("Não informado").unique()
        diagnostico_selecionado = st.sidebar.multiselect("Diagnóstico", diagnosticos)
    else:
        diagnostico_selecionado = []

    df_filtrado = df.copy()

    # Aplicar filtros existentes
    if responsavel_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Fechado por'].isin(responsavel_selecionado)]

    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Reclamação'].isin(categoria_selecionada)]

    # Aplicar novos filtros
    if criado_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Criado por'].isin(criado_selecionado)]

    if diagnostico_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Diagnóstico'].fillna("Não informado").isin(diagnostico_selecionado)]

    # ===============================
    # Métricas
    # ===============================
    df_encerrados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].copy()

    if not df_encerrados.empty:
        df_encerrados['DataHoraAbertura'] = pd.to_datetime(df_encerrados['Data de abertura'] + ' ' + df_encerrados['Hora de abertura'], errors='coerce')
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(df_encerrados['Data de fechamento'] + ' ' + df_encerrados['Hora de fechamento'], errors='coerce')
        df_encerrados['TempoAtendimentoMin'] = ((df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60).clip(lower=0).dropna().round(2)
        tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)
    else:
        tempo_medio = 0.0

    total_chamados = len(df_filtrado)
    total_abertos = df_filtrado[df_filtrado['Status'].str.lower() == 'aberto'].shape[0]
    total_fechados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].shape[0]

    if not df_filtrado.empty:
        df_filtrado['Diagnóstico'] = df_filtrado['Diagnóstico'].fillna('Não informado')
        criadores = df_filtrado['Diagnóstico'].value_counts()
        maior_ofensor = criadores.idxmax()
        qtd_ofensor = criadores.max()
        pct_ofensor = round((qtd_ofensor / len(df_filtrado) * 100), 2)
    else:
        maior_ofensor = '-'
        qtd_ofensor = 0
        pct_ofensor = 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio total (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % de chamados do maior ofensor", f"{pct_ofensor}% ({qtd_ofensor} chamados)")

    # 🔥 CAMPO NOVO
    st.write(
        f"### Total de chamados: **{total_chamados}** — "
        f"Abertos: **{total_abertos}** — "
        f"Fechados: **{total_fechados}**"
    )

    # ===============================
    # Função para gráficos + tabela
    # ===============================
    def grafico_com_tabela(campo, titulo):
        st.subheader(titulo)

        col_table, col_graph = st.columns([1.5,3])

        df_filtrado[campo] = df_filtrado[campo].fillna('Não informado').astype(str)

        tabela = df_filtrado.groupby(campo)['Id'].count().rename('Qtd de Chamados').reset_index()
        tabela[campo] = tabela[campo].astype(str)
        tabela['Qtd de Chamados'] = tabela['Qtd de Chamados'].astype(int)

        # ➕ COLUNA DE PORCENTAGEM
        total = tabela['Qtd de Chamados'].sum()
        tabela['% do Total'] = (tabela['Qtd de Chamados'] / total * 100).round(2).astype(str) + '%'

        with col_table:
            if campo in ["Reclamação", "Diagnóstico"]:
                st.dataframe(
                    tabela.style.set_properties(**{'color':'black','background-color':'#f7f7f7','font-size':'14px'}),
                    use_container_width=True,
                    height=600
                )
            else:
                st.dataframe(
                    tabela.style.set_properties(**{'color':'black','background-color':'#f7f7f7','font-size':'14px'}),
                    use_container_width=False,
                    width=350
                )

        contagem_x = tabela[campo].tolist()
        contagem_y = tabela['Qtd de Chamados'].tolist()

        fig = px.bar(
            x=contagem_x,
            y=contagem_y,
            text=contagem_y,
            labels={'x':'', 'y':''},
            color=contagem_y,
            color_continuous_scale='Blues',
            template='plotly_white'
        )

        fig.update_layout(
            showlegend=False,
            xaxis=dict(tickfont=dict(color='#000000'), gridcolor='#e0e0e0'),
            yaxis=dict(tickfont=dict(color='#000000'), gridcolor='#e0e0e0'),
            plot_bgcolor='#f7f7f7',
            paper_bgcolor='#f7f7f7'
        )

        fig.update_traces(textposition='outside', textfont=dict(color='black', size=12),
                          marker_line_color='black', marker_line_width=1)

        with col_graph:
            st.plotly_chart(fig, use_container_width=True)

        return fig, tabela

    # ===============================
    # Gráficos principais
    # ===============================
    fig_abertos_por, tab_abertos = grafico_com_tabela('Criado por','Abertos por:')
    fig_reclamacao, tab_reclamacao = grafico_com_tabela('Reclamação','Reclamação:')
    fig_diagnostico, tab_diagnostico = grafico_com_tabela('Diagnóstico','Diagnóstico:')
    fig_fechado_por, tab_fechado = grafico_com_tabela('Fechado por','Fechado por:')

    # ===============================
    # Exportar HTML (inclui novos dados, tabelas e gráficos)
    # ===============================
    def to_html_bonito():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><title>Dashboard NMC</title>")
        buffer.write("""
        <style>
        body {background-color: #f0f4f8; color: #000000; font-family: Arial, sans-serif; margin: 20px;}
        h1 {text-align:center; color:#000000;}
        h2, h3 {color: #000000; margin-bottom:5px;}
        p {color: #000000; margin:2px 0;}
        table {border-collapse: collapse; width: 100%; font-size:13px; margin-bottom:15px;}
        th, td {border: 1px solid #ccc; padding: 4px 6px; text-align: left; color: #000000; background-color:#f7f7f7;}
        th {background-color: #e0e0e0;}
        tr:nth-child(even) {background-color: #f9f9f9;}
        .metric {font-size:14px; font-weight:bold; margin-bottom:8px;}
        .fig-container {margin-bottom: 25px;}
        .table-and-fig {display:flex; gap:20px; align-items:flex-start; margin-bottom:30px;}
        .table-box {flex:1; min-width:300px; max-width:600px; overflow:auto;}
        .fig-box {flex:2; min-width:300px;}
        </style>
        """)
        buffer.write("</head><body>")
        buffer.write("<h1>Chamados NMC Enterprise</h1>")

        # Cabeçalho com métricas
        buffer.write(f"<div class='metric'>⏱ Tempo médio total (min): {tempo_medio:.2f}</div>")
        buffer.write(f"<div class='metric'>Total de chamados: {total_chamados} — Abertos: {total_abertos} — Fechados: {total_fechados}</div>")
        buffer.write(f"<div class='metric'>📌 Maior ofensor: {maior_ofensor} ({qtd_ofensor} chamados, {pct_ofensor}%)</div>")

        # Listas de figuras e tabelas correspondentes
        figs = [fig_abertos_por, fig_reclamacao, fig_diagnostico, fig_fechado_por]
        tabs = [tab_abertos, tab_reclamacao, tab_diagnostico, tab_fechado]
        titulos = ['Abertos por:', 'Reclamação:', 'Diagnóstico:', 'Fechado por:']

        for titulo, fig, tabela in zip(titulos, figs, tabs):
            buffer.write(f"<h2>{titulo}</h2>")
            buffer.write("<div class='table-and-fig'>")
            buffer.write("<div class='table-box'>")
            buffer.write(tabela.to_html(index=False, classes='data-table', border=0))
            buffer.write("</div>")
            buffer.write("<div class='fig-box'>")
            buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            buffer.write("</div>")
            buffer.write("</div>")

        buffer.write("<h2>Tabela completa de chamados</h2>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode('utf-8')

    st.download_button(
        label="📥 Baixar Dashboard",
        data=to_html_bonito(),
        file_name="dashboard_completo.html",
        mime="text/html"
    )

else:
    st.info("Aguardando upload do arquivo CSV para exibir o dashboard.")
