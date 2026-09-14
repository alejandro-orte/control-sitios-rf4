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
st.write("Sincronización en tiempo real desde **Google Sheets** (Excluyendo sitios en **PRODUCCIÓN**).")

# 🔗 URL pública CSV de tu Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?output=csv"

# Estilos CSS personalizados para la leyenda de estados condicionales
st.markdown("""
<style>
    .badge {
        padding: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
        color: white;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-red { background-color: #dc3545; }
    .badge-yellow { background-color: #f39c12; }
    .badge-green { background-color: #198754; }
    .badge-gray { background-color: #6c757d; }
</style>
<div style="margin-bottom: 20px;">
    <b>Leyenda de Condición (Sitios sin OnAir):</b> 
    <span class="badge badge-red">🚨 Crítico (>= 16 días)</span> 
    <span class="badge badge-yellow">⚠️ Alerta (8 - 15 días)</span> 
    <span class="badge badge-green">✅ En Norma (< 8 días)</span> 
    <span class="badge badge-gray">⏳ Pendiente Integración</span>
</div>
""", unsafe_allow_html=True)

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
    
    # Validar columnas principales requeridas del archivo
    required_cols = {'Site Name', 'Proyecto', 'Territorio Comercial', 'SS IMP', 'Integracion', 'Estado Macro', 'Estado Insrv'}
    if not required_cols.issubset(df.columns):
        st.error(f"Faltan columnas requeridas en la hoja de Google Sheets. Se esperaban al menos: {required_cols}")
    else:
        df_proc = df.copy()

        # 🚫 EXCLUIR SITIOS EN PRODUCCIÓN
        df_proc = df_proc[df_proc['Estado Macro'].astype(str).str.strip().str.upper() != 'PRODUCCIÓN']

        # Convertir Fechas a formato datetime
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

        # Fecha actual sin hora
        fecha_actual = pd.Timestamp.now().floor('d')

        # Días transcurridos desde la fecha de Integración
        df_proc['Dias_Desde_Integracion'] = (fecha_actual - df_proc['Fecha_Integracion_DT']).dt.days

        # --- LÓGICA CONDICIONAL ---
        def clasificar_condicion(row):
            if pd.notna(row['Fecha_OnAir_DT']):
                return "🎉 Completado / OnAir"
            elif pd.isna(row['Fecha_Integracion_DT']):
                return "⏳ Pendiente Integración"
            elif row['Dias_Desde_Integracion'] >= 16:
                return "🚨 Crítico (>= 16 días)"
            elif row['Dias_Desde_Integracion'] >= 8:
                return "⚠️ Alerta (8 - 15 días)"
            elif row['Dias_Desde_Integracion'] >= 0:
                return "✅ En Norma (< 8 días)"
            else:
                return "Fecha Futura / Error"

        df_proc['Condición / Estado'] = df_proc.apply(clasificar_condicion, axis=1)

        # Mapeo de prioridad para ordenamiento automático
        prioridad_map = {
            "🚨 Crítico (>= 16 días)": 1,
            "⚠️ Alerta (8 - 15 días)": 2,
            "✅ En Norma (< 8 días)": 3,
            "⏳ Pendiente Integración": 4,
            "🎉 Completado / OnAir": 5,
            "Fecha Futura / Error": 6
        }
        df_proc['Prioridad'] = df_proc['Condición / Estado'].map(prioridad_map)
        df_proc = df_proc.sort_values(by=['Prioridad', 'Dias_Desde_Integracion'], ascending=[True, False])

        # --- FILTROS DE LA BARRA LATERAL ---
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Búsqueda")

        # 1. Filtro por Condición / Estado Alerta
        condiciones = ['Todos'] + sorted(list(df_proc['Condición / Estado'].dropna().astype(str).unique()))
        condicion_sel = st.sidebar.selectbox("Filtrar por Condición / Alerta", condiciones)

        df_filtrado = df_proc.copy()
        if condicion_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Condición / Estado'] == condicion_sel]

        # 2. Filtro por Proyecto
        proyectos = ['Todos'] + sorted(list(df_filtrado['Proyecto'].dropna().astype(str).unique()))
        proyecto_sel = st.sidebar.selectbox("Filtrar por Proyecto", proyectos)
        if proyecto_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Proyecto'] == proyecto_sel]

        # 3. Filtro por Territorio Comercial
        territorios = ['Todos'] + sorted(list(df_filtrado['Territorio Comercial'].dropna().astype(str).unique()))
        territorio_sel = st.sidebar.selectbox("Filtrar por Territorio Comercial", territorios)
        if territorio_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Territorio Comercial'] == territorio_sel]

        # 4. Filtro por Contratista (SS IMP)
        contratistas = ['Todos'] + sorted(list(df_filtrado['SS IMP'].dropna().astype(str).unique()))
        contratista_sel = st.sidebar.selectbox("Filtrar por Contratista (SS IMP)", contratistas)
        if contratista_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['SS IMP'] == contratista_sel]

        # 5. Filtro por Estado Macro
        estados_macro = ['Todos'] + sorted(list(df_filtrado['Estado Macro'].dropna().astype(str).unique()))
        estado_macro_sel = st.sidebar.selectbox("Filtrar por Estado Macro", estados_macro)
        if estado_macro_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Estado Macro'] == estado_macro_sel]

        # 6. Búsqueda por Nombre de Sitio
        busqueda = st.sidebar.text_input("Buscar por Sitio (Site Name)")
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['Site Name'].astype(str).str.contains(busqueda, case=False, na=False)]

        # --- TARJETAS MÉTRICAS ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Sitios Pendientes", len(df_filtrado))
        col2.metric("🚨 Críticos (>=16d)", (df_filtrado['Condición / Estado'] == "🚨 Crítico (>= 16 días)").sum())
        col3.metric("⚠️ Alerta (8-15d)", (df_filtrado['Condición / Estado'] == "⚠️ Alerta (8 - 15 días)").sum())
        col4.metric("✅ En Norma (<8d)", (df_filtrado['Condición / Estado'] == "✅ En Norma (< 8 días)").sum())
        col5.metric("🎉 OnAir / Completado", (df_filtrado['Condición / Estado'] == "🎉 Completado / OnAir").sum())

        st.markdown("---")

        # --- PREPARACIÓN DE LA TABLA PRINCIPAL ---
        df_display = df_filtrado.copy()
        
        # Columna explícita para Días Transcurridos
        df_display['Días Transcurridos'] = df_display['Dias_Desde_Integracion'].apply(
            lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha Integración"
        )

        # Orden prioritario de columnas
        cols_ordenadas = [
            'Condición / Estado', 'Días Transcurridos', 'Site Name', 'Territorio Comercial', 
            'Proyecto', 'SS IMP', 'Integracion', 
            'OnAir', 'Estado Macro', 
            'Estado Insrv', 'Sub Estado Insrv', 'Comentario'
        ]
        
        cols_existentes = [c for c in cols_ordenadas if c in df_display.columns]
        otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Region', 'Fecha_Integracion_DT', 'Fecha_OnAir_DT', 'Dias_Desde_Integracion', 'Prioridad']]
        
        df_final = df_display[cols_existentes + otras_cols]

        # Estilo condicional para las celdas de 'Condición / Estado'
        def colorear_condicion(val):
            if val == "🚨 Crítico (>= 16 días)":
                return 'background-color: #f8d7da; color: #842029; font-weight: bold;'
            elif val == "⚠️ Alerta (8 - 15 días)":
                return 'background-color: #fff3cd; color: #664d03; font-weight: bold;'
            elif val == "✅ En Norma (< 8 días)":
                return 'background-color: #d1e7dd; color: #0f5132; font-weight: bold;'
            elif val == "⏳ Pendiente Integración":
                return 'background-color: #e2e3e5; color: #41464b; font-weight: bold;'
            elif val == "🎉 Completado / OnAir":
                return 'background-color: #cff4fc; color: #055160;'
            else:
                return ''

        styled_df = df_final.style.map(colorear_condicion, subset=['Condición / Estado'])

        st.subheader(f"Lista de Sitios Pendientes ({len(df_final)} mostrados)")
        
        # Configuración de anchos para garantizar el scroll horizontal
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Condición / Estado": st.column_config.TextColumn("Condición / Estado", width="medium"),
                "Días Transcurridos": st.column_config.TextColumn("Días Transcurridos", width="small"),
                "Site Name": st.column_config.TextColumn("Site Name", width="medium"),
                "Territorio Comercial": st.column_config.TextColumn("Territorio Comercial", width="medium"),
                "Comentario": st.column_config.TextColumn("Comentario", width="large"),
            }
        )

        # Botón de descarga en CSV
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv,
            file_name=f"control_semanal_bss_pendientes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
