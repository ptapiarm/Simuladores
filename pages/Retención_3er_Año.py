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
ANIOS_HIST = [2019,2020, 2021, 2022, 2023]

# Modo GENERAL (sin separar por sexo)
datos_general = pd.DataFrame({
    "Cohorte": ANIOS_HIST,
    "% de retención": [70.5, 69.5, 67.8, 67.8, 67.8],
})

# Modo POR SEXO
datos_sexo = pd.DataFrame({
    "Cohorte": ANIOS_HIST * 2,
    "Sexo": ["Hombre"] * 5 + ["Mujer"] * 5,
    "% de retención": [67.0, 65.1, 64.6, 63.3, 64.4,   # Hombres
              73.6, 72.9, 70.1, 70.5, 70.3],  # Mujeres
})

# Curva de comparación / referencia — sistema universitario completo (Datos SIES)
NOMBRE_SIES = "Universidades-Datos Sies"
ANIOS_SIES = [2021, 2022, 2023]

datos_general_sies = pd.DataFrame({
    "Cohorte": ANIOS_SIES,
    "% de retención": [50,50,50],
})

datos_sexo_sies = pd.DataFrame({
    "Cohorte": ANIOS_SIES * 2,
    "Sexo": ["Mujer"] * 3 + ["Hombre"] * 3,
    "% de retención": [   50,50,50, # Mujeres
              50,50,50],  # Hombres
})


# =========================================================
# 1B. GRÁFICOS — helper con escala de eje Y fija
# =========================================================
ESCALA_Y_MIN = 50
ESCALA_Y_MAX = 100


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


def grafico_lineas(df_wide, colores, height=400, width=560, series_ocultas=None, **_ignorado):
    """Dibuja un gráfico de líneas (Plotly) a partir de un DataFrame ancho
    (índice = Cohorte, una columna por serie), con el eje Y fijo entre
    ESCALA_Y_MIN y ESCALA_Y_MAX, puntos marcados en cada año y los colores
    indicados en el mismo orden que las columnas. Cada curva se puede
    activar/desactivar haciendo clic en su nombre en la leyenda.
    `series_ocultas`: nombres de columnas que deben partir apagadas
    (visibles solo al hacer clic en la leyenda), sin dejar de estar
    disponibles para el usuario."""
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
    """Opción 1: Ajuste global (mínimos cuadrados).
    La recta se calcula para representar lo mejor posible TODOS los años del
    histórico en conjunto. No necesariamente pasa por el último valor real."""
    x = np.array(anios)
    y = np.array(valores)
    coef = np.polyfit(x, y, 1)  # pendiente, intercepto
    modelo = np.poly1d(coef)
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    resultado = [modelo(a) for a in anios_futuros]
    return anios_futuros, resultado


