"""
Página de Inicio — Plataforma de Simuladores UAH
--------------------------------------------------
Este es el archivo raíz de la app multi-página de Streamlit. Al convertir el
proyecto en multi-página, este script pasa a ser el punto de entrada (la
"página de inicio"), y las demás páginas (como el simulador) viven dentro de
la carpeta `pages/`.

Estructura de carpetas esperada:

    tu_carpeta/
    ├── Inicio.py            <- este archivo
    ├── UAH-logo.png         <- el logo (debe estar aquí, junto a Inicio.py)
    ├── .streamlit/
    │   └── config.toml
    └── pages/
        └── simulador_metas.py   <- (u otras páginas que agregues)

IMPORTANTE: si el script de una página dentro de `pages/` busca el logo con
`Path(__file__).parent / "UAH-logo.png"`, va a buscarlo DENTRO de `pages/`,
no en la raíz. Para que el logo también se vea en esas páginas, cualquiera
de estas dos opciones funciona:
  1) Dejar una copia de "UAH-logo.png" también dentro de `pages/`, o
  2) Cambiar esa línea por `Path(__file__).parent.parent / "UAH-logo.png"`
     en los scripts que estén dentro de `pages/`.
"""

import base64
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Inicio — UAH", layout="wide", page_icon="🎓")

# =========================================================
# TEMA INSTITUCIONAL (colores UAH) — mismo tema que el resto de la app
# =========================================================
COLOR_FONDO = "#ecebe5"
COLOR_TEXTO = "#000000"
COLOR_ACENTO = "#ff6f43"
COLOR_BLANCO = "#ffffff"

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
        padding: 1.4rem 1.6rem;
        border: 1px solid #ddd9cd;
        height: 100%;
    }}
    .uah-card-title {{
        margin-top: 0;
        font-size: 1.25rem;
        font-weight: 700;
        line-height: 1.3;
    }}
    .uah-card-accent {{
        border-left: 4px solid {COLOR_ACENTO};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_base64():
    """Lee el logo UAH desde disco (misma carpeta que este script) y lo
    entrega en base64. Si no encuentra el archivo, retorna None y el
    encabezado se muestra sin logo."""
    ruta = Path(__file__).parent / "UAH-logo.png"
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
            <div style="color:{COLOR_BLANCO}; font-size:1.6rem; font-weight:700; line-height:1.3;">Plataforma de Simuladores</div>
            <div style="color:{COLOR_BLANCO}; opacity:0.9;">Universidad Alberto Hurtado</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CONTENIDO — Página de inicio
# =========================================================
st.markdown("## Bienvenido/a")
st.markdown(
    """
Esta plataforma reúne las herramientas de simulación y proyección de
indicadores institucionales de la Universidad Alberto Hurtado.

Usa el **menú de la izquierda** para navegar entre las páginas disponibles.
    """
)

st.markdown("### Herramientas disponibles")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="uah-card uah-card-accent">
            <div class="uah-card-title">📊 Retención 1er Año</div>
            <p>Proyecta el cumplimiento de metas de Retención 1er Año a
            futuro, en modo General o desagregado por sexo, comparando
            distintos métodos de simulación.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="uah-card uah-card-accent">
            <div class="uah-card-title">📊 Retención 3er Año</div>
            <p>Proyecta el cumplimiento de metas de Retención 3er Año a
            futuro, en modo General o desagregado por sexo, comparando
            distintos métodos de simulación.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="uah-card uah-card-accent">
            <div class="uah-card-title">🎓 Titulación Oportuna</div>
            <p>Proyecta el cumplimiento de metas de Titulación Oportuna a
            futuro, en modo General o desagregado por sexo, comparando
            distintos métodos de simulación.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption("Universidad Alberto Hurtado — Plataforma interna de simuladores.")
