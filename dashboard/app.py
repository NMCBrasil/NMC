import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="Comparador de Configurações", layout="wide")
st.title("🔎 Comparador de Configurações de Equipamentos")

CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

# Upload de arquivos
uploaded_files = st.file_uploader("Carregar arquivos .txt", type=["txt"], accept_multiple_files=True)
if uploaded_files:
    for file in uploaded_files:
        with open(os.path.join(CONFIG_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())
    st.success("Arquivos salvos em 'configs/'")

# Lista arquivos disponíveis
files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".txt")]
if len(files) >= 2:
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.selectbox("Device 1", files)
    with col2:
        file2 = st.selectbox("Device 2", files)

    if st.button("Comparar"):
        c1 = open(os.path.join(CONFIG_DIR, file1)).read().splitlines()
        c2 = open(os.path.join(CONFIG_DIR, file2)).read().splitlines()
        max_len = max(len(c1), len(c2))

        resumo = []
        for i in range(max_len):
            line1 = c1[i] if i < len(c1) else ""
            line2 = c2[i] if i < len(c2) else ""
            if line1 != line2:
                observacao = "Configuração diferente"
                impacto = ""
                sugestao = ""

                # Regras simples de análise automática
                if "hostname" in line1 or "hostname" in line2:
                    observacao = "Hostname divergente"
                    impacto = "Pode afetar SNMP/logs"
                    sugestao = "Padronizar nomenclatura"
                elif "ip address" in line1 or "ip address" in line2:
                    observacao = "Endereço IP diferente"
                    impacto = "Pode impactar gestão/NTP/TACACS"
                    sugestao = "Alinhar IPs de Loopback/VLAN"
                elif "ntp server" in line1 or "ntp server" in line2:
                    observacao = "Configuração NTP divergente"
                    impacto = "Logs podem ficar fora de sincronismo"
                    sugestao = "Configurar NTP em ambos"
                elif "vlan" in line1 or "vlan" in line2:
                    observacao = "Configuração de VLAN diferente"
                    impacto = "Pode afetar comunicação entre redes"
                    sugestao = "Uniformizar VLANs críticas"
                elif "line con" in line1 or "line con" in line2:
                    observacao = "Configuração de console diferente"
                    impacto = "Acesso administrativo pode variar"
                    sugestao = "Padronizar senha e AAA"

                resumo.append({
                    "Linha": i+1,
                    "Device 1": line1,
                    "Device 2": line2,
                    "Observação": observacao,
                    "Impacto": impacto,
                    "Sugestão": sugestao
                })

        st.subheader("🤖 Relatório Inteligente")
        if resumo:
            df = pd.DataFrame(resumo)
            st.dataframe(df)
        else:
            # Mesmo sem diferenças linha a linha, sempre mostrar pontos de atenção
            st.info("As configurações são muito semelhantes. Ainda assim, verifique:")
            st.write("- Hostname e IP de Loopback")
            st.write("- VLANs atribuídas em interfaces críticas")
            st.write("- Configuração de NTP (presente em um, ausente em outro)")
            st.write("- Senha de console e AAA")
            st.write("Sugestão: alinhar esses pontos para evitar falhas em backup/comutação.")
else:
    st.warning("⚠️ É necessário pelo menos dois arquivos .txt para comparar.")