def proyeccion_regresion_lineal_anclada(valores, anios, n_futuro):
    """Opción 2: Ajuste anclado al último año real.
    Usa la misma pendiente (tasa de cambio promedio) que calcula la regresión
    con todo el histórico, pero la proyección arranca exactamente desde el
    último valor real, sin salto, y sube (o baja) de forma constante según
    esa pendiente."""
    x = np.array(anios)
    y = np.array(valores)
    coef = np.polyfit(x, y, 1)  # pendiente, intercepto
    pendiente = coef[0]
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    ultimo_valor = valores[-1]
    resultado = [ultimo_valor + pendiente * i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado


def proyeccion_crecimiento_fijo(valores, anios, n_futuro, incremento):
    """Aplica un incremento fijo (en puntos porcentuales) cada año, a partir
    del último valor real. Útil cuando el histórico es muy parejo y no hay
    una tendencia clara que proyectar: en vez de inventar una tasa, se fija
    de antemano cuánto se quiere crecer cada año."""
    anios_futuros = [anios[-1] + i for i in range(1, n_futuro + 1)]
    ultimo_valor = valores[-1]
    resultado = [ultimo_valor + incremento * i for i in range(1, n_futuro + 1)]
    return anios_futuros, resultado


METODOS = {
    "Promedio móvil (últimos 3 años)": "pm3",
    "Regresión lineal (ajuste global)": "reg",
    "Regresión lineal (anclada al último año)": "reg_anclada",
    "Crecimiento fijo +1 pp/año": "crec_1",
    "Crecimiento fijo +1.5 pp/año": "crec_15",
    "Crecimiento fijo +2 pp/año": "crec_2",
    "Proyección manual": "manual",
}


def calcular_proyeccion(metodo_key, valores, anios, n_futuro, ventana=3, ventana_tend=None, objetivo_forzado=None):
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
    elif metodo_key == "crec_1":
        anios_f, vals_f = proyeccion_crecimiento_fijo(valores, anios, n_futuro, 1.0)
        nota = "Crecimiento fijo de +1 punto porcentual por año, a partir del último valor real."
    elif metodo_key == "crec_15":
        anios_f, vals_f = proyeccion_crecimiento_fijo(valores, anios, n_futuro, 1.5)
        nota = "Crecimiento fijo de +1.5 puntos porcentuales por año, a partir del último valor real."
    elif metodo_key == "crec_2":
        anios_f, vals_f = proyeccion_crecimiento_fijo(valores, anios, n_futuro, 2.0)
        nota = "Crecimiento fijo de +2 puntos porcentuales por año, a partir del último valor real."
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
    "💡 Histórico muy parejo (sin tendencia clara): se incluyeron tres "
    "escenarios de crecimiento fijo (+1, +1.5 y +2 puntos porcentuales por "
    "año) para simular distintos ritmos de mejora, además de Promedio móvil "
    "y Regresión lineal."
)

comparar_todos = st.sidebar.checkbox("Comparar todos los métodos a la vez", value=False)

ventana = 3
if metodo_key == "pm3" or comparar_todos:
    ventana = st.sidebar.slider("Ventana del promedio móvil (años)", 2, 5, 3)

ventana_tend = None


# =========================================================
# 4. CARGA DE DATOS
# =========================================================
def _filtrar_por_sexo(sexo):
    """Extrae el histórico UAH de un sexo específico, con la misma forma
    (Cohorte + "% de retención") que espera mostrar_bloque_general."""
    return (
        datos_sexo[datos_sexo["Sexo"] == sexo][["Cohorte", "% de retención"]]
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


# =========================================================
# 5. MODO GENERAL
# =========================================================
COLOR_SIES = "#8c8c8c"


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
        pd.DataFrame({"Cohorte": anios_f, "% de retención proyectada": valores_previos}),
        use_container_width=False,
        hide_index=True,
        key=f"editor_manual_general_{n_futuro}_{key_suffix}",
        disabled=["Cohorte"],
        column_config={
            "% de retención proyectada": st.column_config.NumberColumn(
                "% de retención proyectada", format="%.1f%%",
            ),
        },
    )
    vals_f = df_manual_editado["% de retención proyectada"].tolist()
    st.session_state["manual_general_valores"] = vals_f
    st.session_state["manual_general_anios"] = anios_f
    return anios_f, vals_f


