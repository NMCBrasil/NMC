import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Chamados NMC Enterprise", layout="wide")

# -------------------------------
# ESTILO CSS
# -------------------------------
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f9f9f9; color: #0f1117; padding: 10px; }
    .stFileUploader > label, .stFileUploader button { color: #0f1117 !important; background-color: #ffffff !important; font-weight: bold; }
    .css-1d391kg h2 { color: #1f2a38; font-weight: bold; }
    div[role="listbox"] { background-color: #ffffff !important; border-radius: 6px; padding: 5px; color: #1f2a38 !important; }
    div[role="option"] { color: #1f2a38 !important; }
    .stMultiSelect > div > div { background-color: #ffffff !important; }
    h2 { color: #1f2a38; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# FUNÇÃO PARA CARREGAR DADOS
# -------------------------------
@st.cache_data
def carregar_dados(caminho):
    df = pd.read_csv(caminho, encoding='latin1', sep=';', on_bad_lines='skip', engine='python')

    # Limpa espaços e caracteres invisíveis das colunas
    df.columns = [c.strip().replace('\r','').replace('\n','').replace('\t','') for c in df.columns]

    # Limpa espaços das strings
    for col in df.select_dtypes('object').columns:
        df[col] = df[col].astype(str).str.strip()

    # Converte datas
    for col in df.columns:
        if 'Data' in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Converte horas
    for col in df.columns:
        if 'Hora' in col:
            try:
                df[col] = pd.to_timedelta(df[col])
            except:
                pass

    # Cria coluna de datetime completo
    if 'Data de abertura' in df.columns and 'Hora de abertura' in df.columns:
        df['Inicio'] = df['Data de abertura'] + df['Hora de abertura']
    if 'Data de fechamento' in df.columns and 'Hora de fechamento' in df.columns:
        df['Fim'] = df['Data de fechamento'] + df['Hora de fechamento']

    # Calcula tempo de atendimento em minutos (somente chamados fechados e positivos)
    if 'Inicio' in df.columns and 'Fim' in df.columns and 'Status' in df.columns:
        df['Tempo Atendimento (min)'] = None
        mask_fechado = df['Status'] == 'Fechado'
        df.loc[mask_fechado, 'Tempo Atendimento (min)'] = (
            (df.loc[mask_fechado, 'Fim'] - df.loc[mask_fechado, 'Inicio']).dt.total_seconds() / 60
        )
        df['Tempo Atendimento (min)'] = df['Tempo Atendimento (min)'].apply(lambda x: x if x and x>0 else None)

    return df

# -------------------------------
# FUNÇÃO PARA PLOTAR BARRAS HORIZONTAIS
# -------------------------------
def plot_bar_horizontal(df_count, coluna, titulo, top_n=10):
    df_count = df_count.fillna("Não informado")
    df_count = df_count.value_counts().head(top_n).reset_index()
    df_count.columns = [coluna, 'Contagem']
    fig = px.bar(df_count, y=coluna, x='Contagem', orientation='h', text='Contagem',
                 title=titulo, color='Contagem', color_continuous_scale='Viridis')
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis=dict(autorange="reversed"),
                      xaxis_title='Quantidade', yaxis_title='',
                      margin=dict(l=120, r=20, t=50, b=50),
                      coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# UPLOAD DE ARQUIVO
# -------------------------------
st.sidebar.header("Escolher arquivo CSV")
arquivo = st.sidebar.file_uploader("Upload CSV", type=['csv'])

if arquivo:
    df = carregar_dados(arquivo)
    st.title("Chamados NMC Enterprise")

    # -------------------------------
    # Filtros - Sidebar
    # -------------------------------
    st.sidebar.header("Filtros")
    opcoes_graficos = ['Reclamação', 'Diagnóstico', 'Fechado por', 'Status']
    graficos_selecionados = st.sidebar.multiselect("Selecione os gráficos:", 
                                                   opcoes_graficos, 
                                                   default=opcoes_graficos)

    # -------------------------------
    # MÉTRICAS RÁPIDAS
    # -------------------------------
    col1, col2, col3, col4 = st.columns(4)
    if 'Status' in df.columns:
        col1.metric("Chamados abertos", len(df[df['Status']=='Aberto']))
        col2.metric("Chamados fechados", len(df[df['Status']=='Fechado']))
        col3.metric("Total de Chamados", len(df))
        if 'Tempo Atendimento (min)' in df.columns:
            tempo_medio = df['Tempo Atendimento (min)'].dropna().mean()
            col4.metric("Tempo médio em min por chamado (Fechados)", f"{tempo_medio:.1f}")

    # -------------------------------
    # GRÁFICOS
    # -------------------------------
    for grafico in graficos_selecionados:
        if grafico in df.columns and not df.empty:
            st.subheader(f"{grafico}")
            plot_bar_horizontal(df[grafico], grafico, grafico)

    # -------------------------------
    # TABELA DETALHADA
    # -------------------------------
    st.subheader("Detalhes dos Chamados")
    colunas_tabela = [c for c in df.columns if c.lower() != 'histórico']
    st.dataframe(df[colunas_tabela])

else:
    st.info("Por favor, faça o upload de um arquivo CSV para visualizar o dashboard.")

