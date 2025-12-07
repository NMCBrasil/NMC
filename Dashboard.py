# Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io
import plotly.io as pio
from fpdf import FPDF

# Configuração do app
st.set_page_config(
    page_title="Chamados NMC Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fundo azul claro e letras pretas
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6f2ff;
        color: black;
    }
    .stMetricLabel, .stMetricValue, .css-1v3fvcr, .css-1aumxhk {
        color: black !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Chamados NMC Enterprise")

# Função para carregar dados
@st.cache_data
def carregar_dados(file):
    df = pd.read_csv(file, encoding='latin1', sep=None, engine='python')
    df.columns = df.columns.str.strip()
    return df

# Upload do CSV
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
        st.write(f"**{maior_ofensor}** abriu **{qtd_ofensor} chamados** ({pct_ofensor}%)")

    # Tempo médio de atendimento
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

    st.metric("⏱ Tempo médio por chamado (min)", f"{tempo_medio:.2f}")

    # Função para criar gráficos
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
                color_continuous_scale='Blues'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis=dict(title="Quantidade"), xaxis=dict(title=campo))
            st.plotly_chart(fig, use_container_width=True)
            return fig
        return None

    fig_reclamacao = plot_bar('Reclamação', '📊 Chamados por Reclamação')
    fig_diagnostico = plot_bar('Diagnóstico', '📊 Chamados por Diagnóstico')
    fig_fechado_por = plot_bar('Fechado por', '📊 Chamados por Responsável pelo Fechamento')

    # Tabela detalhada
    st.subheader("Detalhes dos chamados")
    colunas_exibir = ['Id', 'Status', 'Criado por', 'Data de abertura', 'Hora de abertura',
                      'Fechado por', 'Data de fechamento', 'Hora de fechamento', 'Cliente',
                      'Reclamação', 'Diagnóstico']
    st.dataframe(df_filtrado[colunas_exibir].sort_values(by='Data de abertura', ascending=False), use_container_width=True)

    # Função para gerar PDF do dashboard
    def generate_pdf(df, tempo_medio, maior_ofensor, qtd_ofensor, pct_ofensor,
                     fig_reclamacao, fig_diagnostico, fig_fechado_por):
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Chamados NMC Enterprise", ln=True, align='C')

        # Métricas
        pdf.set_font("Arial", '', 12)
        pdf.ln(5)
        pdf.cell(0, 8, f"Tempo médio por chamado (min): {tempo_medio:.2f}", ln=True)
        pdf.cell(0, 8, f"Maior ofensor: {maior_ofensor} ({qtd_ofensor} chamados, {pct_ofensor}%)", ln=True)
        pdf.ln(5)

        # Função para adicionar gráfico Plotly como imagem
        def add_plotly_fig(fig, title):
            if fig:
                img_bytes = pio.to_image(fig, format='png', width=700, height=400, scale=2)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, title, ln=True)
                pdf.image(io.BytesIO(img_bytes), w=180)
                pdf.ln(5)

        add_plotly_fig(fig_reclamacao, "Chamados por Reclamação")
        add_plotly_fig(fig_diagnostico, "Chamados por Diagnóstico")
        add_plotly_fig(fig_fechado_por, "Chamados por Responsável pelo Fechamento")

        # Tabela
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "Detalhes dos Chamados (50 primeiras linhas)", ln=True)
        pdf.set_font("Arial", '', 10)

        # Cabeçalho da tabela
        for col in colunas_exibir:
            pdf.cell(30, 6, str(col), border=1)
        pdf.ln()
        # Dados da tabela (limite 50 linhas para caber)
        for idx, row in df[colunas_exibir].head(50).iterrows():
            for col in colunas_exibir:
                text = str(row[col])[:15]
                pdf.cell(30, 6, text, border=1)
            pdf.ln()

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return pdf_output

    pdf_data = generate_pdf(df_filtrado, tempo_medio, maior_ofensor, qtd_ofensor, pct_ofensor,
                            fig_reclamacao, fig_diagnostico, fig_fechado_por)

    st.download_button(
        label="📥 Baixar dashboard completo em PDF",
        data=pdf_data,
        file_name="dashboard_completo.pdf",
        mime="application/pdf"
    )

else:
    st.info("Aguardando upload do arquivo CSV para exibir o dashboard.")
