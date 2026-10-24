# ============================================================
# DASHBOARD INTERACTIVO DE VENTAS
# Tecnologías: Python, Streamlit y Plotly Express
# ============================================================

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. ESTILOS CSS
# ============================================================

st.markdown(
    """
    <style>
        .main {
            background-color: #f5f7fb;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1 {
            color: #172554;
            font-weight: 800;
        }

        h2, h3 {
            color: #1e3a5f;
        }

        div[data-testid="stMetric"] {
            background-color: white;
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        div[data-testid="stMetricLabel"] {
            color: #64748b;
        }

        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 700;
        }

        section[data-testid="stSidebar"] {
            background-color: #eef2ff;
        }

        .subtitle {
            color: #64748b;
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }

        .section-description {
            color: #64748b;
            font-size: 0.95rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 3. CARGA DE DATOS
# ============================================================

# Construye la ruta a partir de la ubicación de app.py.
# Así no dependemos de la carpeta desde la que se ejecute
# el comando streamlit run.

RUTA_DATOS = Path(__file__).resolve().parent / "data" / "datos.csv"


@st.cache_data
def cargar_datos(ruta):
    """Carga el CSV y prepara los tipos de datos."""

    df = pd.read_csv(ruta)

    # Eliminar espacios accidentales en los encabezados.
    df.columns = df.columns.str.strip()

    # Comprobar que existan las columnas necesarias.
    columnas_requeridas = [
        "ID_Venta",
        "Fecha",
        "Categoria",
        "Producto",
        "Sucursal",
        "Vendedor",
        "Canal_Venta",
        "Metodo_Pago",
        "Precio_Unitario",
        "Cantidad",
        "Descuento_Pct",
        "Ingresos",
        "Costo_Total",
        "Ganancia",
        "En_Promocion",
        "Cliente_Afiliado"
    ]

    faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan las siguientes columnas en el CSV: "
            + ", ".join(faltantes)
        )

    # Convertir la fecha.
    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    # Convertir las columnas numéricas.
    columnas_numericas = [
        "Precio_Unitario",
        "Cantidad",
        "Descuento_Pct",
        "Ingresos",
        "Costo_Total",
        "Ganancia"
    ]

    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )

    # Convertir las columnas booleanas.
    def convertir_booleano(serie):
        valores = {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "si": True,
            "sí": True,
            "no": False
        }

        return (
            serie.astype(str)
            .str.strip()
            .str.lower()
            .map(valores)
            .fillna(False)
            .astype(bool)
        )

    columnas_booleanas = [
        "En_Promocion",
        "Cliente_Afiliado"
    ]

    for columna in columnas_booleanas:
        df[columna] = convertir_booleano(df[columna])

    # Eliminar registros sin fecha o sin datos numéricos
    # esenciales para los gráficos.
    df = df.dropna(
        subset=[
            "Fecha",
            "Ingresos",
            "Ganancia",
            "Cantidad"
        ]
    )

    return df


# Mostrar un mensaje comprensible si falla la carga.
if not RUTA_DATOS.exists():
    st.error(
        f"No se encontró el archivo de datos: {RUTA_DATOS}"
    )

    st.info(
        "Coloca tu archivo datos.csv dentro de la carpeta "
        "'data', junto al archivo app.py."
    )

    st.stop()


try:
    df = cargar_datos(str(RUTA_DATOS))

except Exception as error:
    st.error(f"No se pudieron cargar los datos: {error}")
    st.stop()


if df.empty:
    st.warning("El archivo CSV no contiene datos válidos.")
    st.stop()


# ============================================================
# 4. ENCABEZADO DEL DASHBOARD
# ============================================================

st.title("🛍️ Dashboard de Ventas | Business Intelligence")

st.markdown(
    """
    <div class="subtitle">
        📊 Analiza el rendimiento comercial, descubre los productos
        más vendidos y explora la rentabilidad de cada sucursal.
        Todo en un solo lugar.
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# 5. BARRA LATERAL: FILTROS
# ============================================================

st.sidebar.title("🎛️ Panel de control")

st.sidebar.markdown(
    "Personaliza el análisis utilizando los siguientes filtros."
)

st.sidebar.divider()


# ------------------------------------------------------------
# Filtro de fechas
# ------------------------------------------------------------

fecha_minima = df["Fecha"].min().date()
fecha_maxima = df["Fecha"].max().date()

rango_fechas = st.sidebar.date_input(
    "📅 Periodo de ventas",
    value=(fecha_minima, fecha_maxima),
    min_value=fecha_minima,
    max_value=fecha_maxima,
    key="filtro_fechas"
)

# date_input puede devolver una o dos fechas.
if isinstance(rango_fechas, (tuple, list)):

    if len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas

    elif len(rango_fechas) == 1:
        fecha_inicio = rango_fechas[0]
        fecha_fin = rango_fechas[0]

    else:
        fecha_inicio = fecha_minima
        fecha_fin = fecha_maxima

else:
    fecha_inicio = rango_fechas
    fecha_fin = rango_fechas


# ------------------------------------------------------------
# Filtro por categoría
# ------------------------------------------------------------

categorias = sorted(
    df["Categoria"].dropna().unique().tolist()
)

categoria_seleccionada = st.sidebar.selectbox(
    "📦 Categoría",
    options=["Todas"] + categorias,
    index=0
)


# ------------------------------------------------------------
# Filtro por sucursal
# ------------------------------------------------------------

sucursales = sorted(
    df["Sucursal"].dropna().unique().tolist()
)

sucursal_seleccionada = st.sidebar.selectbox(
    "🏬 Sucursal",
    options=["Todas"] + sucursales,
    index=0
)


# ------------------------------------------------------------
# Filtro por canal de venta
# ------------------------------------------------------------

canales = sorted(
    df["Canal_Venta"].dropna().unique().tolist()
)

canal_seleccionado = st.sidebar.selectbox(
    "🌐 Canal de venta",
    options=["Todos"] + canales,
    index=0
)


# ------------------------------------------------------------
# Filtro por método de pago
# ------------------------------------------------------------

metodos_pago = sorted(
    df["Metodo_Pago"].dropna().unique().tolist()
)

pago_seleccionado = st.sidebar.selectbox(
    "💳 Método de pago",
    options=["Todos"] + metodos_pago,
    index=0
)


# ------------------------------------------------------------
# Filtro por productos
# ------------------------------------------------------------

productos = sorted(
    df["Producto"].dropna().unique().tolist()
)

productos_seleccionados = st.sidebar.multiselect(
    "🛒 Productos",
    options=productos,
    default=[],
    help="Si no seleccionas productos, se mostrarán todos."
)


# ------------------------------------------------------------
# Filtros mediante checkbox
# ------------------------------------------------------------

st.sidebar.divider()

st.sidebar.subheader("Opciones adicionales")

solo_promociones = st.sidebar.checkbox(
    "🏷️ Mostrar solo ventas en promoción",
    value=False
)

solo_afiliados = st.sidebar.checkbox(
    "⭐ Mostrar solo clientes afiliados",
    value=False
)


# ============================================================
# 6. APLICAR LOS FILTROS
# ============================================================

df_filtrado = df.copy()

# Filtrar fechas.
df_filtrado = df_filtrado[
    (df_filtrado["Fecha"].dt.date >= fecha_inicio)
    &
    (df_filtrado["Fecha"].dt.date <= fecha_fin)
]

# Filtrar categoría.
if categoria_seleccionada != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Categoria"] == categoria_seleccionada
    ]

