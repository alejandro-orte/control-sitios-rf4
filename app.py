import streamlit as st
import pandas as pd
import re
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Control de Sitios RF",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sistema de Control de Sitios RF")

# ==========================================
# CONFIGURACIÓN DE URLS DE GOOGLE SHEETS
# ==========================================
# Reemplaza las URLs por las correspondientes o configúralas en los secrets de Streamlit
SHEET_URL_GENERAL = st.secrets.get("SHEET_URL_GENERAL", "PEGA_AQUI_LA_URL_CSV_DE_LA_PESTAÑA_GENERAL")
SHEET_URL_UMBRELLA = st.secrets.get("SHEET_URL_UMBRELLA", "PEGA_AQUI_LA_URL_CSV_DE_LA_PESTAÑA_UMBRELLA")

@st.cache_data(ttl=300)
def cargar_datos(url):
    return pd.read_csv(url)

# ==========================================
# CREACIÓN DE PESTAÑAS
# ==========================================
tab_general, tab_rechazados = st.tabs(["📋 General", "🚫 Sitios Rechazados (Umbrella)"])


# ==========================================
# PESTAÑA 1: GENERAL
# ==========================================
with tab_general:
    st.header("📋 Reporte General de Sitios")
    
    if SHEET_URL_GENERAL == "PEGA_AQUI_LA_URL_CSV_DE_LA_PESTAÑA_GENERAL":
        st.info("ℹ️ Configura la URL CSV para la Pestaña General en la variable `SHEET_URL_GENERAL`.")
    else:
        try:
            df_general = cargar_datos(SHEET_URL_GENERAL)
            st.dataframe(df_general, use_container_width=True, hide_index=True)
        except Exception as e_gen:
            st.error(f"Error al cargar la pestaña General: {e_gen}")


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

            # Detección de la columna Estado
            col_estado = None
            for col in df_umbrella.columns:
                col_clean = str(col).strip().lower().replace('_', ' ')
                if col_clean in ['estado', 'sub estado', 'subestado', 'status', 'condicion']:
                    col_estado = col
                    break

            if col_estado:
                mask_rechazados = df_umbrella[col_estado].astype(str).str.strip().isin(estados_rechazados)
                df_rechazados = df_umbrella[mask_rechazados].copy()
            else:
                df_rechazados = df_umbrella.copy()

            # --- 2. FILTRADO Y CONSERVACIÓN DE COLUMNAS (PROTECCIÓN EXPLÍCITA PARA Flujo_UUID) ---
            terminos_a_eliminar = [
                'secuencial', 'nombre flujo', 'id sitio', 'idsitio',
                'imagen', 'foto', 'photo', 'img', 'evidencia', 'pic', 'adjunto', 'url', 'link'
            ]

            cols_para_drop = []
            for col in df_rechazados.columns:
                col_raw = str(col).strip()
                col_limpia = re.sub(r'[\s_]+', ' ', col_raw).lower()
                
                # Excepción directa: proteger Flujo_UUID para que nunca se descarte
                if col_limpia in ['flujo uuid', 'flujo_uuid', 'uuid']:
                    continue

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

            # --- 4. FORMATO DE FECHAS (Evita ##########) ---
            for col in df_rechazados_clean.columns:
                if 'fecha' in str(col).lower():
                    fecha_parsed = pd.to_datetime(df_rechazados_clean[col], errors='coerce', dayfirst=True)
                    df_rechazados_clean[col] = fecha_parsed.dt.strftime('%Y-%m-%d').fillna(df_rechazados_clean[col].astype(str))
                    df_rechazados_clean[col] = df_rechazados_clean[col].replace({'nan': '', 'None': '', '<NaT>': ''})

            # --- 5. BUSCADOR POR NOMBRE DE SITIO O Flujo_UUID ---
            col_sitio = None
            for col in df_rechazados_clean.columns:
                col_norm = str(col).strip().lower().replace('_', ' ')
                if col_norm in ['nombre sitio', 'nombre_sitio', 'sitio b', 'sitio_b', 'sitio']:
                    col_sitio = col
                    break

            col_uuid = None
            for col in df_rechazados_clean.columns:
                if str(col).strip().lower() in ['flujo_uuid', 'flujo uuid']:
                    col_uuid = col
                    break

            search_query = st.text_input(
                "🔍 **Buscar por Nombre de Sitio o Flujo_UUID:**",
                placeholder="Ejemplo: NAR.Santa Cecilia o 46977E-9118CE...",
                key="search_sitio_umbrella"
            )

            if search_query.strip():
                query = search_query.strip()
                condiciones = []
                if col_sitio:
                    condiciones.append(df_rechazados_clean[col_sitio].astype(str).str.contains(query, case=False, na=False))
                if col_uuid:
                    condiciones.append(df_rechazados_clean[col_uuid].astype(str).str.contains(query, case=False, na=False))
                
                if condiciones:
                    mask_search = condiciones[0]
                    for cond in condiciones[1:]:
                        mask_search |= cond
                    df_rechazados_clean = df_rechazados_clean[mask_search]
                else:
                    mask_search = df_rechazados_clean.astype(str).apply(
                        lambda row: row.str.contains(query, case=False, na=False)
                    ).any(axis=1)
                    df_rechazados_clean = df_rechazados_clean[mask_search]

            # --- 6. REORDENAR COLUMNAS PARA VISUALIZACIÓN ---
            # Ubicación preferencial al inicio: Nombre_Sitio -> Estado -> Fecha_Estado -> Flujo_UUID
            cols = list(df_rechazados_clean.columns)
            prioridad = [col_sitio, col_estado, col_fecha_estado, col_uuid]
            prioridad_existente = [c for c in prioridad if c and c in cols]

            for c in prioridad_existente:
                cols.remove(c)

            df_rechazados_clean = df_rechazados_clean[prioridad_existente + cols]

            # --- 7. PRESENTACIÓN DE RESULTADOS ---
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
