import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Control de Sitios Sin Fecha InSrv - Equipo RF 4",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Monitoreo de Sitios - Equipo RF 4 (Sin Fecha InSrv)")
st.write("Sube el archivo Excel/HTML (`PlanBSS*.xls`) para mostrar **únicamente los sitios de Equipo RF = 4 que no cuentan con Fecha InSrv**, ordenados de **mayor a menor** según los días transcurridos desde su integración.")

# Cargador de archivo
uploaded_file = st.file_uploader("Cargar archivo de Plan BSS (.xls / .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Leer archivo Excel o HTML guardado como .xls
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
            # 1. Filtrar solo Equipo RF == 4
            df_rf4 = df[df['Equipo RF'] == 4].copy()

            # 2. Filtrar únicamente sitios SIN Fecha InSrv
            df_rf4 = df_rf4[
                df_rf4['Fecha InSrv'].isna() | 
                (df_rf4['Fecha InSrv'].astype(str).str.strip() == '') | 
                (df_rf4['Fecha InSrv'].astype(str).str.upper() == 'NAN')
            ]

            # Convertir Fecha Integracion a formato datetime
            df_rf4['Fecha_Integracion_DT'] = pd.to_datetime(
                df_rf4['Fecha Integracion'], 
                format='%d/%m/%Y', 
                errors='coerce'
            )

            # Fecha actual
            fecha_actual = pd.Timestamp.now().floor('d')

            # Calcular días transcurridos desde la integración
            df_rf4['Dias_Desde_Integracion'] = (fecha_actual - df_rf4['Fecha_Integracion_DT']).dt.days

            # 3. ORDENAR DESCENDENTE POR DÍAS (de mayor a menor)
            # Los sitios no integrados (NaN) se colocan al final
            df_rf4 = df_rf4.sort_values(by='Dias_Desde_Integracion', ascending=False, na_position='last')

            # Tarjetas de métricas
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sitios RF 4 Sin InSrv", len(df_rf4))
            col2.metric("Integrados (Pendientes InSrv)", df_rf4['Fecha_Integracion_DT'].notna().sum())
            col3.metric("Pendientes Integración", df_rf4['Fecha_Integracion_DT'].isna().sum())
            
            promedio_dias = df_rf4['Dias_Desde_Integracion'].mean()
            col4.metric("Promedio Días Transcurridos", f"{promedio_dias:.1f} días" if pd.notnull(promedio_dias) else "N/A")

            st.markdown("---")

            # Barra lateral con filtros
            st.sidebar.header("Filtros de Búsqueda")
            
            if 'MasterPlan' in df_rf4.columns:
                planes = ['Todos'] + list(df_rf4['MasterPlan'].dropna().unique())
                plan_sel = st.sidebar.selectbox("Filtrar por MasterPlan", planes)
                if plan_sel != 'Todos':
                    df_rf4 = df_rf4[df_rf4['MasterPlan'] == plan_sel]

            filtro_estado = st.sidebar.radio(
                "Estado de Integración",
                ["Todos", "Solo Integrados", "Solo Pendientes"]
            )
            
            if filtro_estado == "Solo Integrados":
                df_rf4 = df_rf4[df_rf4['Fecha_Integracion_DT'].notna()]
            elif filtro_estado == "Solo Pendientes":
                df_rf4 = df_rf4[df_rf4['Fecha_Integracion_DT'].isna()]

            busqueda = st.sidebar.text_input("Buscar por nombre de Sitio")
            if busqueda:
                df_rf4 = df_rf4[df_rf4['Sitio'].astype(str).str.contains(busqueda, case=False, na=False)]

            # Formatear la columna para mostrar en la tabla
            df_display = df_rf4.copy()
            df_display['Días Desde Integración'] = df_display['Dias_Desde_Integracion'].apply(
                lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Integrar"
            )

            # Organizar las columnas
            cols_prioritarias = ['Sitio', 'MasterPlan', 'Equipo RF', 'Fecha Integracion', 'Días Desde Integración', 'Fecha InSrv']
            cols_existentes = [c for c in cols_prioritarias if c in df_display.columns]
            otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Fecha_Integracion_DT', 'Dias_Desde_Integracion']]
            
            df_final = df_display[cols_existentes + otras_cols]

            st.subheader("Tabla de Sitios (Ordenados por Mayor Tiempo Integrado)")
            st.dataframe(df_final, use_container_width=True, hide_index=True)

            # Descargar reporte
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte en CSV",
                data=csv,
                file_name=f"sitios_rf4_sin_insrv_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube tu archivo `.xls` para continuar.")
