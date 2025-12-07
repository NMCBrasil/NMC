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

# CSS customizado: fundo azul claro, letras pretas, botão download legível, gráficos com fundo cinza
st.markdown("""
<style>
/* Fundo azul claro e letras pretas */
.stApp {
    background-color: #e6f2ff;
    color: black;
}

/* Força textos de métricas para preto */
.stMetricLabel, .stMetricValue, .css-1v3fvcr, .css-1aumxhk {
    color: black !important;
}

/* Estiliza todos os botões de download */
.stDownloadButton button {
    color: black !important;                   /* texto preto */
    background-color: #cce0ff !important;      /* azul claro mais visível */
    border: 1px solid black !important;
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

    # Maior ofensor
    if not df_filtrado.empty:
        maior_ofensor = df_filtrado['Criado por'].value_counts().idxmax()
        qtd_ofensor = df_filtrado['Criado por'].value_counts().max()
        pct_ofensor = (qtd_ofensor / len(df_filtrado) * 100).round(2)
        st.subheader("📌 Maior ofensor")
        st.markdown(f"<p style='color:black; font-size:18px;'>**{maior_ofensor}** abriu **{qtd_ofensor} chamados** ({pct_ofensor}%)</p>", unsafe_allow_html=True)

    # Tempo médio
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

    st.markdown(f"""
    <div style='background-color:#e6f2ff; padding:10px; border-radius:5px; display:inline-block'>
        <h4 style='margin:0; color:black'>⏱ Tempo médio por chamado (min)</h4>
        <p style='font-size:24px; margin:0; color:black'>{tempo_medio:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    # Função para criar gráficos com fundo cinza claro
    def plot_bar(campo, titulo):
        if campo in df_filtrado.columns and not df_filtrado[campo].dropna().empty:
            contagem = df_filtrado[campo].value_counts()
            fig = px.bar(
                x=contagem.index,
                y=contagem.values,
                text=contagem.values,
                labels={"x": campo, "y": "Quantidade"},
                title=titulo,
                color=contagem.values,
                color_continuous_scale='Blues',
                template='plotly_white'
            )
            fig.update_layout(
                plot_bgcolor='#f2f2f2',  # fundo do gráfico cinza claro
                paper_bgcolor='#f2f2f2',
                xaxis=dict(title=campo, gridcolor='white'),
                yaxis=dict(title='Quantidade', gridcolor='white')
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            return fig
        return None

    fig_reclamacao = plot_bar('Reclamação', '📊 Chamados por Reclamação')
    fig_diagnostico = plot_bar('Diagnóstico', '📊 Chamados por Diagnóstico')
    fig_fechado_por = plot_bar('Fechado por', '📊 Chamados por Responsável pelo Fechamento')

    # Tabela
    st.subheader("Detalhes dos chamados")
    colunas_exibir = ['Id', 'Status', 'Criado por', 'Data de abertura', 'Hora de abertura',
                      'Fechado por', 'Data de fechamento', 'Hora de fechamento', 'Cliente',
                      'Reclamação', 'Diagnóstico']
    st.dataframe(df_filtrado[colunas_exibir].sort_values(by='Data de abertura', ascending=False), use_container_width=True)

    # Exportar dashboard como HTML
    def to_html():
        buffer = io.StringIO()
        buffer.write("<html><head><meta charset='utf-8'><title>Dashboard NMC</title>")
        buffer.write("""
        <style>
        body {background-color: #e6f2ff; color: black; font-family: Arial, sans-serif;}
        h1, h2, h4, p {color: black;}
        table {border-collapse: collapse; width: 100%; font-size:14px;}
        th, td {border: 1px solid black; padding: 4px; text-align: left;}
        th {background-color: #d9d9d9;}
        tr:nth-child(even) {background-color: #f2f2f2;}
        </style>
        """)
        buffer.write("</head><body>")
        buffer.write("<h1>Chamados NMC Enterprise</h1>")
        buffer.write(f"<p>Tempo médio: {tempo_medio:.2f} min</p>")
        buffer.write(f"<p>Maior ofensor: {maior_ofensor} ({qtd_ofensor} chamados, {pct_ofensor}%)</p>")
        buffer.write("<h2>Gráficos</h2>")
        if fig_reclamacao:
            buffer.write(fig_reclamacao.to_html(full_html=False, include_plotlyjs='cdn'))
        if fig_diagnostico:
            buffer.write(fig_diagnostico.to_html(full_html=False, include_plotlyjs='cdn'))
        if fig_fechado_por:
            buffer.write(fig_fechado_por.to_html(full_html=False, include_plotlyjs='cdn'))
        buffer.write("<h2>Tabela de Chamados</h2>")
        buffer.write(df_filtrado[colunas_exibir].to_html(index=False))
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
