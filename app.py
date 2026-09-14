import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Control Semanal de Sitios BSS",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Tablero de Control Semanal de Sitios BSS")
st.write("Sincronización en tiempo real desde **Google Sheets**.")

# 🔗 URL CSV pública de tu Google Sheet (Asegúrate de publicar la pestaña 'CONTROL' como CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?output=csv"

# Cargar datos descartando caché automáticamente cada 60 segundos
@st.cache_data(ttl=60)
def cargar_datos(url):
    return pd.read_csv(url)

# Botón manual de sincronización en la barra lateral
st.sidebar.header("🔄 Sincronización")
if st.sidebar.button("Actualizar datos desde Google Sheets"):
    st.cache_data.clear()

try:
    df = cargar_datos(SHEET_URL)
    
    # Validar columnas principales del nuevo formato
    required_cols = {'Site Name', 'Proyecto', 'Region', 'SS IMP', 'Integracion', 'Estado Macro', 'Estado Insrv'}
    if not required_cols.issubset(df.columns):
        st.error(f"Faltan columnas requeridas en la hoja de Google Sheets. Se esperaban al menos: {required_cols}")
    else:
        df_proc = df.copy()

        # Convertir Fechas (Integración y OnAir) a datetime
        df_proc['Fecha_Integracion_DT'] = pd.to_datetime(
            df_proc['Integracion'], 
            dayfirst=True, 
            errors='coerce'
        )
        
        if 'OnAir' in df_proc.columns:
            df_proc['Fecha_OnAir_DT'] = pd.to_datetime(
                df_proc['OnAir'], 
                dayfirst=True, 
                errors='coerce'
            )
        else:
            df_proc['Fecha_OnAir_DT'] = pd.NaT

        # Fecha actual
        fecha_actual = pd.Timestamp.now().floor('d')

        # Días desde Integración hasta hoy (para sitios no terminados/producción)
        df_proc['Dias_Desde_Integracion'] = (fecha_actual - df_proc['Fecha_Integracion_DT']).dt.days

        # --- FILTROS DE LA BARRA LATERAL ---
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Búsqueda")

        # 1. Filtro por Proyecto
        proyectos = ['Todos'] + sorted(list(df_proc['Proyecto'].dropna().astype(str).unique()))
        proyecto_sel = st.sidebar.selectbox("Filtrar por Proyecto", proyectos)

        df_filtrado = df_proc.copy()
        if proyecto_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Proyecto'] == proyecto_sel]

        # 2. Filtro por Región
        regiones = ['Todos'] + sorted(list(df_filtrado['Region'].dropna().astype(str).unique()))
        region_sel = st.sidebar.selectbox("Filtrar por Región", regiones)
        if region_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Region'] == region_sel]

        # 3. Filtro por Contratista (SS IMP)
        contratistas = ['Todos'] + sorted(list(df_filtrado['SS IMP'].dropna().astype(str).unique()))
        contratista_sel = st.sidebar.selectbox("Filtrar por Contratista (SS IMP)", contratistas)
        if contratista_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['SS IMP'] == contratista_sel]

        # 4. Filtro por Estado Macro
        estados_macro = ['Todos'] + sorted(list(df_filtrado['Estado Macro'].dropna().astype(str).unique()))
        estado_macro_sel = st.sidebar.selectbox("Filtrar por Estado Macro", estados_macro)
        if estado_macro_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Estado Macro'] == estado_macro_sel]

        # 5. Filtro por Estado Insrv
        estados_insrv = ['Todos'] + sorted(list(df_filtrado['Estado Insrv'].dropna().astype(str).unique()))
        estado_insrv_sel = st.sidebar.selectbox("Filtrar por Estado Insrv", estados_insrv)
        if estado_insrv_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Estado Insrv'] == estado_insrv_sel]

        # 6. Búsqueda por Nombre de Sitio
        busqueda = st.sidebar.text_input("Buscar por Sitio (Site Name)")
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['Site Name'].astype(str).str.contains(busqueda, case=False, na=False)]

        # --- TARJETAS MÉTRICAS ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Sitios", len(df_filtrado))
        col2.metric("Producción", (df_filtrado['Estado Macro'] == "PRODUCCIÓN").sum())
        col3.metric("Nokia NPO", (df_filtrado['Estado Macro'] == "NOKIA_NPO").sum())
        col4.metric("Nokia NI", (df_filtrado['Estado Macro'] == "NOKIA_NI").sum())
        col5.metric("Claro GI / Otros", len(df_filtrado) - (
            (df_filtrado['Estado Macro'] == "PRODUCCIÓN").sum() +
            (df_filtrado['Estado Macro'] == "NOKIA_NPO").sum() +
            (df_filtrado['Estado Macro'] == "NOKIA_NI").sum()
        ))

        st.markdown("---")

        # --- PREPARACIÓN DE TABLA FINAL ---
        df_display = df_filtrado.copy()
        
        # Formatear la columna de días desde integración
        df_display['Días Integ. a Hoy'] = df_display['Dias_Desde_Integracion'].apply(
            lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha"
        )

        # Ordenar columnas preferidas al inicio
        cols_ordenadas = [
            'Site Name', 'Proyecto', 'Region', 'SS IMP', 
            'Estado Macro', 'Estado Insrv', 'Sub Estado Insrv', 
            'Integracion', 'OnAir', 'Días Integ. a Hoy', 'Comentario'
        ]
        
        cols_existentes = [c for c in cols_ordenadas if c in df_display.columns]
        otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Fecha_Integracion_DT', 'Fecha_OnAir_DT', 'Dias_Desde_Integracion']]
        
        df_final = df_display[cols_existentes + otras_cols]

        # Función de estilo para resaltar Estado Macro
        def colorear_estado_macro(val):
            if val == "PRODUCCIÓN":
                return 'background-color: #d1e7dd; color: #0f5132; font-weight: bold;'
            elif val == "NOKIA_NPO":
                return 'background-color: #fff3cd; color: #664d03; font-weight: bold;'
            elif val == "NOKIA_NI":
                return 'background-color: #f8d7da; color: #842029; font-weight: bold;'
            elif val == "CLARO_GI":
                return 'background-color: #cff4fc; color: #055160; font-weight: bold;'
            else:
                return 'background-color: #e2e3e5; color: #41464b;'

        styled_df = df_final.style.map(colorear_estado_macro, subset=['Estado Macro'])

        st.subheader(f"Lista de Sitios ({len(df_final)} mostrados)")
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # --- BOTÓN DE DESCARGA ---
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv,
            file_name=f"control_semanal_bss_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
