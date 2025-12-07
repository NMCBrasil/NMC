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

# CSS customizado para cores leves e textos legíveis
st.markdown("""
<style>
/* Fundo do dashboard */
.stApp { background-color: #f5f7fa; color: #0a0a0a; }

/* Sidebar leve */
.css-18e3th9 { background-color: #eaeaea !important; }

/* Letras de métricas */
.stMetricLabel, .stMetricValue, .css-1v3fvcr, .css-1aumxhk { color: #0a0a0a !important; }

/* Botão de download */
.stDownloadButton button {
    color: #0a0a0a !important;
    background-color: #d9e4f5 !important;
    border: 1px solid #0a0a0a !important;
    padding: 6px 12px !important;
    border-radius: 5px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Chamados NMC Enterprise")

# Função para carregar dados
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    return df

# Upload CSV
st.sidebar.header("Upload de arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Escolha o arquivo CSV", type=["csv"])

if uploaded_file is not None:
    df = carregar_dados(uploaded_file)

    # Filtros
    st.sidebar.header("Filtros")
    responsaveis = df['Fechado por'].dropna().unique()
    responsavel_selecionado = st.sidebar.multiselect("Responsável pelo fechamento", responsaveis)
    categorias = df['Reclamação'].dropna().unique()
    categoria_selecionada = st.sidebar.multiselect("Categoria de Reclamação", categorias)

    df_filtrado = df.copy()
    if responsavel_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Fechado por'].isin(responsavel_selecionado)]
    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Reclamação'].isin(categoria_selecionada)]

    # --------------------
    # Métricas principais
    # --------------------
    df_encerrados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].copy()
    if not df_encerrados.empty:
        df_encerrados['DataHoraAbertura'] = pd.to_datetime(
            df_encerrados['Data de abertura'] + ' ' + df_encerrados['Hora de abertura'], errors='coerce'
        )
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(
            df_encerrados['Data de fechamento'] + ' ' + df_encerrados['Hora de fechamento'], errors='coerce'
        )
        df_encerrados['TempoAtendimentoMin'] = (
            (df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60
        ).round(2).clip(lower=0)
        tempo_medio = df_encerrados['TempoAtendimentoMin'].mean()
    else:
        tempo_medio = 0.0

    if not df_filtrado.empty:
        maior_ofensor = df_filtrado['Criado por'].value_counts().idxmax()
        qtd_ofensor = df_filtrado['Criado por'].value_counts().max()
        pct_ofensor = (qtd_ofensor / len(df_filtrado) * 100).round(2)
    else:
        maior_ofensor = '-'
        qtd_ofensor = 0
        pct_ofensor = 0.0

    # Layout das métricas em 3 colunas
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Tempo médio (min)", f"{tempo_medio:.2f}")
    col2.metric("📌 Maior ofensor", f"{maior_ofensor}")
    col3.metric("📊 % de chamados do maior ofensor", f"{pct_ofensor}% ({qtd_ofensor} chamados)")

    # --------------------
    # Função para gráficos + tabela lado a lado
    # --------------------
    def grafico_com_tabela(campo, titulo):
        st.subheader(titulo)
        col_table, col_graph = st.columns([2,3])

        # Tabela
        tabela = df_filtrado[[campo,'Id','Status','Cliente']].groupby(campo).count().rename(columns={'Id':'Qtd de Chamados'})
        with col_table:
            st.dataframe(tabela, use_container_width=True)

        # Gráfico
        contagem = df_filtrado[campo].value_counts()
        fig = px.bar(
            x=contagem.index,
            y=contagem.values,
            text=contagem.values,
            labels={'x':campo,'y':'Quantidade'},
            color=contagem.values,
            color_continuous_scale='Blues',
            template='plotly_white'
        )
        fig.update_layout(
            plot_bgcolor='#f7f7f7',
            paper_bgcolor='#f7f7f7',
            title_font=dict(color='#0a0a0a', size=16),
            xaxis=dict(title=campo, title_font=dict(color='#0a0a0a'), tickfont=dict(color='#0a0a0a'), gridcolor='white'),
            yaxis=dict(title='Quantidade', title_font=dict(color='#0a0a0a'), tickfont=dict(color='#0a0a0a'), gridcolor='white')
        )
        fig.update_traces(textposition='outside', textfont=dict(color='black', size=12),
                          marker_line_color='black', marker_line_width=1)
        with col_graph:
            st.plotly_chart(fig, use_container_width=True)
        return fig

    # --------------------
    # Gráficos principais com tabela
    # --------------------
    fig_pessoa = grafico_com_tabela('Criado por','📋 Chamados por pessoa')
    fig_reclamacao = grafico_com_tabela('Reclamação','📊 Chamados por Reclamação')
    fig_diagnostico = grafico_com_tabela('Diagnóstico','📊 Chamados por Diagnóstico')
    fig_fechado_por = grafico_com_tabela('Fechado por','📊 Chamados por Responsável pelo Fechamento')

    # --------------------
    # Exportar dashboard completo em HTML
    # --------------------
    def to_html():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><title>Dashboard NMC</title>")
        buffer.write("""
        <style>
        body {background-color: #f5f7fa; color: #0a0a0a; font-family: Arial, sans-serif;}
        h1, h2, h4, p {color: #0a0a0a;}
        table {border-collapse: collapse; width: 100%; font-size:14px;}
        th, td {border: 1px solid #ccc; padding: 6px; text-align: left;}
        th {background-color: #e0e0e0;}
        tr:nth-child(even) {background-color: #f9f9f9;}
        </style>
        """)
        buffer.write("</head><body>")
        buffer.write("<h1>Chamados NMC Enterprise</h1>")
        buffer.write(f"<p>Tempo médio: {tempo_medio:.2f} min</p>")
        buffer.write(f"<p>Maior ofensor: {maior_ofensor} ({qtd_ofensor} chamados, {pct_ofensor}%)</p>")
        for fig in [fig_pessoa, fig_reclamacao, fig_diagnostico, fig_fechado_por]:
            buffer.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        buffer.write("<h2>Tabela completa de chamados</h2>")
        buffer.write(df_filtrado.to_html(index=False))
        buffer.write("</body></html>")
        return buffer.getvalue().encode('utf-8')

    st.download_button(
        label="📥 Baixar dashboard completo em HTML (exportável para PDF)",
        data=to_html(),
        file_name="dashboard_completo.html",
        mime="text/html"
    )

else:
    st.info("Aguardando upload do arquivo CSV para exibir o dashboard.")
