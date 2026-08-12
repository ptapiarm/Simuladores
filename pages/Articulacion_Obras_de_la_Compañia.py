"""
Articulación con Obras de la Compañía — Proyección por regresión
--------------------------------------------------------------------
App en Streamlit que proyecta, año a año, 4 datos crudos (sin normalizar,
sin ponderar, sin combinar en un índice):

  - Iniciativas:      N° total de iniciativas conjuntas UAH-Obras.
  - Instituciones:    N° de obras/instituciones distintas como contraparte.
  - Participación UAH: N° de estudiantes UAH (pregrado/posgrado) que
                        participaron (prestan el servicio).
  - Beneficiarios:    N° de personas destinatarias externas que reciben
                        el servicio (no pide meta, se proyecta solo con
                        la tendencia real 2024→2025).

Para Iniciativas, Instituciones y Participación UAH, tú defines una META
para un año futuro; la app ajusta una regresión lineal (mínimos cuadrados)
que pasa por 2024 (real), 2025 (real) y tu meta, y completa los años
intermedios con esa recta.

Datos reales extraídos del informe "Colaboraciones UAH - Obras Sociales de
la Compañía de Jesús (2024-2025)".
"""

import base64
from pathlib import Path

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Índice de Articulación — UAH", layout="wide", page_icon="🎓")

# =========================================================
# 0. TEMA INSTITUCIONAL (colores UAH) Y ENCABEZADO CON LOGO
# =========================================================
COLOR_FONDO = "#ecebe5"
COLOR_TEXTO = "#000000"
COLOR_ACENTO = "#ff6f43"
COLOR_BLANCO = "#ffffff"

