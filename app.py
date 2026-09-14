import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Control General de Sitios BSS",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Tablero Dinámico de Control de Sitios BSS")
st.write("Sincronización en tiempo real desde **Google Sheets**.")

# 🔗 URL CSV pública de tu Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?output=csv"

# Estilos CSS personalizados para la leyenda
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
    <b>Leyenda de Estados:</b> 
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
    
    # Verificación de columnas principales
    required_cols = {'Equipo RF', 'Sitio', 'Fecha Integracion', 'Fecha InSrv'}
    if not required_cols.issubset(df.columns):
        st.error(f"Faltan columnas requeridas en Google Sheets. Se necesitan: {required_cols}")
    else:
        # Filtrar sitios sin Fecha InSrv (vacíos o sin valor válido)
        df_sin_insrv = df[
            df['Fecha InSrv'].isna() | 
            (df['Fecha InSrv'].astype(str).str.strip() == '') | 
            (df['Fecha InSrv'].astype(str).str.upper() == 'NAN')
        ].copy()

        # Convertir Fecha Integración (soporta formato DD/MM/YYYY)
        df_sin_insrv['Fecha_Integracion_DT'] = pd.to_datetime(
            df_sin_insrv['Fecha Integracion'], 
            dayfirst=True, 
            errors='coerce'
        )

        # Fecha actual sin hora
        fecha_actual = pd.Timestamp.now().floor('d')

        # Cálculo de días transcurridos
        df_sin_insrv['Dias_Desde_Integracion'] = (fecha_actual - df_sin_insrv['Fecha_Integracion_DT']).dt.days

        # Regla de clasificación del estado
        def clasificar_estado(row):
            if pd.isna(row['Fecha_Integracion_DT']):
                return "⏳ Pendiente Integración"
            elif row['Dias_Desde_Integracion'] >= 16:
                return "🚨 Crítico (>= 16 días)"
            elif row['Dias_Desde_Integracion'] >= 8:
                return "⚠️ Alerta (8 - 15 días)"
            elif row['Dias_Desde_Integracion'] >= 0:
                return "✅ En Norma (< 8 días)"
            else:
                return "Fecha Futura / Error"

        df_sin_insrv['Condición / Estado'] = df_sin_insrv.apply(clasificar_estado, axis=1)

        # Orden de prioridad
        prioridad_map = {
            "🚨 Crítico (>= 16 días)": 1,
            "⚠️ Alerta (8 - 15 días)": 2,
            "✅ En Norma (< 8 días)": 3,
            "⏳ Pendiente Integración": 4,
            "Fecha Futura / Error": 5
        }
        df_sin_insrv['Prioridad'] = df_sin_insrv['Condición / Estado'].map(prioridad_map)
        df_sin_insrv = df_sin_insrv.sort_values(by=['Prioridad', 'Dias_Desde_Integracion'], ascending=[True, False])

        # --- FILTROS EN BARRA LATERAL ---
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Búsqueda")

        # 1. Filtro Equipo RF
        equipos_rf_disponibles = ['Todos'] + sorted(list(df_sin_insrv['Equipo RF'].dropna().unique()))
        equipo_rf_sel = st.sidebar.selectbox("Filtrar por Equipo RF", equipos_rf_disponibles)

        df_filtrado = df_sin_insrv.copy()
        if equipo_rf_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Equipo RF'] == equipo_rf_sel]

        # 2. Filtro Estado
        estados_disponibles = ['Todos'] + list(df_filtrado['Condición / Estado'].unique())
        estado_sel = st.sidebar.selectbox("Filtrar por Condición / Estado", estados_disponibles)
        if estado_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Condición / Estado'] == estado_sel]

        # 3. Filtro MasterPlan (si existe la columna)
        if 'MasterPlan' in df_filtrado.columns:
            planes = ['Todos'] + sorted(list(df_filtrado['MasterPlan'].dropna().unique()))
            plan_sel = st.sidebar.selectbox("Filtrar por MasterPlan", planes)
            if plan_sel != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['MasterPlan'] == plan_sel]

        # 4. Buscador por Sitio
        busqueda = st.sidebar.text_input("Buscar por nombre de Sitio")
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['Sitio'].astype(str).str.contains(busqueda, case=False, na=False)]

        # Muestra de métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Sitios", len(df_filtrado))
        col2.metric("🚨 Críticos", (df_filtrado['Condición / Estado'] == "🚨 Crítico (>= 16 días)").sum())
        col3.metric("⚠️ Alerta", (df_filtrado['Condición / Estado'] == "⚠️ Alerta (8 - 15 días)").sum())
        col4.metric("✅ En Norma", (df_filtrado['Condición / Estado'] == "✅ En Norma (< 8 días)").sum())
        col5.metric("⏳ Sin Integrar", (df_filtrado['Condición / Estado'] == "⏳ Pendiente Integración").sum())

        st.markdown("---")

        # Formato de columna de días
        df_display = df_filtrado.copy()
        df_display['Días Sin InSrv'] = df_display['Dias_Desde_Integracion'].apply(
            lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha Integración"
        )

        cols_prioritarias = [
            'Sitio', 'Equipo RF', 'Condición / Estado', 'MasterPlan', 
            'Fecha Integracion', 'Días Sin InSrv', 'Fecha InSrv'
        ]
        cols_existentes = [c for c in cols_prioritarias if c in df_display.columns]
        otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Fecha_Integracion_DT', 'Dias_Desde_Integracion', 'Prioridad']]
        
        df_final = df_display[cols_existentes + otras_cols]

        # Estilo de color para la celda de estado
        def colorear_celda_condicion(val):
            if val == "🚨 Crítico (>= 16 días)":
                return 'background-color: #f8d7da; color: #842029; font-weight: bold;'
            elif val == "⚠️ Alerta (8 - 15 días)":
                return 'background-color: #fff3cd; color: #664d03; font-weight: bold;'
            elif val == "✅ En Norma (< 8 días)":
                return 'background-color: #d1e7dd; color: #0f5132; font-weight: bold;'
            elif val == "⏳ Pendiente Integración":
                return 'background-color: #e2e3e5; color: #41464b; font-weight: bold;'
            else:
                return ''

        styled_df = df_final.style.map(colorear_celda_condicion, subset=['Condición / Estado'])

        st.subheader(f"Lista de Sitios ({len(df_final)} mostrados)")
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Descarga en CSV
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv,
            file_name=f"sitios_bss_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
