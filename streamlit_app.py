import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Dashboard de Percepção", layout="wide")

# -----------------------------------------------------------------------------
# Funções utilitárias
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Remove linhas que são cabeçalho repetido
    if "Mês/Ano" in df.columns:
        df = df[
            df["Mês/Ano"].astype(str).str.strip() != "Carimbo de data/hora"
        ].copy()

        # Converte mês/ano para uma data padronizada
        df["Mês/Ano"] = pd.to_datetime(
            df["Mês/Ano"],
            format="%m/%Y",
            errors="coerce"
        )

        # Remove valores inválidos
        df = df.dropna(subset=["Mês/Ano"]).copy()

        # Mantém somente mês/ano, sem diferença de dia/hora
        df["Mês/Ano"] = df["Mês/Ano"].dt.to_period("M").dt.to_timestamp()

        # Agrupa pesquisas que atravessaram dois meses
        df.loc[
            df["Mês/Ano"].isin([
                pd.Timestamp("2026-07-01"),
                pd.Timestamp("2026-08-01")
            ]),
            "Mês/Ano"
        ] = pd.Timestamp("2026-07-01")

        df.loc[
            df["Mês/Ano"].isin([
                pd.Timestamp("2026-03-01"),
                pd.Timestamp("2026-04-01")
            ]),
            "Mês/Ano"
        ] = pd.Timestamp("2026-03-01")

        df.loc[
            df["Mês/Ano"].isin([
                pd.Timestamp("2024-10-01"),
                pd.Timestamp("2024-11-01")
            ]),
            "Mês/Ano"
        ] = pd.Timestamp("2024-11-01")

        df.loc[
            df["Mês/Ano"].isin([
                pd.Timestamp("2023-06-01"),
                pd.Timestamp("2023-07-01")
            ]),
            "Mês/Ano"
        ] = pd.Timestamp("2023-07-01")

    return df
DATA_PATH = "data/AH.xlsx"
df_raw = load_data(DATA_PATH)

PERCEPTION_COLS = [
    "Saúde",
    "Conservação Urbana e Patrimonial",
    "Educação",
    "Preservação Ambiental",
    "Assistência Social",
    "Transportes",
]

PROFILE_COLS = [
    "Sexo",
    "Faixa etária",
    "Cor/raça",
    "Escolaridade",
    "Ocupação",
    "Renda familiar (SM)",
    "Zona",
]

ORDER_AVAL = ["Ótima", "Boa", "Regular", "Ruim", "Péssima"]
COLOR_MAP = {
    "Ótima": "#2ca02c",
    "Boa": "#98df8a",
    "Regular": "#ffdd57",
    "Ruim": "#ff7f0e",
    "Péssima": "#d62728",
}

CAT_MAP = {
    "Ótima": "Ótima/Boa",
    "Boa": "Ótima/Boa",
    "Regular": "Regular",
    "Ruim": "Ruim/Péssimo",
    "Péssima": "Ruim/Péssima",
}

BAR_COLOR = "#1f77b4"  # cor base para gráficos de perfil

# -----------------------------------------------------------------------------
# Sidebar – filtros
# -----------------------------------------------------------------------------

st.sidebar.image("img/logo_rio21.png", use_container_width=True)

st.sidebar.title("Filtros globais")

# Garante que cada mês apareça apenas uma vez
months_sorted = sorted(
    df_raw["Mês/Ano"].dropna().unique()
)

month_selected = st.sidebar.selectbox(
    "Selecione o mês (mm/aaaa)",
    options=[pd.Timestamp(d).strftime("%m/%Y") for d in months_sorted],
    index=len(months_sorted) - 1,
)

month_dt = pd.to_datetime(month_selected, format="%m/%Y")

filters: dict[str, list] = {}

with st.sidebar.expander("Filtros de perfil", expanded=False):
    st.markdown(
        "Selecione valores específicos de perfil para refinar as visualizações de todas as abas."
    )

    for col in PROFILE_COLS:
        # Converte tudo para texto apenas na hora de ordenar/exibir,
        # evitando o erro quando há números e textos na mesma coluna.
        options = sorted(
            df_raw[col].dropna().unique(),
            key=lambda x: str(x)
        )

        selected = st.multiselect(
            col,
            options=options,
            default=options,
            key=f"flt_{col}"
        )

        filters[col] = selected

st.sidebar.caption(
    "Desenvolvido pelo Instituto Rio21. Conheça o trabalho do Instituto Rio21: "
    "[rio21.org](https://www.rio21.org)."
)


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()

    # Filtro do mês selecionado
    df = df[df["Mês/Ano"] == month_dt]

    # Filtros de perfil
    for col, sel in filters.items():
        if sel and len(sel) < len(df[col].dropna().unique()):
            df = df[df[col].isin(sel)]

    return df