# Colores por sub-indicador (dentro de la paleta institucional)
COLOR_PROFUNDIDAD = "#ff6f43"
COLOR_AMPLITUD = "#4d4d4d"
COLOR_PARTICIPACION = "#c9542b"
COLOR_INDICE = "#000000"

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
    .uah-card {{
        background-color: {COLOR_BLANCO};
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        border: 1px solid #ddd9cd;
        text-align: center;
    }}
    .uah-card .valor {{
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }}
    .uah-card .etiqueta {{
        font-size: 0.85rem;
        opacity: 0.75;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_base64():
    """Lee el logo UAH desde disco (una carpeta arriba, en la raíz del
    proyecto, ya que este script vive dentro de pages/). Si no lo
    encuentra, retorna None y el encabezado se muestra sin logo."""
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
            <div style="color:{COLOR_BLANCO}; font-size:1.6rem; font-weight:700; line-height:1.3;">Índice de Articulación con Obras de la Compañía</div>
            <div style="color:{COLOR_BLANCO}; opacity:0.9;">Universidad Alberto Hurtado</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
# =========================================================
# 1. DATOS BASE (2024 y 2025) — extraídos del informe "Colaboraciones UAH
#    - Obras Sociales de la Compañía de Jesús (2024-2025)". Fijos.
# =========================================================
ANIOS_HIST = [2024, 2025]

# Iniciativas totales conjuntas (Tabla 5 del informe, dato explícito)
INICIATIVAS_TOTALES = {2024: 13, 2025: 25}

# N° de instituciones/obras distintas que aparecen como contraparte
# (definición amplia: incluye obras sociales, educacionales y unidades
# pastorales/relacionadas — Tablas 1 a 4 del informe).
OBRAS_POR_ANIO = {
    2024: ["INFOCAP", "SJM", "Hogar de Cristo", "TECHO", "Fundación Educacional Loyola"],
    2025: [
        "SJM", "Hogar de Cristo", "TECHO", "INFOCAP",
        "Fundación Educacional Alonso de Ovalle", "Centro Vives",
        "Fundación Súmate", "Fondo Esperanza", "Fundación Emplea",
        "Red Juvenil Ignaciana (RJI)", "Capellanía TECHO",
    ],
}
OBRAS_DISTINTAS = {a: len(lista) for a, lista in OBRAS_POR_ANIO.items()}

# Participación de integrantes UAH = suma de "N° est. pregrado/posgrado
# UAH" de cada iniciativa (sumado iniciativa por iniciativa desde las
# Tablas 1 y 2 del informe). Son quienes PRESTAN el servicio.
PARTICIPACION_TOTAL = {2024: 193, 2025: 515}

# Beneficiarios = suma de "N° destinatarias(os)" de cada iniciativa (las
# personas EXTERNAS que reciben el servicio).
BENEFICIARIOS_TOTAL = {2024: 672, 2025: 1179}

profundidad_valor = {
    a: (INICIATIVAS_TOTALES[a] / OBRAS_DISTINTAS[a] if OBRAS_DISTINTAS[a] > 0 else 0.0)
    for a in ANIOS_HIST
}

with st.expander("ℹ️ Qué significa cada dato"):
    st.markdown(
        f"""
- **Iniciativas** = N° total de iniciativas conjuntas UAH-Obras Sociales.
  2024: {INICIATIVAS_TOTALES[2024]}. 2025: {INICIATIVAS_TOTALES[2025]}.
- **Instituciones** = N° de obras/instituciones distintas como contraparte.
  2024: {OBRAS_DISTINTAS[2024]}. 2025: {OBRAS_DISTINTAS[2025]}.
- **Participación UAH** = N° de estudiantes UAH (pregrado/posgrado) que
  participaron — quienes prestan el servicio. 2024: {PARTICIPACION_TOTAL[2024]}.
  2025: {PARTICIPACION_TOTAL[2025]}.
- **Beneficiarios** = N° de personas destinatarias externas que reciben el
  servicio. 2024: {BENEFICIARIOS_TOTAL[2024]}. 2025: {BENEFICIARIOS_TOTAL[2025]}.
- **Profundidad** (referencial) = Iniciativas ÷ Instituciones. 2024:
  {profundidad_valor[2024]:.2f}. 2025: {profundidad_valor[2025]:.2f}.

⚠️ Ninguno de estos números es un conteo de personas únicas — si alguien
participó en 2 iniciativas el mismo año, queda contado 2 veces. Fuente:
informe "Colaboraciones UAH - Obras Sociales de la Compañía de Jesús
(2024-2025)". Instituciones y Participación UAH se reconstruyeron sumando
manualmente las Tablas 1 y 2 del informe (no vienen como total ya
calculado por año).
        """
    )

# =========================================================
# 2. PROYECCIÓN POR REGRESIÓN CON META (barra lateral)
#    Tú defines un año meta y una meta (valor esperado) para cada ítem.
#    Se ajusta una regresión lineal (mínimos cuadrados) que pasa por los
#    3 puntos: 2024 (real), 2025 (real) y año_meta (tu meta), y con esa
#    recta se completan todos los años intermedios.
# =========================================================
st.sidebar.title("📈 Proyección (regresión con meta)")

anio_meta = st.sidebar.number_input(
    "Año meta", min_value=2026, max_value=2035, value=2030, step=1,
)
st.sidebar.caption(
    f"Define tu meta para {anio_meta} en cada ítem — se ajusta una "
    "regresión lineal usando 2024, 2025 y tu meta, y se completan los "
    "años intermedios con esa recta."
)

ITEMS_REGRESION = {
    "Iniciativas": (
        INICIATIVAS_TOTALES,
        INICIATIVAS_TOTALES[2025] + (INICIATIVAS_TOTALES[2025] - INICIATIVAS_TOTALES[2024]) * 5,
    ),
    "Instituciones": (
        OBRAS_DISTINTAS,
        OBRAS_DISTINTAS[2025] + (OBRAS_DISTINTAS[2025] - OBRAS_DISTINTAS[2024]) * 5,
    ),
    "Participación UAH": (
        PARTICIPACION_TOTAL,
        PARTICIPACION_TOTAL[2025] + (PARTICIPACION_TOTAL[2025] - PARTICIPACION_TOTAL[2024]) * 5,
    ),
}

metas = {}
for nombre, (datos_hist, default_meta) in ITEMS_REGRESION.items():
    metas[nombre] = st.sidebar.number_input(
        f"Meta — {nombre} en {anio_meta}",
        min_value=0.0, value=round(float(default_meta), 1), step=1.0,
        key=f"meta_{nombre}",
    )


def _regresion_lineal(xs, ys):
    """Ajuste por mínimos cuadrados (OLS) de una recta y = pendiente*x + intercepto."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    pendiente = num / den if den != 0 else 0.0
    intercepto = my - pendiente * mx
    return pendiente, intercepto


ANIOS_PROY = list(range(2026, anio_meta + 1))
ANIOS_TOTAL = ANIOS_HIST + ANIOS_PROY

# Se ajusta una recta por cada ítem CON meta (Iniciativas, Instituciones,
# Participación UAH), usando 2024, 2025 y la meta que definiste
series = {}
regresion_info = {}
for nombre, (datos_hist, _default) in ITEMS_REGRESION.items():
    xs = [2024, 2025, anio_meta]
    ys = [datos_hist[2024], datos_hist[2025], metas[nombre]]
    pendiente, intercepto = _regresion_lineal(xs, ys)
    regresion_info[nombre] = (pendiente, intercepto)
    serie = dict(datos_hist)  # 2024 y 2025 quedan con el dato REAL, no la recta
    for year in ANIOS_PROY:
        # Son cantidades (iniciativas, instituciones, personas) — se
        # redondean a números enteros, nunca fracciones
        serie[year] = round(max(0.0, pendiente * year + intercepto))
    series[nombre] = serie

# Beneficiarios NO pide meta — se proyecta solo con la tendencia real
# 2024→2025 (línea que pasa exactamente por esos 2 puntos)
pendiente_benef, intercepto_benef = _regresion_lineal(
    [2024, 2025], [BENEFICIARIOS_TOTAL[2024], BENEFICIARIOS_TOTAL[2025]]
)
serie_beneficiarios = dict(BENEFICIARIOS_TOTAL)
for year in ANIOS_PROY:
    serie_beneficiarios[year] = round(max(0.0, pendiente_benef * year + intercepto_benef))
series["Beneficiarios"] = serie_beneficiarios

# Profundidad (referencial) = Iniciativas ÷ Instituciones, derivada de las
# dos series de arriba — no pide meta propia
serie_profundidad = {}
for year in ANIOS_TOTAL:
    ini = series["Iniciativas"][year]
    inst = series["Instituciones"][year]
    serie_profundidad[year] = ini / inst if inst > 0 else 0.0
series["Profundidad"] = serie_profundidad

st.sidebar.caption(f"Proyectando hasta {anio_meta} ({len(ANIOS_PROY)} año(s) después de 2025).")

# =========================================================
# 3. TABLA — proyección por año, sin normalizar ni ponderar
# =========================================================
st.markdown("### 📋 Proyección por año")

filas = []
for year in ANIOS_TOTAL:
    filas.append({
        "Año": year,
        "Proyectado": year not in ANIOS_HIST,
        "Iniciativas": series["Iniciativas"][year],
        "Instituciones": series["Instituciones"][year],
        "Participación UAH": series["Participación UAH"][year],
        "Beneficiarios": series["Beneficiarios"][year],
        "Profundidad (Iniciativas ÷ Instituciones)": series["Profundidad"][year],
    })

datos_calc = pd.DataFrame(filas)
tabla_mostrar = datos_calc.copy()
COLS_ENTERAS = ["Iniciativas", "Instituciones", "Participación UAH", "Beneficiarios"]
tabla_mostrar[COLS_ENTERAS] = tabla_mostrar[COLS_ENTERAS].round(0).astype(int)
tabla_mostrar["Profundidad (Iniciativas ÷ Instituciones)"] = tabla_mostrar[
    "Profundidad (Iniciativas ÷ Instituciones)"
].round(2)
st.dataframe(tabla_mostrar, use_container_width=False, hide_index=True)

