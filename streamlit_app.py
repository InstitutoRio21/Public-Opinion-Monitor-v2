import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Percepção", layout="wide")

PERCEPTION_COLS = ["Saúde", "Conservação Urbana e Patrimonial", "Educação", "Preservação Ambiental", "Assistência Social", "Transportes"]
PROFILE_COLS = ["Sexo", "Faixa etária", "Cor/raça", "Escolaridade", "Ocupação", "Renda familiar (SM)", "Zona"]
ORDER_AVAL = ["Ótima", "Boa", "Regular", "Ruim", "Péssima"]
COLOR_MAP = {"Ótima": "#2ca02c", "Boa": "#98df8a", "Regular": "#ffdd57", "Ruim": "#ff7f0e", "Péssima": "#d62728"}
CAT_MAP = {"Ótima": "Ótima/Boa", "Boa": "Ótima/Boa", "Regular": "Regular", "Ruim": "Ruim/Péssima", "Péssima": "Ruim/Péssima"}
BAR_COLOR = "#1f77b4"

EDITION_MONTH = {
    1: "08/2021",
    2: "11/2021",
    3: "03/2022",
    4: "07/2022",
    5: "11/2022",
    6: "03/2023",
    7: "07/2023",
    8: "11/2023",
    9: "03/2024",
    10: "07/2024",
    11: "11/2024",
    12: "03/2025",
    13: "07/2025",
    14: "11/2025",
    15: "03/2026",
    16: "07/2026"
}

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    excel = pd.ExcelFile(path)
    df = None

    required_cols = {"Mês/Ano", "Edição", "peso"}

    for sheet in excel.sheet_names:
        temp = pd.read_excel(path, sheet_name=sheet)
        temp.columns = temp.columns.astype(str).str.strip()

        if "Edição" in temp.columns and any(col in temp.columns for col in PERCEPTION_COLS):
            df = temp
            break

    if df is None:
        df = pd.read_excel(path)
        df.columns = df.columns.astype(str).str.strip()

    if "Mês/Ano" not in df.columns:
        if "Edição" in df.columns:
            df["Mês/Ano"] = df["Edição"].map(EDITION_MONTH)
        else:
            return df

    df = df[df["Mês/Ano"].astype(str).str.strip() != "Carimbo de data/hora"].copy()

    def converter_data(valor):
        if pd.isna(valor):
            return pd.NaT

        if isinstance(valor, pd.Timestamp):
            return valor.to_period("M").to_timestamp()

        texto = str(valor).strip()

        if not texto or texto.lower() in ["nan", "nat", "none"]:
            return pd.NaT

        for formato in ["%m/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            data = pd.to_datetime(texto, format=formato, errors="coerce")
            if pd.notna(data):
                return data.to_period("M").to_timestamp()

        data = pd.to_datetime(texto, dayfirst=True, errors="coerce")

        if pd.notna(data):
            return data.to_period("M").to_timestamp()

        return pd.NaT

    df["Mês/Ano"] = df["Mês/Ano"].apply(converter_data)

    if df["Mês/Ano"].isna().all() and "Edição" in df.columns:
        df["Mês/Ano"] = df["Edição"].map(EDITION_MONTH)
        df["Mês/Ano"] = pd.to_datetime(df["Mês/Ano"], format="%m/%Y", errors="coerce")

    df.loc[df["Mês/Ano"].isin([pd.Timestamp("2026-07-01"), pd.Timestamp("2026-08-01")]), "Mês/Ano"] = pd.Timestamp("2026-07-01")
    df.loc[df["Mês/Ano"].isin([pd.Timestamp("2026-03-01"), pd.Timestamp("2026-04-01")]), "Mês/Ano"] = pd.Timestamp("2026-03-01")
    df.loc[df["Mês/Ano"].isin([pd.Timestamp("2024-10-01"), pd.Timestamp("2024-11-01")]), "Mês/Ano"] = pd.Timestamp("2024-11-01")
    df.loc[df["Mês/Ano"].isin([pd.Timestamp("2023-06-01"), pd.Timestamp("2023-07-01")]), "Mês/Ano"] = pd.Timestamp("2023-07-01")

    return df

def getPercents(df, colunas):
    df = df.dropna(subset=["peso"]).copy()
    variaveis = [c for c in colunas if c != "peso"]

    if len(variaveis) == 1:
        variavel = variaveis[0]
        resultado = df.groupby(variavel)["peso"].sum().reset_index(name="freq_ponderada")
        resultado["percent"] = resultado["freq_ponderada"] / resultado["freq_ponderada"].sum() * 100
        return resultado

    if len(variaveis) == 2:
        variavel_1, variavel_2 = variaveis
        resultado = df.groupby([variavel_1, variavel_2])["peso"].sum().reset_index(name="freq_ponderada")
        total = resultado.groupby(variavel_1)["freq_ponderada"].sum().reset_index(name="total")
        resultado = resultado.merge(total, on=variavel_1, how="left")
        resultado["percent"] = resultado["freq_ponderada"] / resultado["total"] * 100
        return resultado

    if len(variaveis) == 3:
        variavel_1, variavel_2, variavel_3 = variaveis
        resultado = df.groupby([variavel_1, variavel_2, variavel_3])["peso"].sum().reset_index(name="freq_ponderada")
        total = resultado.groupby([variavel_1, variavel_3])["freq_ponderada"].sum().reset_index(name="total")
        resultado = resultado.merge(total, on=[variavel_1, variavel_3], how="left")
        resultado["percent"] = resultado["freq_ponderada"] / resultado["total"] * 100
        return resultado

    raise ValueError("Selecione entre 1 e 3 variáveis.")

DATA_PATH = "data/Base_de_Dados_Pesquisa_Gestao_Municipal_ponderada.xlsx"
df_raw = load_data(DATA_PATH)

if df_raw.empty:
    st.error("A base foi carregada, mas não possui nenhuma linha.")
    st.stop()

if "peso" not in df_raw.columns:
    st.error("A base não possui a coluna 'peso'. Use a base ponderada.")
    st.stop()

st.sidebar.image("img/logo_rio21.png", use_container_width=True)
st.sidebar.title("Filtros globais")

months_sorted = sorted(df_raw["Mês/Ano"].dropna().unique())

if months_sorted:
    month_options = [pd.Timestamp(d).strftime("%m/%Y") for d in months_sorted]
    month_selected = st.sidebar.selectbox("Selecione o mês (mm/aaaa)", options=month_options, index=len(month_options) - 1)
    month_dt = pd.to_datetime(month_selected, format="%m/%Y")
else:
    st.sidebar.error("Não foi possível identificar os meses da base.")
    st.sidebar.write("Coluna Mês/Ano:", df_raw["Mês/Ano"].head().tolist())
    st.sidebar.write("Edições:", df_raw["Edição"].dropna().unique().tolist() if "Edição" in df_raw.columns else "Não encontrada")
    month_selected = None
    month_dt = None

filters = {}

with st.sidebar.expander("Filtros de perfil", expanded=False):
    st.markdown("Selecione valores específicos de perfil para refinar as visualizações de todas as abas.")

    for col in PROFILE_COLS:
        if col not in df_raw.columns:
            continue

        options = sorted(df_raw[col].dropna().unique(), key=lambda x: str(x))

        if options:
            selected = st.multiselect(col, options=options, default=options, key=f"flt_{col}")
            filters[col] = selected
        else:
            filters[col] = []

st.sidebar.caption("Desenvolvido pelo Instituto Rio21. Conheça mais o nosso trabalho: rio21.org.")

def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    if month_dt is not None:
        df = df[df["Mês/Ano"] == month_dt]

    for col, sel in filters.items():
        if col in df.columns and sel:
            df = df[df[col].isin(sel)]

    return df

_df = apply_filters(df_raw)

TAB_TITLES = ["💡Apresentação", "📊Painel geral de acompanhamento", "📈Painel temporal", "👥Perfil da amostra", "🔍Cruzamentos de variáveis", "📥Download da base"]
tabs = st.tabs(TAB_TITLES)

with tabs[0]:
    st.header("Apresentação e instruções de uso")

    st.markdown("""
Este dashboard interativo apresenta os principais resultados das
pesquisas de percepção da população carioca sobre serviços públicos
realizada periodicamente pelo Instituto Rio21 em parceria com o
Diário do Rio.

As informações são coletadas por meio de entrevistas *online* com 
uma amostra da população do município do Rio de Janeiro. Os dados 
passam por tratamento estatístico, com **ponderação por sexo, faixa 
etária e cor/raça**, utilizando como referência a distribuição da 
população segundo o **Censo Demográfico 2022 do IBGE**. 
Esse procedimento ajusta a composição da amostra em relação à população 
de referência, e os percentuais apresentados consideram esses pesos estatísticos.


**Como navegar:**

1. **Painel geral de acompanhamento** – distribuição das avaliações por área em um mês específico.
2. **Painel temporal** – evolução das avaliações agrupadas em três categorias.
3. **Perfil da amostra** – composição sociodemográfica dos entrevistados.
4. **Cruzamentos de variáveis** – crie tabelas e gráficos de frequência/percentual a partir de até três variáveis simultâneas.
5. **Download da base** – visualize e baixe o banco de dados completo em CSV.

A qualquer momento, use a barra lateral para filtrar **mês** e/ou qualquer variável de **perfil**.

Esses filtros afetam todas as abas (exceto *Download*, que sempre mostra a base integral).
""")

with tabs[1]:
    st.header("Painel geral de acompanhamento")

    st.markdown("""
Visualize a **distribuição percentual** das avaliações para cada
área da administração.

*Escolha o mês desejado* no menu lateral ou mantenha o último mês
para visão atual.

→ É útil para detectar rapidamente quais áreas têm melhor ou pior
percepção no período selecionado.
""")

    df_month = _df[_df["Mês/Ano"] == month_dt] if month_dt is not None else pd.DataFrame()

    if df_month.empty:
        st.warning("Não há registros para a combinação de filtros selecionada.")
    else:
        df_long = df_month.melt(id_vars=["peso"], value_vars=PERCEPTION_COLS, var_name="Área", value_name="Avaliação").dropna(subset=["Avaliação", "peso"])
        df_long["Avaliação"] = pd.Categorical(df_long["Avaliação"].astype("string").str.strip(), categories=ORDER_AVAL, ordered=True)

        counts = df_long.groupby(["Área", "Avaliação"], observed=True)["peso"].sum().reset_index(name="freq_ponderada")
        counts["percent"] = counts["freq_ponderada"] / counts.groupby("Área")["freq_ponderada"].transform("sum") * 100

        fig = px.bar(counts, x="percent", y="Área", color="Avaliação", orientation="h", text_auto=".1f", labels={"percent": "%"}, category_orders={"Avaliação": ORDER_AVAL}, color_discrete_map=COLOR_MAP)
        fig.update_layout(barmode="stack", xaxis_title="Percentual", yaxis_title="Área", template="simple_white")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")

        st.plotly_chart(fig, use_container_width=True, key="grafico_painel_geral")

with tabs[2]:
    st.header("Painel temporal")

    st.markdown("""
Acompanhe a **tendência** das avaliações desde agosto de 2021.

São exibidos três gráficos:

**Ótima/Boa**, **Regular** e **Ruim/Péssima**.
""")

    df_temporal = df_raw.copy()
    df_long = df_temporal.melt(id_vars=["Mês/Ano", "peso"], value_vars=PERCEPTION_COLS, var_name="Área", value_name="Avaliação")
    df_long["Avaliação"] = df_long["Avaliação"].astype("string").str.strip()
    df_long["Categoria"] = df_long["Avaliação"].map(CAT_MAP)
    df_long = df_long.dropna(subset=["Categoria", "peso"])

    series = df_long.groupby(["Mês/Ano", "Área", "Categoria"], observed=True)["peso"].sum().reset_index(name="freq_ponderada")
    series["percent"] = series["freq_ponderada"] / series.groupby(["Mês/Ano", "Área"])["freq_ponderada"].transform("sum") * 100
    series = series.sort_values("Mês/Ano")

    for cat in ["Ótima/Boa", "Regular", "Ruim/Péssima"]:
        st.subheader(f"Evolução – {cat}")

        sub = series[series["Categoria"] == cat]

        fig = px.line(sub, x="Mês/Ano", y="percent", color="Área", markers=True, labels={"percent": "%", "Mês/Ano": "Mês"})
        fig.update_layout(yaxis_title="Percentual", xaxis_title="Mês/Ano", template="simple_white")
        fig.update_yaxes(range=[0, 100], ticksuffix="%")

        st.plotly_chart(fig, use_container_width=True, key=f"grafico_temporal_{cat}")

with tabs[3]:
    st.header("Painel de acompanhamento do perfil da amostra")

    st.markdown("""
Veja a **composição da amostra** para cada variável
sociodemográfica, no mês selecionado.
""")

    df_month = _df[_df["Mês/Ano"] == month_dt] if month_dt is not None else pd.DataFrame()

    if df_month.empty:
        st.warning("Não há registros para a combinação de filtros selecionada.")
    else:
        for i, col in enumerate(PROFILE_COLS):
            if i % 3 == 0:
                cols_row = st.columns(3, gap="large")

            with cols_row[i % 3]:
                st.subheader(col)

                counts = getPercents(df_month, [col, "peso"]).sort_values("percent", ascending=True)

                fig = px.bar(counts, x="percent", y=col, orientation="h", text="percent", labels={"percent": "%"}, color_discrete_sequence=[BAR_COLOR])

                fig.update_traces(texttemplate="%{x:.1f}%", textposition="inside", insidetextanchor="middle", marker_line_color="white", marker_line_width=0.5, hovertemplate="<b>%{y}</b><br>Percentual: %{x:.1f}%<extra></extra>")
                fig.update_layout(template="simple_white", xaxis_title="Percentual", yaxis_title="", yaxis=dict(categoryorder="total ascending"), bargap=0.2, margin=dict(l=0, r=0, t=0, b=0))
                fig.update_xaxes(ticksuffix="%", showgrid=False, range=[0, 100])
                fig.update_yaxes(showgrid=False)

                st.plotly_chart(fig, use_container_width=True, key=f"grafico_perfil_{col}")

with tabs[4]:
    st.header("Cruzamentos de variáveis")

    st.markdown("""

    Crie tabelas e gráficos frequência/percentual com até três variáveis simultâneas.

– **1 variável**: frequência global.

– **2 variáveis**: distribuição dentro de cada nível da primeira variável.

– **3 variáveis**: mesmo princípio, com facetas para a terceira variável.
""")

    vars_available = [c for c in df_raw.columns if c not in ["Mês/Ano", "peso"]]

    sel_vars = st.multiselect("Selecione até 3 variáveis para cruzar", options=vars_available, help="É possível selecionar de 1 a 3 variáveis", max_selections=3)

    if sel_vars:
        cross = getPercents(_df, sel_vars + ["peso"])
        st.dataframe(cross, use_container_width=True, height=400)

        metric = "percent"
        text_fmt = "%{x:.1f}%"
        common_args = dict(x=metric, orientation="h", text=metric, labels={metric: "%"})

        if len(sel_vars) == 1:
            fig = px.bar(cross, y=sel_vars[0], color_discrete_sequence=[BAR_COLOR], **common_args)

        elif len(sel_vars) == 2:
            fig = px.bar(cross, y=sel_vars[0], color=sel_vars[1], barmode="stack", **common_args)

        else:
            facets = cross[sel_vars[2]].unique()
            n_facets = len(facets)
            cols_wrap = 2
            rows = (n_facets + cols_wrap - 1) // cols_wrap

            fig = px.bar(cross, y=sel_vars[0], color=sel_vars[1], facet_col=sel_vars[2], facet_col_wrap=cols_wrap, facet_row_spacing=0.12, facet_col_spacing=0.04, barmode="stack", **common_args)
            fig.update_layout(height=max(350, 250 * rows))

        fig.update_traces(texttemplate=text_fmt)
        fig.update_layout(template="simple_white", xaxis_title="Percentual", yaxis_title="")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")

        st.plotly_chart(fig, use_container_width=True, key="grafico_cruzamentos")

    else:
        st.info("Selecione pelo menos uma variável para visualizar o cruzamento.")

with tabs[5]:
    st.header("Download da base completa")

    st.markdown("""
Visualize o banco de dados completo (sem filtros)
e faça o **download em CSV** para análises adicionais.
""")

    st.dataframe(df_raw, use_container_width=True, height=500)

    csv_data = df_raw.to_csv(index=False).encode("utf-8")

    st.download_button(label="Baixar CSV", data=csv_data, file_name="base_completa.csv", mime="text/csv")