# Filtrar sucursal.
if sucursal_seleccionada != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Sucursal"] == sucursal_seleccionada
    ]

# Filtrar canal.
if canal_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Canal_Venta"] == canal_seleccionado
    ]

# Filtrar método de pago.
if pago_seleccionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Metodo_Pago"] == pago_seleccionado
    ]

# Filtrar productos.
if productos_seleccionados:
    df_filtrado = df_filtrado[
        df_filtrado["Producto"].isin(productos_seleccionados)
    ]

# Filtrar promociones.
if solo_promociones:
    df_filtrado = df_filtrado[
        df_filtrado["En_Promocion"] == True
    ]

# Filtrar clientes afiliados.
if solo_afiliados:
    df_filtrado = df_filtrado[
        df_filtrado["Cliente_Afiliado"] == True
    ]


# ============================================================
# 7. INDICADORES PRINCIPALES (KPI)
# ============================================================

st.subheader("📈 Resumen ejecutivo")

total_ventas = len(df_filtrado)

ingresos_totales = df_filtrado["Ingresos"].sum()

ganancia_total = df_filtrado["Ganancia"].sum()

unidades_vendidas = df_filtrado["Cantidad"].sum()

ticket_promedio = (
    ingresos_totales / total_ventas
    if total_ventas > 0
    else 0
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    label="🧾 Número de ventas",
    value=f"{total_ventas:,}"
)

