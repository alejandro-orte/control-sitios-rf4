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

# 🔗 URL pública CSV de la hoja principal
SHEET_URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?output=csv"

# 🔗 REEMPLAZA ESTA URL por la URL pública CSV generada al publicar la pestaña 'umbrella'
SHEET_URL_UMBRELLA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?gid=644478638&single=true&output=csv"

# Cargar datos descartando caché automáticamente cada 60 segundos
@st.cache_data(ttl=60)
def cargar_datos(url):
    try:
        # Intento estándar de lectura
        return pd.read_csv(url)
    except Exception:
        # Si falla por inconsistencia en número de columnas (comas/saltos de línea)
        return pd.read_csv(url, on_bad_lines='skip', engine='python')

# Botón manual de sincronización en la barra lateral
st.sidebar.header("🔄 Sincronización")
if st.sidebar.button("Actualizar datos desde Google Sheets"):
    st.cache_data.clear()

try:
    df = cargar_datos(SHEET_URL_MAIN)

    # --- CREACIÓN DE PESTAÑAS (TABS) EN LA NAVEGACIÓN ---
    tab_principal, tab_rechazados = st.tabs(["📡 Tablero Principal (BSS)", "🚫 Sitios Rechazados (Umbrella)"])

    # ==========================================
    # PESTAÑA 1: TABLERO PRINCIPAL
    # ==========================================
    with tab_principal:
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

        df_proc = df.copy()

        # 🚫 EXCLUIR SITIOS EN PRODUCCIÓN
        if 'Estado Macro' in df_proc.columns:
            df_proc = df_proc[df_proc['Estado Macro'].astype(str).str.strip().str.upper() != 'PRODUCCIÓN']

        # Convertir Fechas a formato datetime
        if 'Integracion' in df_proc.columns:
            df_proc['Fecha_Integracion_DT'] = pd.to_datetime(df_proc['Integracion'], dayfirst=True, errors='coerce')
        else:
            df_proc['Fecha_Integracion_DT'] = pd.NaT
            
        if 'OnAir' in df_proc.columns:
            df_proc['Fecha_OnAir_DT'] = pd.to_datetime(df_proc['OnAir'], dayfirst=True, errors='coerce')
        else:
            df_proc['Fecha_OnAir_DT'] = pd.NaT

        fecha_actual = pd.Timestamp.now().floor('d')
        df_proc['Dias_Desde_Integracion'] = (fecha_actual - df_proc['Fecha_Integracion_DT']).dt.days

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
        st.sidebar.header("🔍 Filtros Tablero Principal")

        condiciones = ['Todos'] + sorted(list(df_proc['Condición / Estado'].dropna().astype(str).unique()))
        condicion_sel = st.sidebar.selectbox("Filtrar por Condición / Alerta", condiciones)

        df_filtrado = df_proc.copy()
        if condicion_sel != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['Condición / Estado'] == condicion_sel]

        if 'Proyecto' in df_filtrado.columns:
            proyectos = ['Todos'] + sorted(list(df_filtrado['Proyecto'].dropna().astype(str).unique()))
            proyecto_sel = st.sidebar.selectbox("Filtrar por Proyecto", proyectos)
            if proyecto_sel != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['Proyecto'] == proyecto_sel]

        if 'Territorio Comercial' in df_filtrado.columns:
            territorios = ['Todos'] + sorted(list(df_filtrado['Territorio Comercial'].dropna().astype(str).unique()))
            territorio_sel = st.sidebar.selectbox("Filtrar por Territorio Comercial", territorios)
            if territorio_sel != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['Territorio Comercial'] == territorio_sel]

        busqueda = st.sidebar.text_input("Buscar por Sitio (Site Name)")
        if busqueda and 'Site Name' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['Site Name'].astype(str).str.contains(busqueda, case=False, na=False)]

        # --- TARJETAS MÉTRICAS ---
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Sitios Pendientes", len(df_filtrado))
        col2.metric("🚨 Críticos (>=16d)", (df_filtrado['Condición / Estado'] == "🚨 Crítico (>= 16 días)").sum())
        col3.metric("⚠️ Alerta (8-15d)", (df_filtrado['Condición / Estado'] == "⚠️ Alerta (8 - 15 días)").sum())
        col4.metric("✅ En Norma (<8d)", (df_filtrado['Condición / Estado'] == "✅ En Norma (< 8 días)").sum())
        col5.metric("🎉 OnAir / Completado", (df_filtrado['Condición / Estado'] == "🎉 Completado / OnAir").sum())

        st.markdown("---")

        df_display = df_filtrado.copy()
        df_display['Días Transcurridos'] = df_display['Dias_Desde_Integracion'].apply(
            lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha Integración"
        )

        cols_ordenadas = [
            'Condición / Estado', 'Días Transcurridos', 'Site Name', 'Territorio Comercial', 
            'Integracion', 'OnAir', 'Estado Macro', 
            'Estado Insrv', 'Sub Estado Insrv', 'Comentario',
            'Proyecto', 'SS IMP'
        ]
        
        cols_existentes = [c for c in cols_ordenadas if c in df_display.columns]
        otras_cols = [c for c in df_display.columns if c not in cols_existentes and c not in ['Region', 'Fecha_Integracion_DT', 'Fecha_OnAir_DT', 'Dias_Desde_Integracion', 'Prioridad']]
        
        df_final = df_display[cols_existentes + otras_cols]

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
        
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True
        )

        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Principal (CSV)",
            data=csv,
            file_name=f"control_semanal_bss_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
