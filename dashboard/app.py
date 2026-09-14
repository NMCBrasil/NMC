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

# Regras confiáveis
rules = {
    "hostname": ("Hostname divergente", "Pode afetar SNMP/logs", "Padronizar nomenclatura"),
    "ip address": ("Endereço IP diferente", "Pode impactar gestão/NTP/TACACS", "Alinhar IPs de Loopback/VLAN"),
    "ntp server": ("Configuração NTP divergente", "Logs podem ficar fora de sincronismo", "Configurar NTP em ambos"),
    "vlan": ("Configuração de VLAN diferente", "Pode afetar comunicação entre redes", "Uniformizar VLANs críticas"),
    "access-list": ("ACL diferente", "Pode afetar regras de firewall", "Revisar políticas de segurança"),
    "crypto": ("Configuração de criptografia diferente", "Pode afetar VPN/segurança", "Padronizar certificados/chaves"),
    "ip route": ("Rotas diferentes", "Pode afetar conectividade", "Alinhar tabela de rotas"),
    "line con": ("Configuração de console diferente", "Acesso administrativo pode variar", "Padronizar senha e AAA"),
}

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
                observacao, impacto, sugestao = ("Configuração diferente", "", "")
                for key, val in rules.items():
                    if key in line1 or key in line2:
                        observacao, impacto, sugestao = val
                        break

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
            st.dataframe(df, use_container_width=True)
        else:
            st.info("As configurações são muito semelhantes. Ainda assim, verifique hostname, IPs, VLANs, NTP e AAA para garantir padronização.")
else:
    st.warning("⚠️ É necessário pelo menos dois arquivos .txt para comparar.")
