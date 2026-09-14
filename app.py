import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Control de Sitios RF 4",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Tablero de Control de Sitios - Equipo RF 4")
st.write("Vista general de **todos los sitios de Equipo RF = 4** sin Fecha de InSrv, clasificados según su estado de integración y días transcurridos.")

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

# Cargador de archivo
uploaded_file = st.file_uploader("Cargar archivo de Plan BSS (.xls / .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Leer archivo Excel o HTML
        try:
            dfs = pd.read_html(uploaded_file)
            df = dfs[0]
        except Exception:
            df = pd.read_excel(uploaded_file)

        # Validar columnas requeridas
        required_cols = {'Equipo RF', 'Sitio', 'Fecha Integracion', 'Fecha InSrv'}
        if not required_cols.issubset(df.columns):
            st.error(f"El archivo debe contener las siguientes columnas: {required_cols}")
        else:
            # 1. Filtrar Equipo RF == 4
            df_rf4 = df[df['Equipo RF'] == 4].copy()

            # 2. Filtrar sin Fecha InSrv (pendientes de pasar a servicio)
            df_rf4 = df_rf4[
                df_rf4['Fecha InSrv'].isna() | 
                (df_rf4['Fecha InSrv'].astype(str).str.strip() == '') | 
                (df_rf4['Fecha InSrv'].astype(str).str.upper() == 'NAN')
            ].copy()

            # Convertir Fecha Integracion
            df_rf4['Fecha_Integracion_DT'] = pd.to_datetime(
                df_rf4['Fecha Integracion'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )

            # Fecha actual para el cálculo
            fecha_actual = pd.Timestamp.now().floor('d')

            # Calcular días transcurridos
            df_rf4['Dias_Desde_Integracion'] = (fecha_actual - df_rf4['Fecha_Integracion_DT']).dt.days

            # Clasificación de condición
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

            df_rf4['Condición / Estado'] = df_rf4.apply(clasificar_estado, axis=1)

            # Ordenar la tabla: Primero Críticos, luego Alertas, luego En Norma, luego Pendientes
            prioridad_map = {
                "🚨 Crítico (>= 16 días)": 1,
                "⚠️ Alerta (8 - 15 días)": 2,
                "✅ En Norma (< 8 días)": 3,
                "⏳ Pendiente Integración": 4,
                "Fecha Futura / Error": 5
            }
            df_rf4['Prioridad'] = df_rf4['Condición / Estado'].map(prioridad_map)
            df_rf4 = df_rf4.sort_values(by=['Prioridad', 'Dias_Desde_Integracion'], ascending=[True, False])

            # Métricas en tarjetas
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Sitios RF4", len(df_rf4))
            col2.metric("🚨 Críticos (>=16d)", (df_rf4['Condición / Estado'] == "🚨 Crítico (>= 16 días)").sum())
            col3.metric("⚠️ Alerta (8-15d)", (df_rf4['Condición / Estado'] == "⚠️ Alerta (8 - 15 días)").sum())
            col4.metric("✅ En Norma (<8d)", (df_rf4['Condición / Estado'] == "✅ En Norma (< 8 días)").sum())
            col5.metric("⏳ Sin Integrar", (df_rf4['Condición / Estado'] == "⏳ Pendiente Integración").sum())

            st.markdown("---")

            # Filtros en la barra lateral
            st.sidebar.header("Filtros de Búsqueda")

            # Filtro por estado
            estados_disponibles = ['Todos'] + list(df_rf4['Condición / Estado'].unique())
            estado_sel = st.sidebar.selectbox("Filtrar por Condición / Estado", estados_disponibles)
            
            if estado_sel != 'Todos':
                df_filtrado = df_rf4[df_rf4['Condición / Estado'] == estado_sel]
            else:
                df_filtrado = df_rf4.copy()

            # Filtro por MasterPlan
            if 'MasterPlan' in df_filtrado.columns:
                planes = ['Todos'] + list(df_filtrado['MasterPlan'].dropna().unique())
                plan_sel = st.sidebar.selectbox("Filtrar por MasterPlan", planes)
                if plan_sel != 'Todos':
                    df_filtrado = df_filtrado[df_filtrado['MasterPlan'] == plan_sel]

            # Búsqueda por nombre de sitio
            busqueda = st.sidebar.text_input("Buscar por nombre de Sitio")
            if busqueda:
                df_filtrado = df_filtrado[df_filtrado['Sitio'].astype(str).str.contains(busqueda, case=False, na=False)]

            # Formatear columna de días para visualización
            df_display = df_filtrado.copy()
            df_display['Días Sin InSrv'] = df_display['Dias_Desde_Integracion'].apply(
                lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha Integración"
            )

            # Reorganizar columnas principales
            cols_prioritarias = [
                'Sitio', 'Condición / Estado', 'MasterPlan', 'Equipo RF', 
                'Fecha Integracion', 'Días Sin InSrv', 'Fecha InSrv'
            ]
            cols_existentes = [c for c in cols_prioritarias if c in df_display.columns]
            otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Fecha_Integracion_DT', 'Dias_Desde_Integracion', 'Prioridad']]
            
            df_final = df_display[cols_existentes + otras_cols]

            # Función para colorear SOLAMENTE la celda de la columna 'Condición / Estado'
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

            st.subheader(f"Lista Completa de Sitios RF 4 ({len(df_final)} sitios)")
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Botón de descarga en CSV
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Tabla Completa (CSV)",
                data=csv,
                file_name=f"todos_sitios_rf4_estados_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube tu archivo `.xls` para generar el tablero.")
