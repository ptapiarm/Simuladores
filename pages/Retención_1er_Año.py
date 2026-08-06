"""
Simulador de Proyección de Metas
---------------------------------
App en Streamlit para proyectar metas a futuro a partir de datos históricos.
Permite simular en modo General (sin separar por sexo) o Por Sexo (Hombres/Mujeres).

Datos ficticios incluidos para poder probar la app. Los valores representan
porcentajes (%) de cumplimiento de meta. Cuando tengas los datos reales,
reemplaza directamente los arreglos en la sección "1. DATOS" más abajo.
No requiere carga de archivos: los datos viven fijos en este script.
"""

import base64
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador de Metas — UAH", layout="wide", page_icon="🎓")

# =========================================================
# 0. TEMA INSTITUCIONAL (colores UAH) Y ENCABEZADO CON LOGO
# =========================================================
COLOR_FONDO = "#ecebe5"
COLOR_TEXTO = "#000000"
COLOR_ACENTO = "#ff6f43"
COLOR_BLANCO = "#ffffff"

# Paleta extendida para gráficos con varias series (tonos derivados del negro
# y el naranja institucional, para mantenerse dentro de la misma identidad).
PALETA_METODOS = ["#000000", "#ff6f43", "#8c8c8c", "#c9542b", "#4d4d4d", "#ffb08c"]

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {COLOR_FONDO};
        color: {COLOR_TEXTO};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_TEXTO};
    }}
    section[data-testid="stSidebar"] * {{
        color: {COLOR_BLANCO} !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] [data-baseweb="base-input"] {{
        background-color: #262626 !important;
        color: {COLOR_BLANCO} !important;
        border-color: #444444 !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: #444444 !important;
    }}
    h1, h2, h3, h4, h5, h6, p, label, span, div {{
        color: {COLOR_TEXTO};
    }}
    .stButton > button, .stDownloadButton > button {{
        background-color: {COLOR_ACENTO};
        color: {COLOR_BLANCO};
        border: none;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background-color: #e35a2e;
        color: {COLOR_BLANCO};
    }}
    [data-baseweb="tab-highlight"] {{
        background-color: {COLOR_ACENTO} !important;
    }}
    .uah-header {{
        background-color: {COLOR_TEXTO};
        padding: 1.2rem 1.6rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 1.2rem;
        margin-bottom: 1.5rem;
    }}
    .uah-header img {{
        height: 56px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_base64():
    """Lee el logo UAH desde disco (misma carpeta del script) y lo entrega en base64.
    Si no encuentra el archivo, retorna None y el encabezado se muestra sin logo."""
    ruta = Path(__file__).parent.parent / "UAH-logo.png"
    if ruta.exists():
        return base64.b64encode(ruta.read_bytes()).decode("ascii")
    return None


_logo_b64 = _logo_base64()
_logo_html = (
    f'<img src="data:image/png;base64,{_logo_b64}" alt="Logo UAH">' if _logo_b64 else ""
)

st.markdown(
    f"""
    <div class="uah-header">
        {_logo_html}
        <div>
            <div style="color:{COLOR_BLANCO}; font-size:1.6rem; font-weight:700; line-height:1.3;">Simulador de Proyección de Metas</div>
            <div style="color:{COLOR_BLANCO}; opacity:0.9;">Universidad Alberto Hurtado</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 1. DATOS (5 años de histórico) — valores en % (0-100)
#    Reemplaza estos valores por los datos reales cuando los tengas.
# =========================================================
ANIOS_HIST = [2021, 2022, 2023, 2024, 2025]

# Modo GENERAL (sin separar por sexo)
datos_general = pd.DataFrame({
    "Cohorte": ANIOS_HIST,
    "% de retención": [82, 82, 81, 80, 84],
})

# Modo POR SEXO
datos_sexo = pd.DataFrame({
    "Cohorte": ANIOS_HIST * 2,
    "Sexo": ["Mujer"] * 5 + ["Hombre"] * 5,
    "% de retención": [84, 83, 83, 82, 86,   # Hombres
              80, 80, 79, 78, 82],  # Mujeres
})

# Curva de comparación / referencia — sistema universitario completo (Datos SIES)
NOMBRE_SIES = "Universidades-Datos Sies"
ANIOS_SIES = [2021, 2022, 2023, 2024]

# En modo General, la referencia SIES viene en 2 series: universidades con
# 6 años de acreditación y universidades con 5 años de acreditación.
NOMBRE_SIES_6 = "Universidades 6 años de acreditación"
NOMBRE_SIES_5 = "Universidades 5 años de acreditación"

datos_general_sies = pd.DataFrame({
    "Cohorte": ANIOS_SIES,
    NOMBRE_SIES_6: [85.4, 83.5, 84.4, 85.7],
    NOMBRE_SIES_5: [82.7, 80.8, 81.8, 82.8],
})

datos_sexo_sies = pd.DataFrame({
    "Cohorte": ANIOS_SIES * 2,
    "Sexo": ["Mujer"] * 4 + ["Hombre"] * 4,
    "% de retención": [84.6, 83.3, 84.0, 85.3,   # Mujeres
              81.2, 79.6, 81.0, 82.3],  # Hombres
})


# =========================================================
# 1B. GRÁFICOS — helper con escala de eje Y fija
# =========================================================
ESCALA_Y_MIN = 50
ESCALA_Y_MAX = 100


def _dash_de_vega(valor):
    """Traduce un patrón de guiones estilo Vega ([1,0], [6,3], [2,2]) al
    nombre de estilo de línea que usa Plotly."""
    if valor == DASH_SOLIDO:
        return "solid"
    if valor == DASH_FINO:
        return "dot"
    return "dash"  # DASH_MEDIO y cualquier otro caso


PLOTLY_LEGEND = dict(
    orientation="h",
    yanchor="top", y=-0.25,
    xanchor="center", x=0.5,
    font=dict(size=12),
    groupclick="togglegroup",  # un clic activa/desactiva todos los tramos de esa curva a la vez
)
PLOTLY_XAXIS = dict(
    title="Cohorte", type="category", tickangle=0,
    showgrid=False, linecolor="#b8b6ac", tickfont=dict(size=12),
)
PLOTLY_YAXIS = dict(
    title="% de retención", range=[ESCALA_Y_MIN, ESCALA_Y_MAX],
    gridcolor="#dedcd3", griddash="dot", linecolor="#b8b6ac", tickfont=dict(size=12),
)


def _layout_base(height, width):
    return dict(
        height=height,
        width=width,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12, color=COLOR_TEXTO),
        margin=dict(t=20, b=10, l=10, r=10),
        legend=PLOTLY_LEGEND,
        xaxis=PLOTLY_XAXIS,
        yaxis=PLOTLY_YAXIS,
        hovermode="x unified",
    )


def grafico_lineas(df_wide, colores, height=400, width=560, **_ignorado):
    """Dibuja un gráfico de líneas (Plotly) a partir de un DataFrame ancho
    (índice = Cohorte, una columna por serie), con el eje Y fijo entre
    ESCALA_Y_MIN y ESCALA_Y_MAX, puntos marcados en cada año y los colores
    indicados en el mismo orden que las columnas. Cada curva se puede
    activar/desactivar haciendo clic en su nombre en la leyenda."""
    fig = go.Figure()
    x_vals = [str(a) for a in df_wide.index]
    for col, color in zip(df_wide.columns, colores):
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_wide[col],
            mode="lines+markers",
            name=col,
            line=dict(color=color, width=3),
            marker=dict(size=8, color=color),
            connectgaps=True,
            hovertemplate="%{fullData.name}: %{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(**_layout_base(height, width))
    st.plotly_chart(fig, use_container_width=False)


def grafico_proyeccion_sexo(df_grafico, color_domain, color_range, dash_domain, dash_range, height=430, width=760):
    """Dibuja el gráfico único de proyección por sexo (Plotly), con líneas
    punteadas para la parte proyectada y sólidas para la histórica. Cada
    curva (agrupada por 'Grupo') se activa/desactiva en conjunto al hacer
    clic en la leyenda, aunque esté compuesta por varios tramos (histórico +
    proyección)."""
    color_map = dict(zip(color_domain, color_range))
    dash_map = {k: _dash_de_vega(v) for k, v in zip(dash_domain, dash_range)}
    fig = go.Figure()
    orden_grupos = list(dict.fromkeys(df_grafico["Grupo"]))
    for grupo in orden_grupos:
        sub_grupo = df_grafico[df_grafico["Grupo"] == grupo]
        color = color_map.get(grupo, COLOR_TEXTO)
        primero = True
        for dashkey in dict.fromkeys(sub_grupo["DashKey"]):
            tramo = sub_grupo[sub_grupo["DashKey"] == dashkey].sort_values("Cohorte")
            fig.add_trace(go.Scatter(
                x=[str(a) for a in tramo["Cohorte"]],
                y=tramo["% de retención"],
                mode="lines+markers",
                name=grupo,
                legendgroup=grupo,
                showlegend=primero,
                line=dict(color=color, width=2.6, dash=dash_map.get(dashkey, "solid")),
                marker=dict(size=7, color=color),
                hovertemplate=f"{grupo} ({dashkey})" + ": %{y:.1f}%<extra></extra>",
            ))
            primero = False
    fig.update_layout(**_layout_base(height, width))
    st.plotly_chart(fig, use_container_width=False)


# =========================================================
# 2. FUNCIONES DE SIMULACIÓN
# =========================================================
def proyeccion_promedio_movil(valores, anios, n_futuro, ventana=3):
    """Proyecta usando el promedio móvil de los últimos `ventana` años.
    El promedio calculado se repite (o se puede ir actualizando) hacia adelante."""
    valores = list(valores)
    resultado = []
    serie = valores.copy()
    for _ in range(n_futuro):
        prom = np.mean(serie[-ventana:])
        resultado.append(prom)
        serie.append(prom)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado


def proyeccion_regresion_lineal(valores, anios, n_futuro):
    """Ajusta una regresión lineal (mínimos cuadrados) y proyecta."""
    x = np.array(anios)
    y = np.array(valores)
    coef = np.polyfit(x, y, 1)  # pendiente, intercepto
    modelo = np.poly1d(coef)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    resultado = [modelo(a) for a in anios_futuros]
    return anios_futuros, resultado


def proyeccion_tendencia_porcentual(valores, anios, n_futuro, ventana_tasas=None):
    """Calcula la tasa de crecimiento promedio año a año (%) y la aplica hacia adelante.
    Por defecto usa todas las tasas interanuales del histórico; si se especifica
    `ventana_tasas`, solo promedia las últimas `ventana_tasas` tasas (años más recientes)."""
    valores = np.array(valores, dtype=float)
    tasas = (valores[1:] - valores[:-1]) / valores[:-1]
    if ventana_tasas is not None:
        tasas = tasas[-ventana_tasas:]
    tasa_prom = np.mean(tasas)
    resultado = []
    ultimo = valores[-1]
    for _ in range(n_futuro):
        ultimo = ultimo * (1 + tasa_prom)
        resultado.append(ultimo)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado, tasa_prom


def proyeccion_cagr(valores, anios, n_futuro):
    """Tasa de crecimiento anual compuesta (CAGR) entre el primer y último año."""
    valores = np.array(valores, dtype=float)
    n_periodos = len(valores) - 1
    cagr = (valores[-1] / valores[0]) ** (1 / n_periodos) - 1
    resultado = []
    ultimo = valores[-1]
    for _ in range(n_futuro):
        ultimo = ultimo * (1 + cagr)
        resultado.append(ultimo)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado, cagr


METODOS = {
    "Promedio móvil (últimos 3 años)": "pm3",
    "Regresión lineal": "reg",
    "Tendencia (% de crecimiento promedio)": "tend",
    "CAGR (crecimiento anual compuesto)": "cagr",
}


def calcular_proyeccion(metodo_key, valores, anios, n_futuro, ventana=3, ventana_tend=None):
    if metodo_key == "pm3":
        anios_f, vals_f = proyeccion_promedio_movil(valores, anios, n_futuro, ventana)
        nota = f"Promedio móvil con ventana de {ventana} años."
    elif metodo_key == "reg":
        anios_f, vals_f = proyeccion_regresion_lineal(valores, anios, n_futuro)
        nota = "Ajuste por regresión lineal (mínimos cuadrados)."
    elif metodo_key == "tend":
        anios_f, vals_f, tasa = proyeccion_tendencia_porcentual(valores, anios, n_futuro, ventana_tend)
        alcance = f"últimas {ventana_tend} tasas interanuales" if ventana_tend else "todas las tasas interanuales del histórico"
        nota = f"Tasa de crecimiento promedio aplicada: {tasa*100:.2f}% anual (calculada sobre {alcance})."
    elif metodo_key == "cagr":
        anios_f, vals_f, cagr = proyeccion_cagr(valores, anios, n_futuro)
        nota = f"CAGR calculado: {cagr*100:.2f}% anual."
    else:
        raise ValueError("Método no reconocido")
    return anios_f, vals_f, nota


# =========================================================
# 3. INTERFAZ - BARRA LATERAL
# =========================================================
st.sidebar.title("⚙️ Configuración")

modo = st.sidebar.radio(
    "Modo de simulación",
    ["General (sin separar por sexo)", "Por sexo"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Proyección")
n_futuro = st.sidebar.slider("Cohortes a proyectar", min_value=1, max_value=5, value=5)

metodo_nombre = st.sidebar.selectbox("Método de simulación", list(METODOS.keys()))
metodo_key = METODOS[metodo_nombre]
st.sidebar.caption(
    "💡 Datos no estacionarios (con tendencia): se recomienda priorizar "
    "Regresión lineal, Tendencia (%) o CAGR."
)

comparar_todos = st.sidebar.checkbox("Comparar todos los métodos a la vez", value=False)

ventana = 3
if metodo_key == "pm3" or comparar_todos:
    ventana = st.sidebar.slider("Ventana del promedio móvil (años)", 2, 5, 3)

ventana_tend = None
if metodo_key == "tend" or comparar_todos:
    usar_todo_hist = st.sidebar.checkbox(
        "Tendencia: usar todo el histórico", value=True,
        help="Si lo desactivas, puedes limitar el cálculo de la tasa de crecimiento "
             "promedio a solo los últimos N años en vez de todo el histórico.",
    )
    if not usar_todo_hist:
        ventana_tend = st.sidebar.slider(
            "Tendencia: cuántas variaciones interanuales promediar", 2, 4, 3,
            help="Ej: 3 = promedia las últimas 3 variaciones año-a-año, "
                 "en vez de usar todo el histórico.",
        )


# =========================================================
# 4. CARGA DE DATOS
# =========================================================
df_entrada = datos_general if modo.startswith("General") else datos_sexo


# =========================================================
# 5. MODO GENERAL
# =========================================================
COLOR_SIES = "#8c8c8c"
COLOR_SIES_6 = "#8c8c8c"
COLOR_SIES_5 = "#c9c9c9"


def mostrar_bloque_general(df, titulo="General", mostrar_grafico_historico=True, df_sies=None):
    st.subheader(f"📁 Datos históricos — {titulo}")
    col_tabla, col_grafico = st.columns([1, 2])
    with col_tabla:
        st.dataframe(
            df,
            use_container_width=False,
            hide_index=True,
            column_config={"% de retención": st.column_config.NumberColumn("% de retención", format="%.1f%%")},
        )
    if mostrar_grafico_historico:
        with col_grafico:
            if df_sies is not None:
                df_hist_sies = pd.merge(df, df_sies, on="Cohorte", how="outer").sort_values("Cohorte")
                columnas_sies = [c for c in df_sies.columns if c != "Cohorte"]
                colores_sies = [COLOR_SIES_6, COLOR_SIES_5][: len(columnas_sies)]
                grafico_lineas(
                    df_hist_sies.set_index("Cohorte")[["% de retención"] + columnas_sies],
                    colores=[COLOR_ACENTO] + colores_sies,
                )
            else:
                grafico_lineas(df.set_index("Cohorte")[["% de retención"]], colores=[COLOR_ACENTO])

    anios = df["Cohorte"].tolist()
    valores = df["% de retención"].tolist()

    st.subheader(f"🔮 Proyección — {titulo}")

    if comparar_todos:
        df_comp = pd.DataFrame({"Cohorte": anios, "Histórico UAH": valores})
        columnas_sies = []
        if df_sies is not None:
            columnas_sies = [c for c in df_sies.columns if c != "Cohorte"]
            df_comp = pd.merge(df_comp, df_sies, on="Cohorte", how="outer")
        notas = []
        df_futuro = None
        for nombre, key in METODOS.items():
            try:
                anios_f, vals_f, nota = calcular_proyeccion(
                    key, valores, anios, n_futuro, ventana, ventana_tend
                )
                serie = pd.Series(
                    [np.nan] * len(anios) + list(vals_f),
                    index=anios + anios_f,
                    name=nombre,
                )
                df_comp = df_comp.set_index("Cohorte").combine_first(
                    serie.to_frame()
                ).reset_index().rename(columns={"index": "Cohorte"})
                serie_futuro = pd.Series(vals_f, index=anios_f, name=nombre)
                df_futuro = (
                    serie_futuro.to_frame() if df_futuro is None
                    else df_futuro.join(serie_futuro, how="outer")
                )
                notas.append(f"- **{nombre}**: {nota}")
            except Exception as e:
                notas.append(f"- **{nombre}**: no se pudo calcular ({e})")
        df_comp = df_comp.sort_values("Cohorte").reset_index(drop=True)
        orden_cols = ["Histórico UAH"]
        colores_cols = [COLOR_TEXTO]
        if columnas_sies:
            orden_cols += columnas_sies
            colores_cols += [COLOR_SIES_6, COLOR_SIES_5][: len(columnas_sies)]
        metodos_presentes = [n for n in METODOS.keys() if n in df_comp.columns]
        orden_cols += metodos_presentes
        # Se evita el gris (#8c8c8c), reservado para la curva SIES, en los colores de método.
        paleta_metodos_disponible = [c for c in PALETA_METODOS if c != COLOR_SIES]
        colores_cols += paleta_metodos_disponible[1: 1 + len(metodos_presentes)]
        df_comp = df_comp[["Cohorte"] + orden_cols]
        col_config = {
            col: st.column_config.NumberColumn(col, format="%.1f%%")
            for col in df_comp.columns if col != "Cohorte"
        }
        st.dataframe(df_comp, use_container_width=False, hide_index=True, column_config=col_config)
        grafico_lineas(
            df_comp.set_index("Cohorte"), colores=colores_cols,
            width=760, legend_columns=2, legend_label_limit=320,
        )
        st.markdown("**Notas de cada método:**")
        st.markdown("\n".join(notas))

        st.markdown("#### 📋 Tabla resumen — valor proyectado por cohorte y método")
        if df_futuro is None:
            st.warning("No fue posible calcular ningún método con los datos actuales.")
        else:
            df_futuro = df_futuro.reset_index().rename(columns={"index": "Cohorte"}).sort_values("Cohorte")
            col_config_futuro = {
                col: st.column_config.NumberColumn(col, format="%.1f%%")
                for col in df_futuro.columns if col != "Cohorte"
            }
            st.dataframe(df_futuro, use_container_width=False, hide_index=True, column_config=col_config_futuro)

            csv = df_futuro.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar tabla de proyecciones (CSV)",
                data=csv,
                file_name=f"proyeccion_comparacion_{titulo.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )
    else:
        anios_f, vals_f, nota = calcular_proyeccion(
            metodo_key, valores, anios, n_futuro, ventana, ventana_tend
        )
        df_proy = pd.DataFrame({"Cohorte": anios_f, "% de retención proyectada": vals_f})
        st.info(nota)

        df_hist_plot = df.rename(columns={"% de retención": "Histórico UAH"})
        df_proy_plot = df_proy.rename(columns={"% de retención proyectada": "Proyección"})
        df_final = pd.merge(
            df_hist_plot[["Cohorte", "Histórico UAH"]],
            df_proy_plot.rename(columns={"Cohorte": "Cohorte"})[["Cohorte", "Proyección"]],
            on="Cohorte",
            how="outer",
        ).sort_values("Cohorte")
        columnas_chart = ["Histórico UAH", "Proyección"]
        colores_chart = [COLOR_TEXTO, COLOR_ACENTO]
        if df_sies is not None:
            columnas_sies = [c for c in df_sies.columns if c != "Cohorte"]
            df_final = pd.merge(df_final, df_sies, on="Cohorte", how="outer").sort_values("Cohorte")
            columnas_chart += columnas_sies
            colores_chart += [COLOR_SIES_6, COLOR_SIES_5][: len(columnas_sies)]
        grafico_lineas(df_final.set_index("Cohorte")[columnas_chart], colores=colores_chart)

        st.markdown("#### 📋 Tabla resumen — valor proyectado por cohorte")
        st.dataframe(
            df_proy,
            use_container_width=False,
            hide_index=True,
            column_config={
                "% de retención proyectada": st.column_config.NumberColumn("% de retención proyectada", format="%.1f%%")
            },
        )

        csv = pd.concat(
            [df.assign(Tipo="Histórico"), df_proy.rename(columns={"% de retención proyectada": "% de retención"}).assign(Tipo="Proyección")],
            ignore_index=True,
        ).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar histórico + proyección (CSV)",
            data=csv,
            file_name=f"proyeccion_{titulo.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )


# =========================================================
# 6. MODO POR SEXO
# =========================================================
DASH_SOLIDO = [1, 0]
DASH_MEDIO = [6, 3]
DASH_FINO = [2, 2]

PALETA_METODOS_SEXO = ["#8c8c8c", "#c9542b", "#4d4d4d", "#ffb08c", "#603813"]


def mostrar_bloque_por_sexo(df, df_sies=None):
    st.subheader("📁 Datos históricos — Por sexo")

    pivot = df.pivot(index="Cohorte", columns="Sexo", values="% de retención").reset_index()
    columnas_orden = ["Cohorte"] + [c for c in ["Mujer", "Hombre"] if c in pivot.columns]
    pivot = pivot[columnas_orden]
    col_config_pivot = {
        "Cohorte": st.column_config.NumberColumn("Cohorte", format="%d"),
        "Mujer": st.column_config.NumberColumn("Mujer", format="%.1f%%"),
        "Hombre": st.column_config.NumberColumn("Hombre", format="%.1f%%"),
    }
    col_tabla3, col_grafico3 = st.columns([1, 2])
    with col_tabla3:
        st.dataframe(pivot, use_container_width=False, hide_index=True, column_config=col_config_pivot)

    pivot_chart = df.pivot(index="Cohorte", columns="Sexo", values="% de retención")
    orden_sexo = [c for c in ["Mujer", "Hombre"] if c in pivot_chart.columns]
    pivot_chart = pivot_chart[orden_sexo]
    colores_hist = [COLOR_ACENTO, COLOR_TEXTO][: len(orden_sexo)]
    colores_sies_sexo = {"Mujer": "#c9c9c9", "Hombre": "#4d4d4d"}

    with col_grafico3:
        if df_sies is not None:
            pivot_sies = df_sies.pivot(index="Cohorte", columns="Sexo", values="% de retención")
            pivot_sies = pivot_sies[[c for c in ["Mujer", "Hombre"] if c in pivot_sies.columns]]
            pivot_sies = pivot_sies.rename(columns={c: f"{c} - {NOMBRE_SIES}" for c in pivot_sies.columns})
            pivot_chart_full = pivot_chart.join(pivot_sies, how="outer")
            colores_hist_full = colores_hist + [colores_sies_sexo.get(s, COLOR_SIES) for s in orden_sexo]
            grafico_lineas(pivot_chart_full, colores=colores_hist_full)
        else:
            grafico_lineas(pivot_chart, colores=colores_hist)

    st.subheader("🔮 Proyección — Por sexo (gráfico y tabla únicos)")

    sexos = orden_sexo  # ["Mujer", "Hombre"]
    registros = []       # para el gráfico (formato largo)
    notas = []
    df_futuro_final = None  # para la tabla resumen (formato ancho)

    if comparar_todos:
        for sexo in sexos:
            df_sexo = df[df["Sexo"] == sexo][["Cohorte", "% de retención"]].reset_index(drop=True)
            anios = df_sexo["Cohorte"].tolist()
            valores = df_sexo["% de retención"].tolist()

            for a, v in zip(anios, valores):
                registros.append({"Cohorte": a, "% de retención": v, "Grupo": f"Histórico UAH - {sexo}", "DashKey": "Histórico"})

            for i, (nombre, key) in enumerate(METODOS.items()):
                try:
                    anios_f, vals_f, nota = calcular_proyeccion(
                        key, valores, anios, n_futuro, ventana, ventana_tend
                    )
                    serie_anios = [anios[-1]] + anios_f
                    serie_vals = [valores[-1]] + vals_f
                    for a, v in zip(serie_anios, serie_vals):
                        registros.append({
                            "Cohorte": a, "% de retención": v, "Grupo": nombre, "DashKey": f"Proyección - {sexo}",
                        })
                    notas.append(f"- **{sexo} — {nombre}**: {nota}")

                    serie_futuro = pd.Series(vals_f, index=anios_f, name=f"{sexo} - {nombre}")
                    df_futuro_final = (
                        serie_futuro.to_frame() if df_futuro_final is None
                        else df_futuro_final.join(serie_futuro, how="outer")
                    )
                except Exception as e:
                    notas.append(f"- **{sexo} — {nombre}**: no se pudo calcular ({e})")

        color_domain = [f"Histórico UAH - {s}" for s in sexos] + list(METODOS.keys())
        color_range = ([COLOR_ACENTO, COLOR_TEXTO][: len(sexos)]) + PALETA_METODOS_SEXO[: len(METODOS)]
        dash_domain = ["Histórico"] + [f"Proyección - {s}" for s in sexos]
        dash_range = [DASH_SOLIDO, DASH_MEDIO, DASH_FINO][: len(dash_domain)]

    else:
        for sexo in sexos:
            df_sexo = df[df["Sexo"] == sexo][["Cohorte", "% de retención"]].reset_index(drop=True)
            anios = df_sexo["Cohorte"].tolist()
            valores = df_sexo["% de retención"].tolist()

            for a, v in zip(anios, valores):
                registros.append({"Cohorte": a, "% de retención": v, "Grupo": sexo, "DashKey": "Histórico"})

            anios_f, vals_f, nota = calcular_proyeccion(
                metodo_key, valores, anios, n_futuro, ventana, ventana_tend
            )
            serie_anios = [anios[-1]] + anios_f
            serie_vals = [valores[-1]] + vals_f
            for a, v in zip(serie_anios, serie_vals):
                registros.append({"Cohorte": a, "% de retención": v, "Grupo": sexo, "DashKey": "Proyección"})
            notas.append(f"- **{sexo}**: {nota}")

            serie_futuro = pd.Series(vals_f, index=anios_f, name=sexo)
            df_futuro_final = (
                serie_futuro.to_frame() if df_futuro_final is None
                else df_futuro_final.join(serie_futuro, how="outer")
            )

        color_domain = list(sexos)
        color_range = [COLOR_ACENTO, COLOR_TEXTO][: len(sexos)]
        dash_domain = ["Histórico", "Proyección"]
        dash_range = [DASH_SOLIDO, DASH_MEDIO]

    if df_sies is not None:
        for sexo in sexos:
            df_s = df_sies[df_sies["Sexo"] == sexo][["Cohorte", "% de retención"]]
            for _, fila in df_s.iterrows():
                registros.append({
                    "Cohorte": fila["Cohorte"], "% de retención": fila["% de retención"],
                    "Grupo": f"{sexo} - {NOMBRE_SIES}", "DashKey": "Histórico",
                })
            color_domain.append(f"{sexo} - {NOMBRE_SIES}")
            color_range.append(colores_sies_sexo.get(sexo, COLOR_SIES))

    df_grafico = pd.DataFrame(registros)
    grafico_proyeccion_sexo(
        df_grafico, color_domain=color_domain, color_range=color_range,
        dash_domain=dash_domain, dash_range=dash_range, height=430, width=760,
    )

    st.markdown("**Notas de la proyección:**")
    st.markdown("\n".join(notas))

    st.markdown("#### 📋 Tabla resumen — valor proyectado por cohorte (única, ambos sexos)")
    if df_futuro_final is None:
        st.warning("No fue posible calcular la proyección con los datos actuales.")
    else:
        df_futuro_final = df_futuro_final.reset_index().rename(columns={"index": "Cohorte"}).sort_values("Cohorte")
        col_config_futuro = {
            col: st.column_config.NumberColumn(col, format="%.1f%%")
            for col in df_futuro_final.columns if col != "Cohorte"
        }
        st.dataframe(df_futuro_final, use_container_width=False, hide_index=True, column_config=col_config_futuro)

        csv = df_futuro_final.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla de proyecciones (CSV)",
            data=csv,
            file_name="proyeccion_por_sexo.csv",
            mime="text/csv",
        )


# =========================================================
# 7. EJECUCIÓN SEGÚN MODO
# =========================================================
if modo.startswith("General"):
    mostrar_bloque_general(df_entrada, titulo="General", df_sies=datos_general_sies)
else:
    mostrar_bloque_por_sexo(df_entrada, df_sies=datos_sexo_sies)

st.markdown("---")
with st.expander("ℹ️ Descripción de los métodos de simulación disponibles"):
    st.markdown(
        """
- **Promedio móvil (últimos 3 años):** promedia los valores más recientes para
  suavizar variaciones puntuales. Al no capturar tendencia, en series con
  tendencia sostenida tiende a subestimar (o sobreestimar) el futuro.
- **Regresión lineal:** ajusta una línea recta a todo el histórico y la extiende
  hacia adelante. Recomendado cuando hay una tendencia clara y sostenida.
- **Tendencia (% de crecimiento promedio):** calcula la variación porcentual
  promedio año a año y la aplica de forma compuesta hacia el futuro. Por
  defecto usa **todo el histórico**, pero puede limitarse a las últimas N
  variaciones interanuales desde la barra lateral. Recomendado para series
  con tendencia.
- **CAGR (crecimiento anual compuesto):** es la tasa de crecimiento que, si
  se repitiera exactamente igual cada año, llevaría desde el primer valor
  del histórico hasta el último — como el interés compuesto de una
  inversión. La fórmula solo usa el primer y el último año, pero eso no
  significa que ignore lo que pasó en el medio: es un atajo matemático
  equivalente a promediar el crecimiento de todos los años "encadenándolos"
  entre sí, en vez de simplemente sumarlos y dividir. Por eso, si el
  indicador subió de forma pareja, el CAGR da prácticamente lo mismo que
  Tendencia; pero si hubo algún año con un salto raro, el CAGR le da menos
  peso a ese sobresalto, porque en el fondo solo le importa dónde arrancaste
  y dónde terminaste. Recomendado para series con tendencia.
        """
    )
