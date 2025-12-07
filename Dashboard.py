import pandas as pd
import xlsxwriter
from io import BytesIO

# Suponha que df_filtrado seja seu DataFrame já preparado
# Exemplo de df_filtrado:
# df_filtrado = pd.read_csv("seu_arquivo.csv", sep=";", encoding="latin1")

def criar_excel_dashboard(df_filtrado):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Escreve os dados brutos
        df_filtrado.to_excel(writer, sheet_name='Dados', index=False)

        workbook  = writer.book
        dashboard = workbook.add_worksheet('Dashboard')

        # Estilos
        header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#4F81BD'})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})

        # Adiciona título
        dashboard.write('A1', 'Dashboard Chamados NMC Enterprise', title_format)

        # -----------------------
        # Gráfico 1: Top 10 Reclamações
        # -----------------------
        if 'Reclamação' in df_filtrado.columns:
            top_reclamacao = df_filtrado['Reclamação'].value_counts().head(10)
            chart1 = workbook.add_chart({'type': 'column'})
            chart1.add_series({
                'name':       'Top 10 Reclamações',
                'categories': ['Dados', 1, df_filtrado.columns.get_loc('Reclamação'), len(top_reclamacao), df_filtrado.columns.get_loc('Reclamação')],
                'values':     ['Dados', 1, df_filtrado.columns.get_loc('Reclamação'), len(top_reclamacao), df_filtrado.columns.get_loc('Reclamação')],
                'data_labels': {'value': True}
            })
            chart1.set_title({'name': 'Top 10 Reclamações'})
            chart1.set_style(11)
            dashboard.insert_chart('B3', chart1, {'x_scale': 1.5, 'y_scale': 1.5})

        # -----------------------
        # Gráfico 2: Top 10 Diagnósticos
        # -----------------------
        if 'Diagnóstico' in df_filtrado.columns:
            top_diag = df_filtrado['Diagnóstico'].value_counts().head(10)
            chart2 = workbook.add_chart({'type': 'column'})
            chart2.add_series({
                'name': 'Top 10 Diagnósticos',
                'categories': list(top_diag.index),
                'values': list(top_diag.values),
                'data_labels': {'value': True}
            })
            chart2.set_title({'name': 'Top 10 Diagnósticos'})
            chart2.set_style(11)
            dashboard.insert_chart('B20', chart2, {'x_scale': 1.5, 'y_scale': 1.5})

        # -----------------------
        # Gráfico 3: Chamados fechados por responsável
        # -----------------------
        if 'Fechado por' in df_filtrado.columns:
            top_fechado = df_filtrado['Fechado por'].value_counts().head(10)
            chart3 = workbook.add_chart({'type': 'column'})
            chart3.add_series({
                'name': 'Chamados fechados por responsável',
                'categories': list(top_fechado.index),
                'values': list(top_fechado.values),
                'data_labels': {'value': True}
            })
            chart3.set_title({'name': 'Chamados fechados por responsável'})
            chart3.set_style(11)
            dashboard.insert_chart('B37', chart3, {'x_scale': 1.5, 'y_scale': 1.5})

        writer.save()
        processed_data = output.getvalue()
    return processed_data

# Para Streamlit
# st.download_button(
#     label="📥 Baixar Dashboard Excel",
#     data=criar_excel_dashboard(df_filtrado),
#     file_name="Dashboard_Chamados.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )
