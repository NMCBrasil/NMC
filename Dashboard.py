# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------
# Configurações iniciais
# ------------------------
st.set_page_config(
    page_title="Chamados NMC Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Chamados NMC Enterprise")

# ------------------------
# Upload de arquivo
# ------------------------
st.sidebar.header("Upload de arquivo")
uploaded_file = st.sidebar.file_uploader(
    "Escolha o arquivo CSV ou Excel (com separador ';')",
    type=["csv", "xls", "xlsx"]
)

@st.cache_data
def carregar_dados(arquivo):
    if arquivo.name.endswith(".csv"):
        df = pd.read_csv(arquivo, sep=";", encoding='latin1')
    else:
        df = pd.read_excel(arquivo)
    return df

if uploaded_file:
    df = carregar_dados(uploaded_file)

    # Limpa espaços extras nas colunas
    df.columns = df.columns.str.strip()

    # ------------------------
    # Sidebar - Filtros
    # ------------------------
    st.sidebar.header("Filtros")
    with st.sidebar.expander("Filtros por responsável"):
        responsavel = st.multiselect(
            "Responsável pelo fechamento:",
            options=df['Fechado por'].dropna().unique() if 'Fechado por' in df.columns else [],
            default=df['Fechado por'].dropna().unique() if 'Fechado por' in df.columns else []
        )

    with st.sidebar.expander("Filtros por categoria"):
        categoria = st.multiselect(
            "Reclamação:",
            options=df['Reclamação'].dropna().unique() if 'Reclamação' in df.columns else [],
            default=df['Reclamação'].dropna().unique() if 'Reclamação' in df.columns else []
        )

    # ------------------------
    # Aplicar filtros
    # ------------------------
    df_filtrado = df.copy()
    if 'Fechado por' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['Fechado por'].isin(responsavel)]
    if 'Reclamação' in df.columns:
        df_filtrado = df_filtrado[df_filtrado['Reclamação'].isin(categoria)]

    # ------------------------
    # Tempo médio de atendimento (em minutos) - apenas fechados
    # ------------------------
    if all(c in df_filtrado.columns for c in ['Data de abertura', 'Hora de abertura', 'Data de fechamento', 'Hora de fechamento', 'Status']):
        df_encerrados = df_filtrado[df_filtrado['Status'].str.lower() == 'fechado'].copy()
        df_encerrados['Data de abertura'] = df_encerrados['Data de abertura'].fillna('')
        df_encerrados['Hora de abertura'] = df_encerrados['Hora de abertura'].fillna('')
        df_encerrados['Data de fechamento'] = df_encerrados['Data de fechamento'].fillna('')
        df_encerrados['Hora de fechamento'] = df_encerrados['Hora de fechamento'].fillna('')

        df_encerrados['DataHoraAbertura'] = pd.to_datetime(
            df_encerrados.apply(
                lambda row: f"{row['Data de abertura']} {row['Hora de abertura']}" if row['Data de abertura'] and row['Hora de abertura'] else pd.NaT,
                axis=1
            ),
            errors='coerce'
        )
        df_encerrados['DataHoraFechamento'] = pd.to_datetime(
            df_encerrados.apply(
                lambda row: f"{row['Data de fechamento']} {row['Hora de fechamento']}" if row['Data de fechamento'] and row['Hora de fechamento'] else pd.NaT,
                axis=1
            ),
            errors='coerce'
        )

        df_encerrados['TempoAtendimento'] = (df_encerrados['DataHoraFechamento'] - df_encerrados['DataHoraAbertura']).dt.total_seconds() / 60
        tempo_medio = round(df_encerrados['TempoAtendimento'].mean(), 2)
        st.metric("Tempo médio em min por chamado", f"{tempo_medio}")
    else:
        st.info("Colunas de data/hora ou status não encontradas para cálculo do tempo médio.")

    # ------------------------
    # Função de gráfico segura
    # ------------------------
    def plot_bar(col, titulo):
        if col in df_filtrado.columns and not df_filtrado[col].dropna().empty:
            contagem = df_filtrado[col].value_counts().head(10)
            fig = px.bar(
                x=contagem.index,
                y=contagem.values,
                text=contagem.values,
                labels={'x': col, 'y': 'Quantidade'},
                title=titulo
            )
            fig.update_traces(textposition='outside', marker_color='steelblue')
            fig.update_layout(xaxis_title=col, yaxis_title='Quantidade', uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Não há dados para '{col}'")

    # ------------------------
    # Gráficos
    # ------------------------
    st.subheader("Gráficos de Chamados")
    plot_bar('Reclamação', 'Top 10 Reclamações')
    plot_bar('Diagnóstico', 'Top 10 Diagnósticos')
    plot_bar('Fechado por', 'Chamados fechados por responsável')

    # ------------------------
    # Tabela de chamados
    # ------------------------
    st.subheader("Detalhes dos Chamados")
    colunas_tabela = [
        'Id', 'Ticket', 'Status', 'Criado por', 'Data de abertura', 'Hora de abertura',
        'Fechado por', 'Data de fechamento', 'Hora de fechamento', 'Cliente',
        'Reclamação', 'Diagnóstico'
    ]
    colunas_tabela = [c for c in colunas_tabela if c in df_filtrado.columns]

    if colunas_tabela:
        st.dataframe(df_filtrado[colunas_tabela].sort_values(by='Data de abertura', ascending=False))
    else:
        st.info("Nenhuma coluna disponível para exibir a tabela.")
