import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import unicodedata

# ====== Configuração da página ======
st.set_page_config(page_title="Painel de Vereadores em Goiás",
                   page_icon="📊",
                   layout="wide")

# ========= Função auxiliar =========
def normalizar(texto: str) -> str:
    if pd.isna(texto):
        return ""
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8").lower()

# ========= Carregamento de dados =========
df = pd.read_csv("vereadores_go_2004_2024.csv")
df["municipio_normalizado"] = df["municipio"].apply(normalizar)

# ========= Valores únicos para filtros =========
anos       = ["Todos"] + sorted(df["ano"].unique().tolist())
partidos   = ["Todos"] + sorted(df["partido"].dropna().unique().tolist())
situacoes  = ["Todos"] + sorted(df["situacao"].dropna().unique().tolist())
municipios = ["Todos"] + df.drop_duplicates("municipio_normalizado")["municipio"].tolist()

# ========= Chaves únicas dos widgets =========
KEYS = {
    "ano":        "filtro_ano",
    "partido":    "filtro_partido",
    "municipio":  "filtro_municipio",
    "situacao":   "filtro_situacao",
}

# ========= Botão Limpar Filtros =========
if st.button("🔄 Limpar Filtros"):
    for k in KEYS.values():
        st.session_state[k] = []
    st.rerun()

# ========= Formulário de filtros =========
with st.form("filtros_form"):
    c1, c2 = st.columns(2)
    ano_sel = c1.multiselect("Ano", anos,
                             key=KEYS["ano"],
                             placeholder="Selecione o(s) ano(s)")
    partido_sel = c2.multiselect("Partido", partidos,
                                 key=KEYS["partido"],
                                 placeholder="Selecione partido(s)")

    c3, c4 = st.columns(2)
    municipio_sel = c3.multiselect("Município", municipios,
                                   key=KEYS["municipio"],
                                   placeholder="Selecione município(s)")
    situacao_sel = c4.multiselect("Situação*", situacoes,
                                  key=KEYS["situacao"],
                                  placeholder="Selecione situação(ões)")

    aplicar = st.form_submit_button("✅ Aplicar Filtros")

# ========= Nota sobre Situação =========
st.caption("*Nota: em 2004 e 2008 os eleitos apareciam como 'Média' ou 'Eleito'. A partir de 2012 os rótulos mudaram para 'Eleito por QP' e 'Eleito por média'.")

# ========= Aplicação dos filtros =========
if aplicar:
    df_filtrado = df[df["estado"] == "GO"].copy()

    if ano_sel and "Todos" not in ano_sel:
        df_filtrado = df_filtrado[df_filtrado["ano"].isin(ano_sel)]
    if municipio_sel and "Todos" not in municipio_sel:
        mun_norm = [normalizar(m) for m in municipio_sel]
        df_filtrado = df_filtrado[df_filtrado["municipio_normalizado"].isin(mun_norm)]
    if partido_sel and "Todos" not in partido_sel:
        df_filtrado = df_filtrado[df_filtrado["partido"].isin(partido_sel)]
    if situacao_sel and "Todos" not in situacao_sel:
        df_filtrado = df_filtrado[df_filtrado["situacao"].isin(situacao_sel)]

    st.title(":bar_chart: Vereadores – Goiás (2004–2024)")

    df_exibicao = df_filtrado.drop(columns=["municipio_normalizado"], errors="ignore")

    st.subheader(":clipboard: Candidatos filtrados")
    st.dataframe(df_exibicao.reset_index(drop=True))

    buf = BytesIO()
    df_exibicao.to_excel(buf, index=False, sheet_name="Candidatos")

    st.download_button("⬇️ Baixar candidatos", buf.getvalue(),
                       "candidatos_filtrados.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader(":bust_in_silhouette: Votos por candidato")
    votos_cand = (df_filtrado
                  .groupby(["ano", "municipio", "nome"])["votos"]
                  .sum()
                  .reset_index()
                  .sort_values("votos", ascending=False))
    st.dataframe(votos_cand)

    buf2 = BytesIO()
    votos_cand.to_excel(buf2, index=False, sheet_name="Votos_Candidato")
    st.download_button("⬇️ Baixar votos/candidato", buf2.getvalue(),
                       "votos_por_candidato.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    top_candidatos = votos_cand.head(20)
    altura = min(max(len(top_candidatos) * 40, 400), 1000)

    chart_c = alt.Chart(top_candidatos).mark_bar().encode(
        x="votos:Q",
        y=alt.Y("nome:N", sort="-x"),
        color="ano:N",
        tooltip=["ano", "municipio", "nome", "votos"]
    ).properties(height=altura, title="Top 20 candidatos mais votados")

    st.altair_chart(chart_c, use_container_width=True)

    st.subheader(":classical_building: Votos por partido")
    votos_part = (df_filtrado
                  .groupby(["ano", "partido"])["votos"]
                  .sum()
                  .reset_index()
                  .sort_values("votos", ascending=False))
    st.dataframe(votos_part)

    buf3 = BytesIO()
    votos_part.to_excel(buf3, index=False, sheet_name="Votos_Partido")
    st.download_button("⬇️ Baixar votos/partido", buf3.getvalue(),
                       "votos_por_partido.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    top_partidos = votos_part.head(20)
    altura_partidos = min(max(len(top_partidos) * 40, 400), 1000)

    chart_p = alt.Chart(top_partidos).mark_bar().encode(
        x="votos:Q",
        y=alt.Y("partido:N", sort="-x"),
        color="ano:N",
        tooltip=["ano", "partido", "votos"]
    ).properties(height=altura_partidos, title="Top 20 partidos mais votados")

    st.altair_chart(chart_p, use_container_width=True)
