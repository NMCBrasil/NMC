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

# Fundo azul claro
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6f2ff;
    }
    .css-1d391kg {
        font-size: 1.5em;
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

    # Função para plotar gráficos no app
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

    plot_bar('Reclamação', '📊 Chamados por Reclamação')
    plot_bar('Diagnóstico', '📊 Chamados por Diagnóstico')
    plot_bar('Fechado por', '📊 Chamados por Responsável pelo Fechamento')

    # Tabela detalhada
    st.subheader("Detalhes dos chamados")
    colunas_exibir = ['Id', 'Status', 'Criado por', 'Data de abertura', 'Hora de abertura',
                      'Fechado por', 'Data de fechamento', 'Hora de fechamento', 'Cliente',
                      'Reclamação', 'Diagnóstico']
    st.dataframe(df_filtrado[colunas_exibir].sort_values(by='Data de abertura', ascending=False), use_container_width=True)

    # Função para gerar Excel completo com gráficos
    def dashboard_to_excel(df, tempo_medio, maior_ofensor, qtd_ofensor, pct_ofensor):
        import xlsxwriter

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Chamados')
            workbook = writer.book
            worksheet = writer.sheets['Chamados']

            # Ajusta largura das colunas
            for i, col in enumerate(df.columns):
                max_len = df[col].astype(str).map(len).max()
                worksheet.set_column(i, i, max(15, max_len + 2))

            # Escreve métricas no topo
            worksheet.write('M1', 'Tempo médio por chamado (min)')
            worksheet.write('N1', round(tempo_medio, 2))
            worksheet.write('M2', 'Maior ofensor')
            worksheet.write('N2', f"{maior_ofensor} ({qtd_ofensor} chamados, {pct_ofensor}%)")

            # Cria gráficos do Excel
            chart1 = workbook.add_chart({'type': 'column'})
            chart2 = workbook.add_chart({'type': 'column'})
            chart3 = workbook.add_chart({'type': 'column'})

            # Dados para gráficos
            def add_chart(chart, coluna):
                contagem = df[coluna].value_counts()
                data_start = 1  # porque linha 0 tem cabeçalho
                # Adiciona categoria e valores em colunas auxiliares temporárias
                temp_col1 = len(df.columns)
                temp_col2 = temp_col1 + 1
                for i, (k, v) in enumerate(contagem.items()):
                    worksheet.write(i+1, temp_col1, k)
                    worksheet.write(i+1, temp_col2, v)
                chart.add_series({
                    'name': coluna,
                    'categories': [worksheet.name, data_start, temp_col1, data_start + len(contagem)-1, temp_col1],
                    'values': [worksheet.name, data_start, temp_col2, data_start + len(contagem)-1, temp_col2],
                    'data_labels': {'value': True}
                })
                chart.set_title({'name': f'Chamados por {coluna}'})
                chart.set_x_axis({'name': coluna})
                chart.set_y_axis({'name': 'Quantidade'})
                chart.set_style(10)
                return chart

            chart1 = add_chart(chart1, 'Reclamação')
            chart2 = add_chart(chart2, 'Diagnóstico')
            chart3 = add_chart(chart3, 'Fechado por')

            # Posiciona gráficos no Excel
            worksheet.insert_chart('M5', chart1)
            worksheet.insert_chart('M25', chart2)
            worksheet.insert_chart('M45', chart3)

        processed_data = output.getvalue()
        return processed_data

    excel_data = dashboard_to_excel(df_filtrado, tempo_medio, maior_ofensor, qtd_ofensor, pct_ofensor)

    st.download_button(
        label="📥 Baixar dashboard completo em Excel",
        data=excel_data,
        file_name="dashboard_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Aguardando upload do arquivo CSV para exibir o dashboard.")