def mostrar_bloque_general(df, titulo="General", mostrar_grafico_historico=True, df_sies=None, objetivos_forzados=None):
    objetivos_forzados = objetivos_forzados or {}
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
                df_hist_sies = pd.merge(
                    df.rename(columns={"% de retención": "% de retención"}),
                    df_sies.rename(columns={"% de retención": NOMBRE_SIES}),
                    on="Cohorte", how="outer",
                ).sort_values("Cohorte")
                grafico_lineas(
                    df_hist_sies.set_index("Cohorte")[["% de retención", NOMBRE_SIES]],
                    colores=[COLOR_ACENTO, COLOR_SIES],
                )
            else:
                grafico_lineas(df.set_index("Cohorte")[["% de retención"]], colores=[COLOR_ACENTO])

    anios = df["Cohorte"].tolist()
    valores = df["% de retención"].tolist()

    st.subheader(f"🔮 Proyección — {titulo}")

    if comparar_todos:
        if titulo == "General":
            _widget_manual_general(anios, valores, n_futuro, key_suffix="comparar")
        df_comp = pd.DataFrame({"Cohorte": anios, "Histórico UAH": valores})
        if df_sies is not None:
            df_comp = pd.merge(
                df_comp, df_sies.rename(columns={"% de retención": NOMBRE_SIES}), on="Cohorte", how="outer"
            )
        notas = []
        df_futuro = None
        for nombre, key in METODOS.items():
            try:
                if key == "manual" and titulo == "General":
                    valores_manual = st.session_state.get("manual_general_valores")
                    if not valores_manual or len(valores_manual) != n_futuro:
                        raise ValueError("aún no ingresado en la vista de un solo método")
                    anios_f = st.session_state.get("manual_general_anios")
                    vals_f = valores_manual
                    nota = "Valores ingresados manualmente (ver vista de un solo método para editarlos)."
                else:
                    anios_f, vals_f, nota = calcular_proyeccion(
                        key, valores, anios, n_futuro, ventana, ventana_tend,
                        objetivo_forzado=objetivos_forzados.get(nombre),
                    )
                serie = pd.Series(
                    [np.nan] * (len(anios) - 1) + [valores[-1]] + list(vals_f),
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
        if df_sies is not None:
            orden_cols += [NOMBRE_SIES]
            colores_cols += [COLOR_SIES]
        metodos_presentes = [n for n in METODOS.keys() if n in df_comp.columns]
        orden_cols += metodos_presentes
        # Se evita el gris (#8c8c8c), reservado para la curva SIES, en los colores de método.
        # Se cicla la paleta por si hay más métodos que colores disponibles.
        paleta_metodos_disponible = [c for c in PALETA_METODOS if c != COLOR_SIES][1:]
        colores_cols += [
            paleta_metodos_disponible[i % len(paleta_metodos_disponible)]
            for i in range(len(metodos_presentes))
        ]
        df_comp = df_comp[["Cohorte"] + orden_cols]

        activas_por_defecto_comparar = {
            "Histórico UAH",
            "Regresión lineal (anclada al último año)",
            "Crecimiento fijo +1 pp/año",
            "Crecimiento fijo +1.5 pp/año",
            "Crecimiento fijo +2 pp/año",
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
        #     df_comp.set_index("Cohorte"), colores=colores_cols,
        #     width=760, legend_columns=2, legend_label_limit=320,
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
            df_comp.set_index("Cohorte"), colores=colores_cols_activas,
            width=760, legend_columns=2, legend_label_limit=320,
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
                file_name=f"proyeccion_comparacion_{titulo.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )
    else:
        datos_manual_incompletos = False
        if metodo_key == "manual" and titulo == "General":
            anios_f, vals_f = _widget_manual_general(anios, valores, n_futuro, key_suffix="single")
            nota = "Proyección ingresada manualmente para General. Este mismo escenario se refleja en Mujeres y Hombres, cada uno convergiendo al valor final que definas aquí."
        elif metodo_key == "manual" and titulo != "General":
            objetivo = objetivos_forzados.get(metodo_nombre)
            if objetivo is None:
                st.warning(
                    "Todavía no has ingresado la proyección manual en el modo **General**. "
                    "Ve a General, elige 'Proyección manual' y define los valores; "
                    "luego vuelve aquí para ver el escenario equivalente."
                )
                datos_manual_incompletos = True
                anios_f, vals_f, nota = [], [], ""
            else:
                anios_f, vals_f, nota = calcular_proyeccion(
                    metodo_key, valores, anios, n_futuro, ventana, ventana_tend,
                    objetivo_forzado=objetivo,
                )
        else:
            anios_f, vals_f, nota = calcular_proyeccion(
                metodo_key, valores, anios, n_futuro, ventana, ventana_tend,
                objetivo_forzado=objetivos_forzados.get(metodo_nombre),
            )

        if datos_manual_incompletos:
            return

        df_proy = pd.DataFrame({"Cohorte": anios_f, "% de retención proyectada": vals_f})
        if nota:
            st.info(nota)

        df_hist_plot = df.rename(columns={"% de retención": "Histórico UAH"})
        df_proy_plot = pd.DataFrame({
            "Cohorte": [anios[-1]] + anios_f,
            "Proyección": [valores[-1]] + list(vals_f),
        })
        df_final = pd.merge(
            df_hist_plot[["Cohorte", "Histórico UAH"]],
            df_proy_plot.rename(columns={"Cohorte": "Cohorte"})[["Cohorte", "Proyección"]],
            on="Cohorte",
            how="outer",
        ).sort_values("Cohorte")
        columnas_chart = ["Histórico UAH", "Proyección"]
        colores_chart = [COLOR_TEXTO, COLOR_ACENTO]
        if df_sies is not None:
            df_final = pd.merge(
                df_final, df_sies.rename(columns={"% de retención": NOMBRE_SIES}), on="Cohorte", how="outer"
            ).sort_values("Cohorte")
            columnas_chart.append(NOMBRE_SIES)
            colores_chart.append(COLOR_SIES)
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
# 6. EJECUCIÓN SEGÚN MODO
# =========================================================
objetivos_forzados_modo = None
if not modo.startswith("General"):
    anios_general = datos_general["Cohorte"].tolist()
    valores_general = datos_general["% de retención"].tolist()
    objetivos_forzados_modo = {}
    for nombre, key in METODOS.items():
        if key == "manual":
            valores_manual = st.session_state.get("manual_general_valores")
            if valores_manual and len(valores_manual) == n_futuro:
                objetivos_forzados_modo[nombre] = valores_manual[-1]
            continue  # si aún no se ingresó la proyección manual en General, se deja sin forzar
        try:
            _, vals_f_general, _ = calcular_proyeccion(key, valores_general, anios_general, n_futuro, ventana, ventana_tend)
            objetivos_forzados_modo[nombre] = vals_f_general[-1]  # valor de General en el último año proyectado
        except Exception:
            pass  # si un método falla para General, se deja sin forzar (usa su propia lógica)

mostrar_bloque_general(
    df_entrada, titulo=titulo_modo, df_sies=None,
    objetivos_forzados=objetivos_forzados_modo,
)

st.markdown("---")
with st.expander("ℹ️ Descripción de los métodos de simulación disponibles"):
    st.markdown(
        """
- **Promedio móvil (últimos 3 años):** promedia los valores más recientes para
  suavizar variaciones puntuales. Al no capturar tendencia, en series con
  tendencia sostenida tiende a subestimar (o sobreestimar) el futuro.
- **Regresión lineal (ajuste global):** ajusta la recta que mejor representa
  todo el histórico en conjunto (mínimos cuadrados) y la extiende hacia
  adelante. Como no está obligada a pasar por el último año, puede haber un
  pequeño salto entre el histórico y el primer año proyectado.
- **Regresión lineal (anclada al último año):** usa la misma pendiente que la
  regresión anterior, pero la proyección arranca exactamente desde el
  último valor real, sin salto.
- **Crecimiento fijo +1 pp/año**, **+1.5 pp/año** y **+2 pp/año:** en vez
  de calcular una tendencia a partir del histórico, suman un incremento fijo
  (1, 1.5 o 2 puntos porcentuales) cada año, a partir del último valor real.
  Se agregaron porque el histórico de este indicador es muy parejo (sin una
  tendencia clara que proyectar), así que en vez de forzar una tasa
  calculada, permiten comparar directamente distintos ritmos de mejora
  hipotéticos.
        """
    )
