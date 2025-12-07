# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(
    page_title="Chamados NMC Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Chamados NMC Enterprise")

# Função para carregar o arquivo
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    # Padroniza nomes de colunas removendo espaços extras
    df.columns = df.columns.str.strip()
    return df

# Upload do arquivo CSV
st.sidebar.header("Upload de arquivo CSV")
uploaded_file = st.sidebar.file_uploader("Escolha o arquivo CSV", type=["csv"])

if uploaded_file is not None:
    df = carregar_dados(uploaded_file)
    
    st.sidebar.header("Filtros")
    
    # Filtro por responsável
    responsaveis = df['Fechado por'].dropna().unique()
    responsavel_selecionado = st.sidebar.multiselect("Responsável pelo fechamento", responsaveis)
    
    # Filtro por categoria
    categorias = df['Reclamação'].dropna().unique()
    categoria_selecionada = st.sidebar.multiselect("Categoria de Reclamação", categorias)
    
    # Aplica filtros
    df_filtrado = df.copy()
    if responsavel_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Fechado por'].isin(responsavel_selecionado)]
    if categoria_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Reclamação'].isin(categoria_selecionada)]
    
    # Calcula tempo médio de atendimento (apenas encerrados)
    df_encerrados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].copy()
    if not df_encerrados.empty:
        # Cria coluna de datetime de abertura e fechamento
        df_encerrados['DataHoraAbertura'] = pd.to_datetime(df_encerrados['Data de abertura'] + ' ' + df_encerrados['Hora de abertura'], errors='coerce')
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(df_encerrados['Data de fechamento'] + ' ' + df_encerrados['Hora de fechamento'], errors='coerce')
        df_encerrados['TempoAtendimentoMin'] = ((df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60).round(2)
        tempo_medio = df_encerrados['TempoAtendimentoMin'].mean().round(2)
    else:
        tempo_medio = 0

    st.metric("Tempo médio em min por chamado (apenas encerrados)", tempo_medio)
    
    # Função para plotar gráfico de barras
    def plot_bar(campo, titulo):
        contagem = df_filtrado[campo].value_counts().head(10)
        if not contagem.empty:
            fig = px.bar(
                x=contagem.index,
                y=contagem.values,
                text=contagem.values,
                labels={"x": campo, "y": "Quantidade"},
                title=titulo
            )
            fig.update_traces(textposition='outside', marker_color='rgb(100,149,237)')
            fig.update_layout(yaxis=dict(title="Quantidade"), xaxis=dict(title=campo), uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)
    
    # Plota gráficos principais
    plot_bar('Reclamação', 'Top 10 Reclamações')
    plot_bar('Diagnóstico', 'Top 10 Diagnósticos')
    plot_bar('Fechado por', 'Chamados fechados por responsável')

    # Mostra tabela detalhada
    st.subheader("Detalhes dos chamados")
    colunas_exibir = ['Id', 'Status', 'Criado por', 'Data de abertura', 'Hora de abertura',
                      'Fechado por', 'Data de fechamento', 'Hora de fechamento', 'Cliente',
                      'Reclamação', 'Diagnóstico']
    st.dataframe(df_filtrado[colunas_exibir].sort_values(by='Data de abertura', ascending=False), use_container_width=True)

    # Função para download em Excel
    def to_excel(df):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Chamados')
        workbook = writer.book
        worksheet = writer.sheets['Chamados']
        # Ajusta largura das colunas
        for i, col in enumerate(df.columns):
            max_len = df[col].astype(str).map(len).max()
            worksheet.set_column(i, i, max(15, max_len + 2))
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    st.download_button(
        label="📥 Baixar dashboard em Excel",
        data=to_excel(df_filtrado),
        file_name="dashboard_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
else:
    st.info("Aguardando upload do arquivo CSV para exibir o dashboard.")