col2.metric(
    label="💰 Ingresos totales",
    value=f"${ingresos_totales:,.2f}"
)

col3.metric(
    label="📊 Ganancia total",
    value=f"${ganancia_total:,.2f}"
)

col4.metric(
    label="📦 Unidades vendidas",
    value=f"{unidades_vendidas:,.0f}"
)

col5.metric(
    label="🛒 Ingreso promedio por venta",
    value=f"${ticket_promedio:,.2f}"
)

st.divider()


# ============================================================
# 8. VISTA PREVIA INTERACTIVA DEL DATAFRAME
# ============================================================

st.subheader("🔎 Explorador de datos")

mostrar_datos = st.checkbox(
    "Mostrar vista previa interactiva de las ventas filtradas",
    value=False
)

if mostrar_datos:

    st.markdown(
        f"Se muestran hasta 10 registros de "
        f"{len(df_filtrado):,} ventas filtradas."
    )

    if not df_filtrado.empty:

        st.dataframe(
            df_filtrado.head(10),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn(
                    "Fecha de venta",
                    format="DD/MM/YYYY"
                ),
                "Precio_Unitario": st.column_config.NumberColumn(
                    "Precio unitario",
                    format="$ %.2f"
                ),
                "Ingresos": st.column_config.NumberColumn(
                    "Ingresos",
                    format="$ %.2f"
                ),
                "Costo_Total": st.column_config.NumberColumn(
                    "Costo total",
                    format="$ %.2f"
                ),
                "Ganancia": st.column_config.NumberColumn(
                    "Ganancia",
                    format="$ %.2f"
                ),
                "Descuento_Pct": st.column_config.NumberColumn(
                    "Descuento",
                    format="%.0%%"
                )
            }
        )

    else:
        st.info("No hay registros que coincidan con los filtros.")

st.divider()


# ============================================================
# 9. COMPROBAR SI HAY DATOS PARA GRAFICAR
# ============================================================

if df_filtrado.empty:

    st.warning(
        "⚠️ No hay ventas que coincidan con los filtros "
        "seleccionados. Modifica los filtros para visualizar "
        "los gráficos."
    )

    st.stop()


# ============================================================
# 10. CONFIGURACIÓN VISUAL DE PLOTLY
# ============================================================

COLORES = [
    "#2563EB",
    "#7C3AED",
    "#06B6D4",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#EC4899",
    "#64748B"
]

TEMA = "plotly_white"


# ============================================================
# 11. GRÁFICO 1: INGRESOS POR CATEGORÍA
# ============================================================

st.subheader("📊 1. Ingresos por categoría")

st.markdown(
    """
    <div class="section-description">
        Compara el rendimiento económico de las diferentes
        categorías de productos. Pasa el cursor sobre las barras
        para consultar los valores.
    </div>
    """,
    unsafe_allow_html=True
)

ventas_categoria = (
    df_filtrado
    .groupby("Categoria", as_index=False)
    .agg(
        Ingresos=("Ingresos", "sum"),
        Ganancia=("Ganancia", "sum"),
        Numero_Ventas=("ID_Venta", "count")
    )
    .sort_values("Ingresos", ascending=True)
)

fig_barras = px.bar(
    ventas_categoria,
    x="Ingresos",
    y="Categoria",
    orientation="h",
    color="Categoria",
    color_discrete_sequence=COLORES,
    text="Ingresos",
    hover_data={
        "Ingresos": ":,.2f",
        "Ganancia": ":,.2f",
        "Numero_Ventas": True,
        "Categoria": True
    },
    labels={
        "Ingresos": "Ingresos ($)",
        "Categoria": "Categoría",
        "Ganancia": "Ganancia ($)",
        "Numero_Ventas": "Número de ventas"
    },
    template=TEMA
)

fig_barras.update_traces(
    texttemplate="$%{x:,.0f}",
    textposition="outside",
    cliponaxis=False
)

