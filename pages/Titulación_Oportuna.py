"""
Simulador de Proyección de Metas — Titulación
-----------------------------------------------
App en Streamlit para proyectar metas de titulación a futuro a partir de
datos históricos. Estructura y métodos de simulación replicados desde el
simulador de Retención de 1er Año.

Datos reales incluidos (% de titulación por cohorte, 2015-2020).
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

PALETA_METODOS = ["#000000", "#ff6f43", "#8c8c8c", "#c9542b", "#4d4d4d", "#ffb08c", "#2b6f77"]

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
            <div style="color:{COLOR_BLANCO}; font-size:1.6rem; font-weight:700; line-height:1.3;">Simulador de Proyección de Metas — Titulación</div>
            <div style="color:{COLOR_BLANCO}; opacity:0.9;">Universidad Alberto Hurtado</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 1. DATOS — % de titulación por cohorte
# =========================================================
ANIOS_HIST = [2016, 2017, 2018, 2019, 2020]
VALORES_HIST = [37.0, 36.0, 38.0, 42.0, 44.1]

datos_general = pd.DataFrame({
    "Cohorte": ANIOS_HIST,
    "% de titulación": VALORES_HIST,
})

# Datos por sexo (mismas cohortes que General: 2016-2020)
ANIOS_HIST_SEXO = [2016, 2017, 2018, 2019, 2020]
datos_sexo = pd.DataFrame({
    "Cohorte": ANIOS_HIST_SEXO * 2,
    "Sexo": ["Hombre"] * 5 + ["Mujer"] * 5,
    "% de titulación": [30.1, 31.0, 31.5, 35.4, 36.9,   # Hombres
                         42.2, 40.5, 43.7, 48.3, 49.9],  # Mujeres
})

# =========================================================
# 1B. GRÁFICOS — helper con escala de eje Y fija
# =========================================================
ESCALA_Y_MIN = 20
ESCALA_Y_MAX = 70

PLOTLY_LEGEND = dict(
    orientation="h",
    yanchor="top", y=-0.25,
    xanchor="center", x=0.5,
    font=dict(size=12),
    groupclick="togglegroup",
)
PLOTLY_XAXIS = dict(
    title="Cohorte", type="category", tickangle=0,
    showgrid=False, linecolor="#b8b6ac", tickfont=dict(size=12),
)
PLOTLY_YAXIS = dict(
    title="% de titulación", range=[ESCALA_Y_MIN, ESCALA_Y_MAX],
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


def grafico_lineas(df_wide, colores, height=420, width=760, series_ocultas=None, **_ignorado):
    series_ocultas = series_ocultas or []
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
            visible="legendonly" if col in series_ocultas else True,
            hovertemplate="%{fullData.name}: %{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(**_layout_base(height, width))
    st.plotly_chart(fig, use_container_width=False)


# =========================================================
# 2. FUNCIONES DE SIMULACIÓN (idénticas a Retención 1er Año)
# =========================================================
def proyeccion_promedio_movil(valores, anios, n_futuro, ventana=3):
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
    x = np.array(anios)
    y = np.array(valores)
    coef = np.polyfit(x, y, 1)
    modelo = np.poly1d(coef)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    resultado = [modelo(a) for a in anios_futuros]
    return anios_futuros, resultado


def proyeccion_regresion_lineal_anclada(valores, anios, n_futuro):
    x = np.array(anios)
    y = np.array(valores)
    coef = np.polyfit(x, y, 1)
    pendiente = coef[0]
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    ultimo_valor = valores[-1]
    resultado = [ultimo_valor + pendiente * i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado


def proyeccion_meta(valores, anios, n_futuro, valor_objetivo):
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    ultimo_valor = valores[-1]
    paso = (valor_objetivo - ultimo_valor) / n_futuro
    resultado = [ultimo_valor + paso * i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado


def proyeccion_tendencia_porcentual(valores, anios, n_futuro, ventana_tasas=None):
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


METODOS = {
    "Promedio móvil (últimos 3 años)": "pm3",
    "Regresión lineal (ajuste global)": "reg",
    "Regresión lineal (anclada al último año)": "reg_anclada",
    "Tendencia (% de crecimiento promedio)": "tend",
    "Meta personalizada": "meta",
    "Proyección manual": "manual",
}


def calcular_proyeccion(metodo_key, valores, anios, n_futuro, ventana=3, ventana_tend=None, valor_meta=None, objetivo_forzado=None):
    if objetivo_forzado is not None:
        # Regla de convergencia: la proyección de este grupo (Mujeres/Hombres)
        # debe llegar exactamente al mismo valor que la proyección General
        # con este mismo método en el último año. Se calcula la diferencia
        # entre ese valor objetivo y el último dato real de este grupo, se
        # reparte en partes iguales entre los años a proyectar, y se va
        # sumando ese incremento fijo cada año a partir del último valor real.
        anios_f = [anios[-1] + i for i in range(1, n_futuro + 1)]
        ultimo_valor = valores[-1]
        incremento_anual = (objetivo_forzado - ultimo_valor) / n_futuro
        vals_f = [ultimo_valor + incremento_anual * i for i in range(1, n_futuro + 1)]
        nota = (
            f"Se distribuye en partes iguales la diferencia entre el valor que da la "
            f"proyección General con este método en {anios_f[-1]} ({objetivo_forzado:.1f}%) y el "
            f"último dato real de este grupo ({ultimo_valor:.1f}%): {incremento_anual:+.2f}pp por año, "
            f"hasta llegar exactamente a {objetivo_forzado:.1f}% en {anios_f[-1]}."
        )
        return anios_f, vals_f, nota
    if metodo_key == "pm3":
        anios_f, vals_f = proyeccion_promedio_movil(valores, anios, n_futuro, ventana)
        nota = f"Promedio móvil con ventana de {ventana} años."
    elif metodo_key == "reg":
        anios_f, vals_f = proyeccion_regresion_lineal(valores, anios, n_futuro)
        nota = "Ajuste por regresión lineal (mínimos cuadrados) sobre todo el histórico."
    elif metodo_key == "reg_anclada":
        anios_f, vals_f = proyeccion_regresion_lineal_anclada(valores, anios, n_futuro)
        nota = "Regresión lineal anclada al último valor real, proyectada con la pendiente del histórico."
    elif metodo_key == "meta":
        anios_f, vals_f = proyeccion_meta(valores, anios, n_futuro, valor_meta)
        nota = (
            f"Trayectoria lineal que apunta a alcanzar {valor_meta:.1f}% "
            f"en {n_futuro} año(s), con incremento anual constante."
        )
    elif metodo_key == "tend":
        anios_f, vals_f, tasa = proyeccion_tendencia_porcentual(valores, anios, n_futuro, ventana_tend)
        alcance = f"últimas {ventana_tend} tasas interanuales" if ventana_tend else "todas las tasas interanuales del histórico"
        nota = f"Tasa de crecimiento promedio aplicada: {tasa*100:.2f}% anual (calculada sobre {alcance})."
    elif metodo_key == "manual":
        raise ValueError("Falta ingresar la proyección manual en el modo General")
    else:
        raise ValueError("Método no reconocido")
    return anios_f, vals_f, nota


# =========================================================
# 3. INTERFAZ - BARRA LATERAL
# =========================================================
st.sidebar.title("⚙️ Configuración")

modo = st.sidebar.radio(
    "Modo de simulación",
    ["General (sin separar por sexo)", "Mujeres", "Hombres"],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Proyección")
n_futuro = st.sidebar.slider("Cohortes a proyectar", min_value=1, max_value=5, value=5)

metodo_nombre = st.sidebar.selectbox("Método de simulación", list(METODOS.keys()))
metodo_key = METODOS[metodo_nombre]
st.sidebar.caption(
    "💡 Datos no estacionarios (con tendencia): se recomienda priorizar "
    "Regresión lineal o Tendencia (%)."
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

valor_meta = None
if metodo_key == "meta" or comparar_todos:
    valor_meta = st.sidebar.slider(
        "Meta personalizada (% de titulación objetivo)",
        min_value=0.0, max_value=100.0, value=50.0, step=0.5,
        help="Valor que se busca alcanzar exactamente en el último año proyectado.",
    )

# =========================================================
# 4. CARGA DE DATOS
# =========================================================
def _widget_manual_general(anios, valores, n_futuro, key_suffix=""):
    """Tabla editable para ingresar la Proyección manual de General. Se puede
    llamar tanto desde la vista de un solo método como desde 'comparar
    todos'; ambas comparten el mismo valor guardado en session_state, así
    que editar en una se refleja en la otra."""
    st.markdown(
        "✏️ **Edita directamente los valores proyectados** para la Proyección "
        "manual (se refleja también en Mujeres y Hombres):"
    )
    anios_f = [anios[-1] + i for i in range(1, n_futuro + 1)]
    valores_previos = st.session_state.get("manual_general_valores")
    if not valores_previos or len(valores_previos) != n_futuro:
        valores_previos = [valores[-1]] * n_futuro
    df_manual_editado = st.data_editor(
        pd.DataFrame({"Cohorte": anios_f, "% de titulación proyectada": valores_previos}),
        use_container_width=False,
        hide_index=True,
        key=f"editor_manual_general_{n_futuro}_{key_suffix}",
        disabled=["Cohorte"],
        column_config={
            "% de titulación proyectada": st.column_config.NumberColumn(
                "% de titulación proyectada", format="%.1f%%",
            ),
        },
    )
    vals_f = df_manual_editado["% de titulación proyectada"].tolist()
    st.session_state["manual_general_valores"] = vals_f
    st.session_state["manual_general_anios"] = anios_f
    return anios_f, vals_f


def _filtrar_por_sexo(sexo):
    """Extrae el histórico de titulación de un sexo específico, con la
    misma forma (Cohorte + "% de titulación") que usa el resto del script."""
    return (
        datos_sexo[datos_sexo["Sexo"] == sexo][["Cohorte", "% de titulación"]]
        .reset_index(drop=True)
    )


if modo.startswith("General"):
    df_entrada = datos_general
    titulo_modo = "General"
elif modo == "Mujeres":
    df_entrada = _filtrar_por_sexo("Mujer")
    titulo_modo = "Mujeres"
else:
    df_entrada = _filtrar_por_sexo("Hombre")
    titulo_modo = "Hombres"

anios = df_entrada["Cohorte"].tolist()
valores = df_entrada["% de titulación"].tolist()

objetivos_forzados_modo = {}
if not modo.startswith("General"):
    anios_general = datos_general["Cohorte"].tolist()
    valores_general = datos_general["% de titulación"].tolist()
    for nombre, key in METODOS.items():
        if key == "manual":
            valores_manual = st.session_state.get("manual_general_valores")
            if valores_manual and len(valores_manual) == n_futuro:
                objetivos_forzados_modo[nombre] = valores_manual[-1]
            continue  # si aún no se ingresó la proyección manual en General, se deja sin forzar
        try:
            _, vals_f_general, _ = calcular_proyeccion(
                key, valores_general, anios_general, n_futuro, ventana, ventana_tend, valor_meta
            )
            objetivos_forzados_modo[nombre] = vals_f_general[-1]  # valor de General en el último año proyectado
        except Exception:
            pass  # si un método falla para General, se deja sin forzar (usa su propia lógica)

# =========================================================
# 5. DATOS HISTÓRICOS
# =========================================================
st.subheader(f"📁 Datos históricos — {titulo_modo}")
col_tabla, col_grafico = st.columns([1, 2])
with col_tabla:
    st.dataframe(
        df_entrada,
        use_container_width=False,
        hide_index=True,
        column_config={"% de titulación": st.column_config.NumberColumn("% de titulación", format="%.1f%%")},
    )
with col_grafico:
    grafico_lineas(df_entrada.set_index("Cohorte")[["% de titulación"]], colores=[COLOR_ACENTO])

# =========================================================
# 6. PROYECCIÓN
# =========================================================
st.subheader(f"🔮 Proyección — {titulo_modo}")

if comparar_todos:
    if titulo_modo == "General":
        _widget_manual_general(anios, valores, n_futuro, key_suffix="comparar")
    df_comp = pd.DataFrame({"Cohorte": anios, "Histórico UAH": valores})
    notas = []
    df_futuro = None
    for nombre, key in METODOS.items():
        try:
            if key == "manual" and titulo_modo == "General":
                valores_manual = st.session_state.get("manual_general_valores")
                if not valores_manual or len(valores_manual) != n_futuro:
                    raise ValueError("aún no ingresado en la vista de un solo método")
                anios_f = st.session_state.get("manual_general_anios")
                vals_f = valores_manual
                nota = "Valores ingresados manualmente (ver vista de un solo método para editarlos)."
            else:
                anios_f, vals_f, nota = calcular_proyeccion(
                    key, valores, anios, n_futuro, ventana, ventana_tend, valor_meta,
                    objetivo_forzado=objetivos_forzados_modo.get(nombre),
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
    metodos_presentes = [n for n in METODOS.keys() if n in df_comp.columns]
    orden_cols = ["Histórico UAH"] + metodos_presentes
    colores_cols = [COLOR_TEXTO] + PALETA_METODOS[1: 1 + len(metodos_presentes)]
    df_comp = df_comp[["Cohorte"] + orden_cols]

    activas_por_defecto_comparar = {
        "Histórico UAH",
        "Regresión lineal (anclada al último año)",
        "Tendencia (% de crecimiento promedio)",
        "Meta personalizada",
    }

    # --- Versión anterior: se mostraban todas las columnas/curvas y las
    # --- inactivas quedaban ocultas pero disponibles con un clic en la
    # --- leyenda (series_ocultas). Se deja comentado por si se quiere
    # --- volver a habilitar esa opción.
    # col_config = {
    #     col: st.column_config.NumberColumn(col, format="%.1f%%")
    #     for col in df_comp.columns if col != "Cohorte"
    # }
    # st.dataframe(df_comp, use_container_width=False, hide_index=True, column_config=col_config)
    # series_ocultas_comparar = [c for c in orden_cols if c not in activas_por_defecto_comparar]
    # grafico_lineas(
    #     df_comp.set_index("Cohorte"), colores=colores_cols, width=760,
    #     series_ocultas=series_ocultas_comparar,
    # )

    # Ahora: solo se muestran (tabla y gráfico) las columnas activas por
    # defecto; el resto ni siquiera se dibuja/lista.
    orden_cols_activas = [c for c in orden_cols if c in activas_por_defecto_comparar]
    colores_cols_activas = [
        color for col, color in zip(orden_cols, colores_cols) if col in activas_por_defecto_comparar
    ]
    df_comp = df_comp[["Cohorte"] + orden_cols_activas]
    col_config = {
        col: st.column_config.NumberColumn(col, format="%.1f%%")
        for col in df_comp.columns if col != "Cohorte"
    }
    st.dataframe(df_comp, use_container_width=False, hide_index=True, column_config=col_config)
    grafico_lineas(
        df_comp.set_index("Cohorte"), colores=colores_cols_activas, width=760,
    )

    st.markdown("**Notas de cada método:**")
    st.markdown("\n".join(notas))

    st.markdown("#### 📋 Tabla resumen — valor proyectado por cohorte y método")
    if df_futuro is None:
        st.warning("No fue posible calcular ningún método con los datos actuales.")
    else:
        df_futuro = df_futuro.reset_index().rename(columns={"index": "Cohorte"}).sort_values("Cohorte")
        # Se deja solo con los métodos activos por defecto (mismo criterio que el gráfico/tabla de arriba).
        metodos_activos_presentes = [c for c in df_futuro.columns if c != "Cohorte" and c in activas_por_defecto_comparar]
        df_futuro = df_futuro[["Cohorte"] + metodos_activos_presentes]
        col_config_futuro = {
            col: st.column_config.NumberColumn(col, format="%.1f%%")
            for col in df_futuro.columns if col != "Cohorte"
        }
        st.dataframe(df_futuro, use_container_width=False, hide_index=True, column_config=col_config_futuro)

        csv = df_futuro.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla de proyecciones (CSV)",
            data=csv,
            file_name=f"proyeccion_comparacion_titulacion_{titulo_modo.lower()}.csv",
            mime="text/csv",
        )
else:
    if metodo_key == "manual" and titulo_modo == "General":
        anios_f, vals_f = _widget_manual_general(anios, valores, n_futuro, key_suffix="single")
        nota = "Proyección ingresada manualmente para General. Este mismo escenario se refleja en Mujeres y Hombres, cada uno convergiendo al valor final que definas aquí."
    elif metodo_key == "manual" and titulo_modo != "General":
        objetivo = objetivos_forzados_modo.get(metodo_nombre)
        if objetivo is None:
            st.warning(
                "Todavía no has ingresado la proyección manual en el modo **General**. "
                "Ve a General, elige 'Proyección manual' y define los valores; "
                "luego vuelve aquí para ver el escenario equivalente."
            )
            st.stop()
        anios_f, vals_f, nota = calcular_proyeccion(
            metodo_key, valores, anios, n_futuro, ventana, ventana_tend, valor_meta,
            objetivo_forzado=objetivo,
        )
    else:
        anios_f, vals_f, nota = calcular_proyeccion(
            metodo_key, valores, anios, n_futuro, ventana, ventana_tend, valor_meta,
            objetivo_forzado=objetivos_forzados_modo.get(metodo_nombre),
        )
    df_proy = pd.DataFrame({"Cohorte": anios_f, "% de titulación proyectada": vals_f})
    st.info(nota)

    df_hist_plot = df_entrada.rename(columns={"% de titulación": "Histórico UAH"})
    df_proy_plot = df_proy.rename(columns={"% de titulación proyectada": "Proyección"})
    df_final = pd.merge(
        df_hist_plot[["Cohorte", "Histórico UAH"]],
        df_proy_plot[["Cohorte", "Proyección"]],
        on="Cohorte",
        how="outer",
    ).sort_values("Cohorte")
    grafico_lineas(df_final.set_index("Cohorte")[["Histórico UAH", "Proyección"]], colores=[COLOR_TEXTO, COLOR_ACENTO])

    st.markdown("#### 📋 Tabla resumen — valor proyectado por cohorte")
    st.dataframe(
        df_proy,
        use_container_width=False,
        hide_index=True,
        column_config={
            "% de titulación proyectada": st.column_config.NumberColumn("% de titulación proyectada", format="%.1f%%")
        },
    )

    csv = pd.concat(
        [
            df_entrada.assign(Tipo="Histórico"),
            df_proy.rename(columns={"% de titulación proyectada": "% de titulación"}).assign(Tipo="Proyección"),
        ],
        ignore_index=True,
    ).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar histórico + proyección (CSV)",
        data=csv,
        file_name=f"proyeccion_titulacion_{titulo_modo.lower()}.csv",
        mime="text/csv",
    )

st.markdown("---")
with st.expander("ℹ️ Descripción de los métodos de simulación disponibles"):
    st.markdown(
        """
- **Promedio móvil (últimos 3 años):** promedia los valores más recientes para
  suavizar variaciones puntuales. Al no capturar tendencia, en series con
  tendencia sostenida tiende a subestimar (o sobreestimar) el futuro.
- **Regresión lineal (ajuste global):** ajusta una línea recta a todo el
  histórico y la extiende hacia adelante. Recomendado cuando hay una
  tendencia clara y sostenida.
- **Regresión lineal (anclada al último año):** usa la misma pendiente que la
  regresión global, pero arranca exactamente desde el último valor real, sin
  salto.
- **Tendencia (% de crecimiento promedio):** calcula la variación porcentual
  promedio año a año y la aplica de forma compuesta hacia el futuro. Por
  defecto usa todo el histórico, pero puede limitarse a las últimas N
  variaciones interanuales desde la barra lateral.
- **Meta personalizada:** traza una línea recta desde el último valor real
  hasta el valor objetivo que definas en la barra lateral, de modo que esa
  meta se alcance justo en el último año proyectado. El incremento anual es
  siempre el mismo. Útil para visualizar qué ritmo de mejora se necesitaría
  para llegar a una meta institucional (ej. Metas 2027), más que para
  predecir lo que probablemente ocurrirá.
        """
    )