_df = apply_filters(df_raw)

# -----------------------------------------------------------------------------
# Abas principais
# -----------------------------------------------------------------------------
TAB_TITLES = [
    "💡Apresentação",
    "📊Painel geral de acompanhamento",
    "📈Painel temporal",
    "👥Perfil da amostra",
    "🔍Cruzamentos de variáveis",
    "📥Download da base",
]

tabs = st.tabs(TAB_TITLES)

# ----------------------------------------------------------------------------
# 0) Apresentação e instruções
# ----------------------------------------------------------------------------
with tabs[0]:
    st.header("Apresentação e instruções de uso")
    st.markdown(
        """
        Este dashboard interativo apresenta os principais resultados das pesquisas de percepção da população sobre serviços públicos
        realizada periodicamente pelo Instituto Rio21 em parceria com o Diário do Rio. 
        As informações são coletadas por meio de entrevistas _online_ com uma amostra da população do município do Rio de Janeiro, 
        e os dados passam por um processo de tratamento para garantir a representatividade da amostra utilizando técnicas estatísticas avançadas.

        **Como navegar:**
        1. **Painel geral de acompanhamento** – distribuição das avaliações por área em um mês específico.
        2. **Painel temporal** – evolução mensal das avaliações agrupadas em três categorias.
        3. **Perfil da amostra** – composição sociodemográfica dos entrevistados.
        4. **Cruzamentos de variáveis** – crie tabelas e gráficos de frequência/percentual a partir de até três variáveis simultâneas.
        5. **Download da base** – visualize e baixe o banco de dados completo em CSV.

        A qualquer momento, use a barra lateral para filtrar **mês** e/ou qualquer variável de **perfil**. Esses filtros afetam todas as abas (exceto _Download_, que sempre mostra a base integral).
        """
    )

# ----------------------------------------------------------------------------
# 1) Painel geral de acompanhamento
# ----------------------------------------------------------------------------
with tabs[1]:
    st.header("Painel geral de acompanhamento")
    st.markdown(
        """Visualize a **distribuição percentual** das avaliações (Ótima → Péssima) para cada área da administração.\
        *Escolha o mês desejado* no menu lateral ou mantenha o último mês para visão atual.\
        → Útil para detectar rapidamente quais áreas têm melhor ou pior percepção no período selecionado.
        """
    )

    df_month = _df[_df["Mês/Ano"] == month_dt]
    if df_month.empty:
        st.warning("Não há registros para a combinação de filtros selecionada.")
    else:
        df_long = df_month.melt(value_vars=PERCEPTION_COLS, var_name="Área", value_name="Avaliação")
        df_long["Avaliação"] = pd.Categorical(df_long["Avaliação"], categories=ORDER_AVAL, ordered=True)
        counts = df_long.groupby(["Área", "Avaliação"]).size().reset_index(name="freq")
        counts["percent"] = counts["freq"] / counts.groupby("Área")["freq"].transform("sum") * 100

        fig = px.bar(
            counts,
            x="percent",
            y="Área",
            color="Avaliação",
            orientation="h",
            text_auto=".1f",
            labels={"percent": "%"},
            category_orders={"Avaliação": ORDER_AVAL},
            color_discrete_map=COLOR_MAP,
        )
        fig.update_layout(barmode="stack", xaxis_title="Percentual", yaxis_title="Área", template="simple_white")
        fig.update_xaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# 2) Painel temporal