# ==========================================
    # PESTAÑA 2: SITIOS RECHAZADOS (PESTAÑA UMBRELLA)
    # ==========================================
    with tab_rechazados:
        st.header("🚫 Registro de Sitios Rechazados desde la pestaña Umbrella (Año 2026)")
        
        if SHEET_URL_UMBRELLA == "PEGA_AQUI_LA_URL_CSV_DE_LA_PESTAÑA_UMBRELLA":
            st.warning("⚠️ Debes publicar la pestaña 'umbrella' en Google Sheets como CSV y pegar la URL en la variable `SHEET_URL_UMBRELLA`.")
        else:
            try:
                df_umbrella = cargar_datos(SHEET_URL_UMBRELLA)

                # --- 1. FILTRADO DE FILAS RECHAZADAS ---
                estados_rechazados = [
                    "Rechazado 1 NOC", 
                    "Rechazado 1 RF", 
                    "Rechazado 2 NOC", 
                    "Rechazado 2 RF"
                ]

                # Buscar la columna que contiene el estado
                col_estado = None
                for col in df_umbrella.columns:
                    col_clean = str(col).strip().lower().replace('_', ' ')
                    if col_clean in ['estado', 'sub estado', 'subestado', 'condicion', 'status', 'estado insrv']:
                        col_estado = col
                        break

                if col_estado:
                    mask_rechazados = df_umbrella[col_estado].astype(str).str.strip().isin(estados_rechazados)
                    df_rechazados = df_umbrella[mask_rechazados].copy()
                else:
                    df_rechazados = df_umbrella.copy()

                # --- 2. ELIMINACIÓN DE COLUMNAS NO DESEADAS E IMÁGENES ---
                terminos_a_eliminar = [
                    'secuencial', 'flujo', 'id sitio', 'idsitio', 'solicitante', 
                    'comercial', 'performance', 'oym', 'site owner', 'owner', 
                    'energia', 'actividad', 'odh', 'proyecto', 'smp',
                    'imagen', 'foto', 'photo', 'img', 'evidencia', 'pic', 'adjunto', 'url', 'link'
                ]

                cols_para_drop = []
                import re
                for col in df_rechazados.columns:
                    col_limpia = re.sub(r'[\s_]+', ' ', str(col)).strip().lower()
                    if any(term in col_limpia for term in terminos_a_eliminar):
                        cols_para_drop.append(col)

                df_rechazados_clean = df_rechazados.drop(columns=cols_para_drop, errors='ignore').copy()

                # --- 3. CORRECCIÓN Y FILTRADO POR AÑO 2026 EN FECHA_ESTADO ---
                col_fecha_estado = None
                for col in df_rechazados_clean.columns:
                    col_limpia = str(col).strip().lower().replace('_', ' ')
                    if 'fecha estado' in col_limpia:
                        col_fecha_estado = col
                        break

                if col_fecha_estado:
                    fechas_dt = pd.to_datetime(df_rechazados_clean[col_fecha_estado], errors='coerce', dayfirst=True)
                    df_rechazados_clean = df_rechazados_clean[fechas_dt.dt.year == 2026].copy()

                # --- 4. FORMATO DE TODAS LAS COLUMNAS DE FECHA (# # # # # # # # # #) ---
                for col in df_rechazados_clean.columns:
                    if 'fecha' in str(col).lower():
                        fecha_parsed = pd.to_datetime(df_rechazados_clean[col], errors='coerce', dayfirst=True)
                        df_rechazados_clean[col] = fecha_parsed.dt.strftime('%Y-%m-%d').fillna(df_rechazados_clean[col].astype(str))
                        df_rechazados_clean[col] = df_rechazados_clean[col].replace({'nan': '', 'None': '', '<NaT>': ''})

                # --- 5. BUSCADOR POR NOMBRE DEL SITIO ---
                col_sitio = None
                for col in df_rechazados_clean.columns:
                    col_norm = str(col).strip().lower().replace('_', ' ')
                    if col_norm in ['sitio b', 'sitio_b', 'sitio', 'nombre sitio', 'nombre_sitio']:
                        col_sitio = col
                        break

                search_query = st.text_input(
                    "🔍 **Buscar por Nombre de Sitio:**",
                    placeholder="Escribe el nombre o código del sitio...",
                    key="search_sitio_umbrella"
                )

                if search_query.strip():
                    if col_sitio:
                        df_rechazados_clean = df_rechazados_clean[
                            df_rechazados_clean[col_sitio].astype(str).str.contains(search_query.strip(), case=False, na=False)
                        ]
                    else:
                        mask = df_rechazados_clean.astype(str).apply(
                            lambda row: row.str.contains(search_query.strip(), case=False, na=False)
                        ).any(axis=1)
                        df_rechazados_clean = df_rechazados_clean[mask]

                # --- 6. REORDENAR: COLOCAR 'ESTADO' AL LADO DE 'SITIO' ---
                if col_sitio and col_estado and col_sitio in df_rechazados_clean.columns and col_estado in df_rechazados_clean.columns:
                    cols = list(df_rechazados_clean.columns)
                    # Quitar col_estado de su posición actual
                    cols.remove(col_estado)
                    # Encontrar el índice de la columna del sitio e insertar 'Estado' inmediatamente después
                    idx_sitio = cols.index(col_sitio)
                    cols.insert(idx_sitio + 1, col_estado)
                    # Reorganizar el DataFrame con el nuevo orden de columnas
                    df_rechazados_clean = df_rechazados_clean[cols]

                st.metric(label="Total Registros Filtrados en Umbrella (2026)", value=len(df_rechazados_clean))

                if not df_rechazados_clean.empty:
                    st.dataframe(
                        df_rechazados_clean,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv_umbrella = df_rechazados_clean.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Reporte Umbrella 2026 (CSV)",
                        data=csv_umbrella,
                        file_name=f"sitios_rechazados_umbrella_2026_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No se encontraron registros rechazados del año 2026 que coincidan con la búsqueda.")

            except Exception as e_umb:
                st.error(f"Error al cargar la pestaña umbrella: {e_umb}")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
