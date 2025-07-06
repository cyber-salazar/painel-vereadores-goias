import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import unicodedata

# ====== Configuração do título e preview do app ======
st.set_page_config(
    page_title="Painel de Vereadores em Goiás",
    page_icon="📊",
    layout="wide"
)
# ========= Função para normalizar texto =========
def normalizar(texto):
    if pd.isna(texto):
        return ""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8").lower()

# ========= Carrega os dados =========
df = pd.read_csv("vereadores_go_2004_2024.csv")
df["municipio_normalizado"] = df["municipio"].apply(normalizar)

# ========= Opções únicas =========
anos = sorted(df["ano"].unique())
estados = sorted(df["estado"].dropna().unique())
partidos = sorted(df["partido"].dropna().unique())
situacoes = sorted(df["situacao"].dropna().unique())

# Mapeia municípios normalizados para o nome com acento mais comum
municipios_dict = df.drop_duplicates(subset="municipio_normalizado")\
    .set_index("municipio_normalizado")["municipio"].to_dict()
municipios_opcoes = list(municipios_dict.values())

# ========= Limpar Filtros =========
if "limpar" not in st.session_state:
    st.session_state["limpar"] = False

if st.button("🔄 Limpar Filtros"):
    st.session_state["limpar"] = True
    st.rerun()

# ========= Formulário de Filtros (sem Estado) =========
with st.form(key="filtros_form"):
    col1, col2 = st.columns(2)
    ano_sel = col1.multiselect("Ano", anos, key="ano_sel", default=[] if st.session_state["limpar"] else None)
    partido_sel = col2.multiselect("Partido", partidos, key="partido_sel", default=[] if st.session_state["limpar"] else None)

    col3, col4 = st.columns(2)
    mun_sel_display = col3.multiselect("Município", municipios_opcoes, key="mun_sel", default=[] if st.session_state["limpar"] else None)
    situacao_sel = col4.multiselect("Situação", situacoes, key="situacao_sel", default=[] if st.session_state["limpar"] else None)

    aplicar = st.form_submit_button("✅ Aplicar Filtros")

st.session_state["limpar"] = False

# ========= Filtro Aplicado (com estado fixo) =========
df_filtrado = df.copy()
df_filtrado = df_filtrado[df_filtrado["estado"] == "GO"]

if "ano_sel" in st.session_state and st.session_state["ano_sel"]:
    df_filtrado = df_filtrado[df_filtrado["ano"].isin(st.session_state["ano_sel"])]
if "mun_sel" in st.session_state and st.session_state["mun_sel"]:
    mun_sel_norm = [normalizar(m) for m in st.session_state["mun_sel"]]
    df_filtrado = df_filtrado[df_filtrado["municipio_normalizado"].isin(mun_sel_norm)]
if "partido_sel" in st.session_state and st.session_state["partido_sel"]:
    df_filtrado = df_filtrado[df_filtrado["partido"].isin(st.session_state["partido_sel"])]
if "situacao_sel" in st.session_state and st.session_state["situacao_sel"]:
    df_filtrado = df_filtrado[df_filtrado["situacao"].isin(st.session_state["situacao_sel"])]


# ========= Título =========
st.title(":bar_chart: Vereadores – Goiás (2004–2024)")

# ========= Tabela 1: Candidatos =========
st.subheader(":clipboard: Lista de Candidatos Filtrados")
st.dataframe(df_filtrado.reset_index(drop=True))

excel_1 = BytesIO()
df_filtrado.to_excel(excel_1, index=False, sheet_name="Candidatos")
excel_1.seek(0)
st.download_button("⬇️ Baixar Candidatos", data=excel_1.getvalue(),
                   file_name="candidatos_filtrados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ========= Tabela 2: Votos por Candidato =========
st.subheader(":bust_in_silhouette: Votos por Candidato")
votos_vereador = df_filtrado.groupby(["ano", "municipio", "nome"])["votos"].sum().reset_index()
votos_vereador = votos_vereador.sort_values(by="votos", ascending=False)
st.dataframe(votos_vereador.reset_index(drop=True))

excel_2 = BytesIO()
votos_vereador.to_excel(excel_2, index=False, sheet_name="Votos por Candidato")
excel_2.seek(0)
st.download_button("⬇️ Baixar Votos por Candidato", data=excel_2.getvalue(),
                   file_name="votos_por_candidato.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Gráfico com ajustes visuais no eixo Y
chart_v = alt.Chart(votos_vereador.head(20)).mark_bar().encode(
    x=alt.X("votos:Q", title="Votos"),
    y=alt.Y("nome:N",
            sort="-x",
            axis=alt.Axis(labelLimit=300, labelFontSize=13, title="Candidato",titlePadding=60)),
    color=alt.Color("ano:N", legend=alt.Legend(title="Ano")),
    tooltip=["ano", "municipio", "nome", "votos"]
).properties(height=600, title="Top 20 Candidatos com Mais Votos")
st.altair_chart(chart_v, use_container_width=True)


# ========= Tabela 3: Votos por Partido =========
st.subheader(":classical_building: Votos por Partido")
votos_partido = df_filtrado.groupby(["ano", "partido"])["votos"].sum().reset_index()
votos_partido = votos_partido.sort_values(by="votos", ascending=False)
st.dataframe(votos_partido.reset_index(drop=True))

excel_3 = BytesIO()
votos_partido.to_excel(excel_3, index=False, sheet_name="Votos por Partido")
excel_3.seek(0)
st.download_button("⬇️ Baixar Votos por Partido", data=excel_3.getvalue(),
                   file_name="votos_por_partido.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Gráfico com nomes visíveis no eixo Y
chart_p = alt.Chart(votos_partido.head(20)).mark_bar().encode(
    x=alt.X("votos:Q", title="Votos"),
    y=alt.Y("partido:N",
            sort="-x",
            axis=alt.Axis(labelLimit=300, labelFontSize=13, title="Partido")),
    color=alt.Color("ano:N", legend=alt.Legend(title="Ano")),
    tooltip=["ano", "partido", "votos"]
).properties(height=600, title="Votos por Partido")
st.altair_chart(chart_p, use_container_width=True)