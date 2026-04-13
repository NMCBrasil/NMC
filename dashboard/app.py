def delete_row(row_id):
    try:
        supabase.table("registros").delete().eq("id", int(row_id)).execute()
        st.toast("Registro excluído com sucesso!")
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")


st.header("📋 Dados detalhados")

for _, row in filtered.iterrows():

    row_id = row.get("id")

    # segurança: ignora linhas sem ID
    if pd.isna(row_id):
        continue

    c1, c2, c3, c4, c5 = st.columns([1,2,2,2,1])

    c1.write(f"🆔 {row_id}")
    c2.write(f"📅 {row.get('mes','')}")
    c3.write(f"📡 {row.get('operadora','')}")
    c4.write(f"🔌 {row.get('circuit', row.get('circuito','N/A'))}")
    c5.write(f"💰 {row.get('desconto',0)}")

    # 🔥 BOTÃO FORTE E ESTÁVEL
    if st.button("🗑️ Excluir", key=str(row_id)):
        delete_row(row_id)
        st.rerun()