fig_barras.update_layout(
    height=420,
    showlegend=False,
    margin=dict(l=20, r=70, t=30, b=30),
    xaxis_title="Ingresos totales ($)",
    yaxis_title="",
    hoverlabel=dict(
        bgcolor="white",
        font_size=13
    )
)

st.plotly_chart(
    fig_barras,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": True,
        "displaylogo": False
    }
)


# ============================================================
# 12. GRÁFICO 2: DISTRIBUCIÓN POR MÉTODO DE PAGO
# ============================================================

st.subheader("🍩 2. Distribución de ventas por método de pago")

st.markdown(
    """
    <div class="section-description">
        Descubre qué métodos de pago concentran más operaciones.
        Puedes pasar el cursor sobre cada segmento o hacer clic
        en la leyenda para explorar las categorías.
    </div>
    """,
    unsafe_allow_html=True
)

ventas_pago = (
    df_filtrado
    .groupby("Metodo_Pago", as_index=False)
    .agg(
        Numero_Ventas=("ID_Venta", "count"),
        Ingresos=("Ingresos", "sum")
    )
)

fig_pie = px.pie(
    ventas_pago,
    names="Metodo_Pago",
    values="Numero_Ventas",
    hole=0.55,
    color_discrete_sequence=COLORES,
    hover_data=["Ingresos"],
    labels={
        "Metodo_Pago": "Método de pago",
        "Numero_Ventas": "Número de ventas",
        "Ingresos": "Ingresos ($)"
    },
    template=TEMA
)

fig_pie.update_traces(
    textposition="inside",
    textinfo="percent+label",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Ventas: %{value}<br>"
        "Porcentaje: %{percent}<br>"
        "<extra></extra>"
    ),
    marker=dict(
        line=dict(
            color="white",
            width=2
        )
    )
)

fig_pie.update_layout(
    height=450,
    showlegend=True,
    legend_title_text="Método de pago",
    margin=dict(l=20, r=20, t=30, b=30),
    hoverlabel=dict(
        bgcolor="white",
        font_size=13
    )
)

st.plotly_chart(
    fig_pie,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "displaylogo": False
    }
)


# ============================================================
# 13. GRÁFICO 3: HISTOGRAMA DE INGRESOS POR VENTA
# ============================================================

st.subheader("📉 3. Distribución de ingresos por venta")

st.markdown(
    """
    <div class="section-description">
        Examina cómo se distribuyen los importes de las ventas.
        El histograma permite identificar los rangos de ingresos
        más frecuentes y detectar operaciones de importe elevado.
    </div>
    """,
    unsafe_allow_html=True
)

numero_intervalos = st.slider(
    "Número de intervalos del histograma",
    min_value=5,
    max_value=30,
    value=12,
    step=1
)

fig_histograma = px.histogram(
    df_filtrado,
    x="Ingresos",
    nbins=numero_intervalos,
    color_discrete_sequence=["#2563EB"],
    marginal="box",
    hover_data=[
        "Categoria",
        "Sucursal",
        "Metodo_Pago"
    ],
    labels={
        "Ingresos": "Ingresos por venta ($)",
        "count": "Número de ventas"
    },
    template=TEMA
)

fig_histograma.update_traces(
    marker=dict(
        line=dict(
            color="white",
            width=1
        )
    ),
    hovertemplate=(
        "Rango de ingresos: %{x}<br>"
        "Número de ventas: %{y}"
        "<extra></extra>"
    )
)

fig_histograma.update_layout(
    height=480,
    bargap=0.08,
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=40),
    xaxis_title="Ingresos por venta ($)",
    yaxis_title="Frecuencia",
    hoverlabel=dict(
        bgcolor="white",
        font_size=13
    )
)

st.plotly_chart(
    fig_histograma,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": True,
        "displaylogo": False
    }
)


# ============================================================
# 14. PIE DE PÁGINA
# ============================================================

st.divider()

st.caption(
    "🛍️ Dashboard de ventas | "
    "Desarrollado con Python, Streamlit, Pandas y Plotly Express."
)

st.caption(
    f"📁 Registros originales: {len(df):,} | "
    f"Registros después de aplicar los filtros: "
    f"{len(df_filtrado):,}"
)