# ----------------------------------------------------------------------------
with tabs[2]:
    st.header("Painel temporal")
    st.markdown(
        """Acompanhe a **tendência** das avaliações ao longo do tempo.\
        São exibidos três gráficos: **Ótimo/Bom**, **Regular** e **Ruim/Péssimo**.\
        """
    )

    df_temporal = df_raw.copy()


    df_long = df_temporal.melt(
        id_vars=["Mês/Ano"],
        value_vars=PERCEPTION_COLS,
        var_name="Área",
        value_name="Avaliação"
    )

    df_long["Avaliação"] = (
        df_long["Avaliação"]
        .astype(str)
        .str.strip()
        .str.replace("Ótimo", "Ótima", regex=False)
        .str.replace("Bom", "Boa", regex=False)
        .str.replace("Péssimo", "Péssima", regex=False)
    )

    df_long["Categoria"] = df_long["Avaliação"].map(CAT_MAP)

    df_long = df_long.dropna(subset=["Categoria"])

    series = (
        df_long
        .groupby(
            ["Mês/Ano", "Área", "Categoria"],
            observed=True
        )
        .size()
        .reset_index(name="freq")
    )

    series["percent"] = (
        series["freq"]
        / series.groupby(["Mês/Ano", "Área"])["freq"].transform("sum")
        * 100
    )

    series = series.sort_values("Mês/Ano")

    for cat in ["Ótima/Boa", "Regular", "Ruim/Péssima"]:
            st.subheader(f"Evolução – {cat}")
            sub = series[series["Categoria"] == cat]
            fig = px.line(sub, x="Mês/Ano", y="percent", color="Área", markers=True, labels={"percent": "%", "Mês/Ano": "Mês"})
            fig.update_layout(yaxis_title="Percentual", xaxis_title="Mês/Ano", template="simple_white")
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# 3) Painel de acompanhamento do perfil da amostra
# ----------------------------------------------------------------------------
with tabs[3]:
    st.header("Painel de acompanhamento do perfil da amostra")
    st.markdown(
        """Veja a **composição da amostra** para cada variável sociodemográfica, no mês selecionado.\
        Útil para avaliar cobertura e possíveis vieses de coleta.
        """
    )

    df_month = _df[_df["Mês/Ano"] == month_dt]
    if df_month.empty:
        st.warning("Não há registros para a combinação de filtros selecionada.")
    else:
        for i, col in enumerate(PROFILE_COLS):
            if i % 3 == 0:
                cols_row = st.columns(3, gap="large")
            with cols_row[i % 3]:
                st.subheader(col)
                counts = df_month[col].value_counts(normalize=True, dropna=False).mul(100).rename("percent").reset_index().rename(columns={"index": col})
                counts = counts.sort_values("percent", ascending=True)

                fig = px.bar(counts, x="percent", y=col, orientation="h", text="percent", labels={"percent": "%"}, color_discrete_sequence=[BAR_COLOR])
                fig.update_traces(texttemplate="%{x:.1f}%", textposition="inside", insidetextanchor="middle", marker_line_color="white", marker_line_width=0.5)
                fig.update_layout(template="simple_white", xaxis_title="Percentual", yaxis_title="", yaxis=dict(categoryorder="total ascending"), bargap=0.2, margin=dict(l=0, r=0, t=0, b=0))
                fig.update_xaxes(ticksuffix="%", showgrid=False)
                fig.update_yaxes(showgrid=False)
                st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# 4) Cruzamentos de variáveis
# ----------------------------------------------------------------------------
with tabs[4]:
    st.header("Cruzamentos de variáveis")
    st.markdown(
        """Selecione até **três variáveis** para cruzar e veja a distribuição percentual de respostas.\
            
        – **1 variável**: frequência global.\
        
        – **2 variáveis**: distribuição dentro de cada nível da variável do eixo Y.\
        
        – **3 variáveis**: mesmo princípio, com facetas para a terceira variável.
        """
    )

    vars_available = [c for c in df_raw.columns if c != "Mês/Ano"]
    sel_vars = st.multiselect(
        "Selecione até 3 variáveis para cruzar",
        options=vars_available,
        help="É possível selecionar de 1 a 3 variáveis",
        max_selections=3,
    )

    if sel_vars:
        cross = _df.groupby(sel_vars).size().reset_index(name="freq")

        if len(sel_vars) == 1:
            cross["percent"] = cross["freq"] / cross["freq"].sum() * 100
        elif len(sel_vars) == 2:
            cross["percent"] = cross["freq"] / cross.groupby(sel_vars[0])["freq"].transform("sum") * 100
        else:
            cross["percent"] = cross["freq"] / cross.groupby([sel_vars[0], sel_vars[2]])["freq"].transform("sum") * 100

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
            fig = px.bar(
                cross,
                y=sel_vars[0],
                color=sel_vars[1],
                facet_col=sel_vars[2],
                facet_col_wrap=cols_wrap,
                facet_row_spacing=0.12,
                facet_col_spacing=0.04,
                barmode="stack",
                **common_args,
            )
            fig.update_layout(height=max(350, 250 * rows))

        fig.update_traces(texttemplate=text_fmt)
        fig.update_layout(template="simple_white", xaxis_title="Percentual", yaxis_title="")
        for axis in fig.layout:
            if isinstance(fig.layout[axis], dict) and fig.layout[axis].get("type") == "linear" and axis.startswith("xaxis"):
                fig.layout[axis].update(range=[0, 100], ticksuffix="%")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecione pelo menos uma variável para visualizar o cruzamento.")

# ----------------------------------------------------------------------------
# 5) Download da base completa
# ----------------------------------------------------------------------------
with tabs[5]:
    st.header("Download da base completa")
    st.markdown("""Visualize o banco de dados completo (sem filtros) e faça o **download em CSV** para análises adicionais.""")

    st.dataframe(df_raw, use_container_width=True, height=500)

    csv_data = df_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Baixar CSV",
        data=csv_data,
        file_name="base_completa.csv",
        mime="text/csv",
    )