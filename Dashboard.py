import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Chamados NMC Enterprise", layout="wide")

# --- Função para carregar dados ---
@st.cache_data
def carregar_dados(caminho_csv):
    try:
        df = pd.read_csv(caminho_csv, sep=';', encoding='latin1')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

# --- Upload de arquivo ---
st.sidebar.title("Upload do Excel")
uploaded_file = st.sidebar.file_uploader("Escolha o arquivo CSV/Excel", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = carregar_dados(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine='openpyxl')

    # --- Logo e título ---
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/14/Hughes_Network_Systems_logo.png", width=200)
    st.title("Chamados NMC Enterprise")

    # --- Limpeza do dataframe ---
    df.columns = df.columns.str.strip()
    
    # --- Conversão de datas e cálculo de tempo médio ---
    df['Data de abertura'] = pd.to_datetime(df['Data de abertura'], errors='coerce')
    df['Data de fechamento'] = pd.to_datetime(df['Data de fechamento'], errors='coerce')
    df['Tempo Atendimento (min)'] = (df['Data de fechamento'] - df['Data de abertura']).dt.total_seconds() / 60

    # --- Filtros ---
    st.sidebar.subheader("Filtros")
    categoria = st.sidebar.selectbox("Selecionar categoria para gráficos", ["Todos"] + list(df['Reclamação'].dropna().unique()))
    
    if categoria != "Todos":
        df_filtrado = df[df['Reclamação'] == categoria]
    else:
        df_filtrado = df.copy()

    # --- Tempo médio de atendimento ---
    tempo_medio = df_filtrado[df_filtrado['Status'].str.lower()=='fechado']['Tempo Atendimento (min)'].mean()
    st.metric("Tempo médio em min por chamado (fechados)", f"{tempo_medio:.1f}")

    # --- Colunas de interesse ---
    colunas_graficos = ['Reclamação', 'Diagnóstico', 'Fechado por']

    # --- Criar gráficos ---
    for col in colunas_graficos:
        st.subheader(f"{col} - Top 10")
        if col in df_filtrado.columns:
            top = df_filtrado[col].value_counts().nlargest(10).reset_index()
            top.columns = [col, 'Quantidade']
            fig = px.bar(top, x=col, y='Quantidade', text='Quantidade')
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_title=col, yaxis_title='Quantidade', template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)

    # --- Mostrar tabela completa ---
    st.subheader("Detalhes dos chamados")
    st.dataframe(df_filtrado.sort_values(by='Data de abertura', ascending=False))

else:
    st.info("Faça upload de um arquivo CSV ou Excel para visualizar o dashboard.")
