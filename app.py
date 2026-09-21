import re
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Control Semanal de Sitios", page_icon="📡", layout="wide"
)

# ==========================================
# ESTILOS CSS PERSONALIZADOS
# ==========================================
st.markdown(
    """
    <style>
        /* Ocultar el label predeterminado del st.radio */
        div[data-testid="stRadio"] > label {
            display: none !important;
        }

        /* Centrar el contenedor general del selector de tableros */
        div[data-testid="stRadio"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
            margin-top: 10px !important;
            margin-bottom: 30px !important;
        }

        /* Contenedor tipo píldora (Segmented Control) */
        div[data-testid="stRadio"] > div {
            display: inline-flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 10px !important;
            background-color: #f1f5f9 !important;
            padding: 6px 10px !important;
            border-radius: 9999px !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: inset 0px 1px 2px rgba(0, 0, 0, 0.04) !important;
            width: auto !important;
        }

        /* Estilo base de cada botón individual */
        div[data-testid="stRadio"] label {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 9999px !important;
            padding: 10px 28px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #475569 !important;
            cursor: pointer !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.05) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            user-select: none !important;
        }

        /* Ocultar el punto/círculo nativo de radio button */
        div[data-testid="stRadio"] label > div:first-child {
            display: none !important;
        }

        /* Efecto al pasar el cursor (Hover) */
        div[data-testid="stRadio"] label:hover {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            border-color: #94a3b8 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.08) !important;
        }

        /* Estilo del Botón SELECCIONADO / ACTIVO */
        div[data-testid="stRadio"] label:has(input:checked) {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            border-color: #1d4ed8 !important;
            font-weight: 700 !important;
            box-shadow: 0px 4px 14px rgba(37, 99, 235, 0.38) !important;
            transform: translateY(-1px) !important;
        }

        /* Barras de desplazamiento notorias */
        ::-webkit-scrollbar {
            width: 14px !important;
            height: 14px !important;
        }
        ::-webkit-scrollbar-track {
            background: #e2e8f0 !important;
            border-radius: 7px !important;
        }
        ::-webkit-scrollbar-thumb {
            background: #64748b !important;
            border-radius: 7px !important;
            border: 3px solid #e2e8f0 !important;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569 !important;
        }

        /* Tarjeta contenedora de Sincronización en Sidebar */
        .sync-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        /* Tarjeta contenedora para filtros */
        .filter-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }

        /* Badges de estado */
        .badge {
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            color: white;
            display: inline-block;
            margin-right: 6px;
            font-size: 13px;
        }
        .badge-red { background-color: #dc3545; }
        .badge-yellow { background-color: #f39c12; }
        .badge-green { background-color: #198754; }
        .badge-gray { background-color: #6c757d; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_tarjeta_metrica(label, value, bg_color, border_color, text_color):
  st.markdown(
      f"""
        <div style="
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease-in-out;
            margin-bottom: 10px;
        ">
            <div style="font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{label}</div>
            <div style="font-size: 30px; font-weight: 700; color: {text_color};">{value}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )


st.title("📡 Tablero de Control de Sitios")

# ==========================================
# CONFIGURACIÓN DE URLS Y CONTRASEÑA
# ==========================================
SHEET_URL_GENERAL = st.secrets.get(
    "SHEET_URL_GENERAL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?output=csv",
)
SHEET_URL_UMBRELLA = st.secrets.get(
    "SHEET_URL_UMBRELLA",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQliAhmZ9J0AnBghSj6yqLMWnjIDypEAZJ73ayyr9Z91uBa5zzsv1sf3RE2OtvEGz4j8R0o0y_YY9sj/pub?gid=644478638&single=true&output=csv",
)

PASSWORD_CORRECTA = st.secrets.get("SYNC_PASSWORD", "admin123")


@st.cache_data(ttl=60)
def cargar_datos(url):
  return pd.read_csv(url)


@st.dialog("🔐 Confirmación requerida")
def modal_autenticacion():
  st.write("Ingresa la contraseña para actualizar información:")
  pwd_input = st.text_input("Contraseña", type="password")

  if st.button("Confirmar y Sincronizar", use_container_width=True):
    if pwd_input == PASSWORD_CORRECTA:
      st.cache_data.clear()
      st.success("¡Datos actualizados correctamente!")
      st.rerun()
    else:
      st.error("❌ Contraseña incorrecta. Intenta nuevamente.")


with st.sidebar:
  st.markdown(
      """
    <div class="sync-card">
        <h3 style="margin-top: 0; color: #1e293b; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
            🔄 Sincronización
        </h3>
        <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 12px;">
            Forzar actualización en tiempo real borrando el caché local de Google Sheets.
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  if st.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    modal_autenticacion()

tab_seleccionada = st.radio(
    "Selecciona el tablero:",
    ["📋 General BSS", "🚫 Sitios Rechazados (Umbrella)"],
    horizontal=True,
    key="navegacion_tableros",
)


# ==========================================
# PESTAÑA 1: GENERAL BSS
# ==========================================
if tab_seleccionada == "📋 General BSS":
  st.write(
      "Sincronización en tiempo real (Excluyendo sitios en **PRODUCCIÓN**)."
  )

  st.markdown(
      """
    <div style="margin-bottom: 20px;">
        <b>Leyenda de Condición (Sitios sin OnAir):</b> 
        <span class="badge badge-red">Crítico</span> 
        <span class="badge badge-yellow">Alerta</span> 
        <span class="badge badge-green">En Norma</span> 
        <span class="badge badge-gray">Pendiente Integración</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  try:
    df = cargar_datos(SHEET_URL_GENERAL)

    required_cols = {
        "Site Name",
        "Proyecto",
        "Territorio Comercial",
        "SS IMP",
        "Integracion",
        "Estado Macro",
        "Estado Insrv",
    }
    if not required_cols.issubset(df.columns):
      st.error(
          "Faltan columnas requeridas en la hoja de Google Sheets. Se esperaban"
          f" al menos: {required_cols}"
      )
    else:
      df_proc = df.copy()

      df_proc = df_proc[
          df_proc["Estado Macro"].astype(str).str.strip().str.upper()
          != "PRODUCCIÓN"
      ]

      df_proc["Fecha_Integracion_DT"] = pd.to_datetime(
          df_proc["Integracion"], dayfirst=True, errors="coerce"
      )

      if "OnAir" in df_proc.columns:
        df_proc["Fecha_OnAir_DT"] = pd.to_datetime(
            df_proc["OnAir"], dayfirst=True, errors="coerce"
        )
      else:
        df_proc["Fecha_OnAir_DT"] = pd.NaT

      fecha_actual = pd.Timestamp.now().floor("d")

      df_proc["Dias_Desde_Integracion"] = (
          fecha_actual - df_proc["Fecha_Integracion_DT"]
      ).dt.days

      def clasificar_condicion(row):
        if pd.notna(row["Fecha_OnAir_DT"]):
          return "Completado"
        elif pd.isna(row["Fecha_Integracion_DT"]):
          return "Pendiente Integración"
        elif row["Dias_Desde_Integracion"] >= 16:
          return "Crítico"
        elif row["Dias_Desde_Integracion"] >= 8:
          return "Alerta"
        elif row["Dias_Desde_Integracion"] >= 0:
          return "En Norma"
        else:
          return "Fecha Futura / Error"

      df_proc["Condición / Estado"] = df_proc.apply(
          clasificar_condicion, axis=1
      )

      prioridad_map = {
          "Crítico": 1,
          "Alerta": 2,
          "En Norma": 3,
          "Pendiente Integración": 4,
          "Completado": 5,
          "Fecha Futura / Error": 6,
      }
      df_proc["Prioridad"] = df_proc["Condición / Estado"].map(prioridad_map)
      df_proc = df_proc.sort_values(
          by=["Prioridad", "Dias_Desde_Integracion"], ascending=[True, False]
      )

      st.sidebar.markdown("---")
      st.sidebar.header("🔍 Filtros General BSS")

      df_filtrado = df_proc.copy()

      condiciones = ["Todos"] + sorted(
          list(df_filtrado["Condición / Estado"].dropna().astype(str).unique())
      )
      condicion_sel = st.sidebar.selectbox(
          "Filtrar por Condición / Alerta", condiciones
      )
      if condicion_sel != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["Condición / Estado"] == condicion_sel
        ]

      proyectos = ["Todos"] + sorted(
          list(df_filtrado["Proyecto"].dropna().astype(str).unique())
      )
      proyecto_sel = st.sidebar.selectbox("Filtrar por Proyecto", proyectos)
      if proyecto_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Proyecto"] == proyecto_sel]

      contratistas = ["Todos"] + sorted(
          list(df_filtrado["SS IMP"].dropna().astype(str).unique())
      )
      contratista_sel = st.sidebar.selectbox(
          "Filtrar por Contratista (SS IMP)", contratistas
      )
      if contratista_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["SS IMP"] == contratista_sel]

      estados_macro = ["Todos"] + sorted(
          list(df_filtrado["Estado Macro"].dropna().astype(str).unique())
      )
      estado_macro_sel = st.sidebar.selectbox(
          "Filtrar por Estado Macro", estados_macro
      )
      if estado_macro_sel != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["Estado Macro"] == estado_macro_sel
        ]

      busqueda = st.sidebar.text_input("Buscar por Sitio (Site Name)")
      if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado["Site Name"]
            .astype(str)
            .str.contains(busqueda, case=False, na=False)
        ]

      st.subheader("Lista de Sitios Pendientes")

      st.markdown('<div class="filter-card">', unsafe_allow_html=True)
      territorios = ["Todos"] + sorted(
          list(df_filtrado["Territorio Comercial"].dropna().astype(str).unique())
      )
      territorio_sel = st.selectbox(
          "🌐 **Filtrar por Regional**", territorios, key="filtro_region_main"
      )
      st.markdown("</div>", unsafe_allow_html=True)

      if territorio_sel != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["Territorio Comercial"] == territorio_sel
        ]

      col1, col2, col3, col4, col5 = st.columns(5)
      with col1:
        render_tarjeta_metrica(
            "Total Sitios Pendientes",
            len(df_filtrado),
            "#f8fafc",
            "#cbd5e1",
            "#0f172a",
        )
      with col2:
        render_tarjeta_metrica(
            "Críticos",
            (df_filtrado["Condición / Estado"] == "Crítico").sum(),
            "#fdf2f2",
            "#f8b4b4",
            "#9b2c2c",
        )
      with col3:
        render_tarjeta_metrica(
            "Alerta",
            (df_filtrado["Condición / Estado"] == "Alerta").sum(),
            "#fffaf0",
            "#fbd38d",
            "#9c4221",
        )
      with col4:
        render_tarjeta_metrica(
            "En Norma",
            (df_filtrado["Condición / Estado"] == "En Norma").sum(),
            "#f0fff4",
            "#9ae6b4",
            "#22543d",
        )
      with col5:
        render_tarjeta_metrica(
            "Completados",
            (df_filtrado["Condición / Estado"] == "Completado").sum(),
            "#ebf8ff",
            "#90cdf4",
            "#2b6cb0",
        )

      st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

      df_display = df_filtrado.copy()
      df_display["Días Transcurridos"] = df_display[
          "Dias_Desde_Integracion"
      ].apply(
          lambda x: (
              f"{int(x)} días" if pd.notna(x) else "Sin Fecha Integración"
          )
      )

      if "Territorio Comercial" in df_display.columns:
        df_display = df_display.rename(
            columns={"Territorio Comercial": "Regional"}
        )

      cols_ordenadas = [
          "Site Name",
          "Condición / Estado",
          "Días Transcurridos",
          "Regional",
          "Integracion",
          "FC Visita",
          "Estado Macro",
          "Estado Insrv",
          "Sub Estado Insrv",
          "Comentario",
          "Proyecto",
          "SS IMP",
      ]

      cols_existentes = [
          c for c in cols_ordenadas if c in df_display.columns
      ]
      otras_cols = [
          c
          for c in df_display.columns
          if c not in cols_existentes
          and c
          not in [
              "Region",
              "Fecha_Integracion_DT",
              "Fecha_OnAir_DT",
              "Dias_Desde_Integracion",
              "Prioridad",
          ]
      ]

      df_final = df_display[cols_existentes + otras_cols]

      def colorear_condicion(val):
        if val == "Crítico":
          return (
              "background-color: #f8d7da; color: #842029; font-weight: bold;"
          )
        elif val == "Alerta":
          return (
              "background-color: #fff3cd; color: #664d03; font-weight: bold;"
          )
        elif val == "En Norma":
          return (
              "background-color: #d1e7dd; color: #0f5132; font-weight: bold;"
          )
        elif val == "Pendiente Integración":
          return (
              "background-color: #e2e3e5; color: #41464b; font-weight: bold;"
          )
        elif val == "Completado":
          return "background-color: #cff4fc; color: #055160;"
        else:
          return ""

      styled_df = df_final.style.map(
          colorear_condicion, subset=["Condición / Estado"]
      )

      st.dataframe(
          styled_df,
          use_container_width=True,
          hide_index=True,
          column_config={
              "Site Name": st.column_config.TextColumn(
                  "Site Name", width="medium", pinned=True
              ),
              "Condición / Estado": st.column_config.TextColumn(
                  "Condición / Estado", width="medium"
              ),
              "Días Transcurridos": st.column_config.TextColumn(
                  "Días Transcurridos", width="small"
              ),
              "Regional": st.column_config.TextColumn(
                  "Regional", width="medium"
              ),
              "FC Visita": st.column_config.TextColumn(
                  "FC Visita", width="medium"
              ),
              "Comentario": st.column_config.TextColumn(
                  "Comentario", width="large"
              ),
              "Proyecto": st.column_config.TextColumn(
                  "Proyecto", width="medium"
              ),
              "SS IMP": st.column_config.TextColumn("SS IMP", width="medium"),
          },
      )

      csv_gen = df_final.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Descargar Reporte General (CSV)",
          data=csv_gen,
          file_name=(
              "control_semanal_bss_pendientes_"
              f"{datetime.now().strftime('%Y%m%d')}.csv"
          ),
          mime="text/csv",
      )

  except Exception as e:
    st.error(f"Error al conectar con la pestaña General de Google Sheets: {e}")


# ==========================================
# PESTAÑA 2: SITIOS RECHAZADOS (PESTAÑA UMBRELLA)
# ==========================================
elif tab_seleccionada == "🚫 Sitios Rechazados (Umbrella)":
  st.header("🚫 Registro de Sitios Rechazados Umbrella")

  st.markdown(
      """
    <div style="margin-bottom: 20px;">
        <b>Leyenda de Condición (Sitios Rechazados Umbrella):</b> 
        <span class="badge badge-red">Crítico</span> 
        <span class="badge badge-yellow">Alerta</span> 
        <span class="badge badge-green">En Norma</span> 
        <span class="badge badge-gray">Sin Fecha Estado</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

  if SHEET_URL_UMBRELLA == "PEGA_AQUI_LA_URL_CSV_DE_LA_PESTAÑA_UMBRELLA":
    st.warning(
        "⚠️ Debes publicar la pestaña 'umbrella' en Google Sheets como CSV y"
        " pegar la URL en la variable `SHEET_URL_UMBRELLA`."
    )
  else:
    try:
      df_umbrella = cargar_datos(SHEET_URL_UMBRELLA)

      st.sidebar.markdown("---")
      st.sidebar.header("🔍 Filtros Umbrella")

      # Casilla opcional para ocultar aprobados (falso por defecto para que NO borre los rechazos NOC)
      excluir_aprobados = st.sidebar.checkbox(
          "Excluir flujos/sitios con estado 'Aprobado'", value=False
      )

      cols_estado_posibles = []
      col_estado = None
      for col in df_umbrella.columns:
        col_clean = str(col).strip().lower().replace("_", " ")
        if any(
            k in col_clean
            for k in ["estado", "status", "condicion", "sub estado"]
        ):
          cols_estado_posibles.append(col)
          if col_clean in [
              "estado",
              "sub estado",
              "subestado",
              "status",
              "condicion",
          ]:
            if not col_estado:
              col_estado = col

      if not col_estado and cols_estado_posibles:
        col_estado = cols_estado_posibles[0]

      col_sitio = None
      for col in df_umbrella.columns:
        col_norm = str(col).strip().lower().replace("_", " ")
        if col_norm in [
            "nombre sitio",
            "nombre_sitio",
            "sitio b",
            "sitio_b",
            "sitio",
        ]:
          col_sitio = col
          break

      col_uuid = None
      for col in df_umbrella.columns:
        if str(col).strip().lower() in ["flujo_uuid", "flujo uuid", "uuid"]:
          col_uuid = col
          break

      col_agrupador = col_uuid if col_uuid else col_sitio

      df_base = df_umbrella.copy()

      if excluir_aprobados and col_estado and col_agrupador:
        mask_aprobados = (
            df_base[col_estado]
            .astype(str)
            .str.strip()
            .str.contains("Aprobado", case=False, na=False)
        )
        flujos_aprobados = df_base[mask_aprobados][col_agrupador].dropna().unique()
        df_base = df_base[~df_base[col_agrupador].isin(flujos_aprobados)]

      # BÚSQUEDA MULTICOLUMNA DE RECHAZOS (Captura NOC, RF, Rechazo, Rechazado, etc.)
      patron_rechazo = r"Rechaz|Rechazo|NOC|RF|Devuelto"

      if cols_estado_posibles:
        mask_rechazados = pd.Series(False, index=df_base.index)
        for c in cols_estado_posibles:
          mask_rechazados |= (
              df_base[c]
              .astype(str)
              .str.contains(patron_rechazo, case=False, na=False)
          )
        df_rechazados = df_base[mask_rechazados].copy()
      else:
        df_rechazados = df_base.copy()

      terminos_a_eliminar = [
          "secuencial",
          "nombre flujo",
          "id sitio",
          "idsitio",
          "imagen",
          "foto",
          "photo",
          "img",
          "evidencia",
          "pic",
          "adjunto",
          "url",
          "link",
          "solicitante",
          "zona comercial",
          "regional",
          "diseñador",
          "site owner",
          "owner soporte zona",
          "sistema de energia instalar",
          "odh",
          "proyecto",
          "smp",
          "wo",
          "tecnologia",
          "escenario modernizacion",
          "truno performance",
          "turno performance",
          "metodo recepcion",
          "operacion planta electrica",
      ]

      cols_para_drop = []
      for col in df_rechazados.columns:
        col_raw = str(col).strip()
        col_limpia = re.sub(r"[\s_]+", " ", col_raw).lower()

        if (
            col_limpia in ["flujo uuid", "flujo_uuid", "uuid"]
            or col in cols_estado_posibles
        ):
          continue

        if any(
            term == col_limpia or term in col_limpia
            for term in terminos_a_eliminar
        ):
          cols_para_drop.append(col)

      df_rechazados_clean = df_rechazados.drop(
          columns=cols_para_drop, errors="ignore"
      ).copy()

      col_fecha_estado = None
      for col in df_rechazados_clean.columns:
        col_limpia = str(col).strip().lower().replace("_", " ")
        if "fecha estado" in col_limpia or "fecha_estado" in col_limpia:
          col_fecha_estado = col
          break

      if col_fecha_estado:
        fechas_dt = pd.to_datetime(
            df_rechazados_clean[col_fecha_estado],
            errors="coerce",
            format="mixed",
        )
        # Mantener registros de 2026 y aquellos que no tengan fecha para evitar perder información
        df_2026 = df_rechazados_clean[
            (fechas_dt.dt.year == 2026) | (fechas_dt.isna())
        ].copy()
        if not df_2026.empty:
          df_rechazados_clean = df_2026

      if col_fecha_estado:
        fechas_estado_dt = pd.to_datetime(
            df_rechazados_clean[col_fecha_estado],
            errors="coerce",
            format="mixed",
        )
        fecha_actual_umb = pd.Timestamp.now().floor("d")
        df_rechazados_clean["Dias_Num_Umbrella"] = (
            fecha_actual_umb - fechas_estado_dt
        ).dt.days

        def clasificar_condicion_umbrella(row):
          dias = row["Dias_Num_Umbrella"]
          if pd.isna(dias):
            return "Sin Fecha Estado"
          elif dias >= 16:
            return "Crítico"
          elif dias >= 8:
            return "Alerta"
          elif dias >= 0:
            return "En Norma"
          else:
            return "Fecha Futura / Error"

        df_rechazados_clean["Condición / Estado"] = df_rechazados_clean.apply(
            clasificar_condicion_umbrella, axis=1
        )
      else:
        df_rechazados_clean["Dias_Num_Umbrella"] = pd.NA
        df_rechazados_clean["Condición / Estado"] = "Sin Fecha Estado"

      prioridad_map_umb = {
          "Crítico": 1,
          "Alerta": 2,
          "En Norma": 3,
          "Sin Fecha Estado": 4,
          "Fecha Futura / Error": 5,
      }
      df_rechazados_clean["Prioridad"] = df_rechazados_clean[
          "Condición / Estado"
      ].map(prioridad_map_umb)
      df_rechazados_clean = df_rechazados_clean.sort_values(
          by=["Prioridad", "Dias_Num_Umbrella"], ascending=[True, False]
      )

      conds_umb = ["Todos"] + sorted(
          list(
              df_rechazados_clean["Condición / Estado"]
              .dropna()
              .astype(str)
              .unique()
          )
      )
      cond_umb_sel = st.sidebar.selectbox(
          "Filtrar Umbrella por Condición", conds_umb
      )

      if cond_umb_sel != "Todos":
        df_rechazados_clean = df_rechazados_clean[
            df_rechazados_clean["Condición / Estado"] == cond_umb_sel
        ]

      for col in df_rechazados_clean.columns:
        if "fecha" in str(col).lower() and col not in [
            "Días Transcurridos",
            "Condición / Estado",
        ]:
          fecha_parsed = pd.to_datetime(
              df_rechazados_clean[col], errors="coerce", format="mixed"
          )
          df_rechazados_clean[col] = (
              fecha_parsed.dt.strftime("%Y-%m-%d").fillna(
                  df_rechazados_clean[col].astype(str)
              )
          )
          df_rechazados_clean[col] = df_rechazados_clean[col].replace(
              {"nan": "", "None": "", "<NaT>": ""}
          )

      col_input, col_btn = st.columns([4, 1])

      with col_input:
        search_query = st.text_input(
            "🔍 **Buscar por Nombre de Sitio o Flujo_UUID:**",
            placeholder="Ejemplo: BOG.RB TIBABITA o NOC...",
            key="search_sitio_umbrella",
        )

      with col_btn:
        st.write("##")
        btn_buscar = st.button(
            "🔍 Buscar", key="btn_buscar_umbrella", use_container_width=True
        )

      if search_query.strip() and (
          btn_buscar or st.session_state.get("search_sitio_umbrella")
      ):
        query = search_query.strip()
        condiciones = []
        if col_sitio:
          condiciones.append(
              df_rechazados_clean[col_sitio]
              .astype(str)
              .str.contains(query, case=False, na=False)
          )
        if col_uuid:
          condiciones.append(
              df_rechazados_clean[col_uuid]
              .astype(str)
              .str.contains(query, case=False, na=False)
          )

        if condiciones:
          mask_search = condiciones[0]
          for cond in condiciones[1:]:
            mask_search |= cond
          df_rechazados_clean = df_rechazados_clean[mask_search]
        else:
          mask_search = (
              df_rechazados_clean.astype(str)
              .apply(
                  lambda row: row.str.contains(query, case=False, na=False)
              )
              .any(axis=1)
          )
          df_rechazados_clean = df_rechazados_clean[mask_search]

      df_rechazados_clean["Días Transcurridos"] = df_rechazados_clean[
          "Dias_Num_Umbrella"
      ].apply(lambda x: f"{int(x)} días" if pd.notna(x) else "Sin Fecha Estado")

      c1, c2, c3, c4 = st.columns(4)
      with c1:
        render_tarjeta_metrica(
            "Total Rechazados",
            len(df_rechazados_clean),
            "#f8fafc",
            "#cbd5e1",
            "#0f172a",
        )
      with c2:
        render_tarjeta_metrica(
            "Críticos",
            (df_rechazados_clean["Condición / Estado"] == "Crítico").sum(),
            "#fdf2f2",
            "#f8b4b4",
            "#9b2c2c",
        )
      with c3:
        render_tarjeta_metrica(
            "Alerta",
            (df_rechazados_clean["Condición / Estado"] == "Alerta").sum(),
            "#fffaf0",
            "#fbd38d",
            "#9c4221",
        )
      with c4:
        render_tarjeta_metrica(
            "En Norma",
            (df_rechazados_clean["Condición / Estado"] == "En Norma").sum(),
            "#f0fff4",
            "#9ae6b4",
            "#22543d",
        )

      st.markdown("---")

      cols = list(df_rechazados_clean.columns)
      prioridad = [
          col_sitio,
          "Condición / Estado",
          "Días Transcurridos",
          col_estado,
          col_fecha_estado,
          col_uuid,
      ]
      prioridad_existente = [c for c in prioridad if c and c in cols]

      for c in prioridad_existente:
        cols.remove(c)

      for col_aux in ["Dias_Num_Umbrella", "Prioridad"]:
        if col_aux in cols:
          cols.remove(col_aux)

      df_rechazados_final = df_rechazados_clean[prioridad_existente + cols]

      def colorear_condicion_umb(val):
        if val == "Crítico":
          return (
              "background-color: #f8d7da; color: #842029; font-weight: bold;"
          )
        elif val == "Alerta":
          return (
              "background-color: #fff3cd; color: #664d03; font-weight: bold;"
          )
        elif val == "En Norma":
          return (
              "background-color: #d1e7dd; color: #0f5132; font-weight: bold;"
          )
        elif val == "Sin Fecha Estado":
          return (
              "background-color: #e2e3e5; color: #41464b; font-weight: bold;"
          )
        else:
          return ""

      styled_df_umb = df_rechazados_final.style.map(
          colorear_condicion_umb, subset=["Condición / Estado"]
      )

      if not df_rechazados_final.empty:
        col_config_umb = {
            "Condición / Estado": st.column_config.TextColumn(
                "Condición / Estado", width="medium"
            ),
            "Días Transcurridos": st.column_config.TextColumn(
                "Días Transcurridos", width="small"
            ),
        }
        if col_sitio:
          col_config_umb[col_sitio] = st.column_config.TextColumn(
              col_sitio, width="medium", pinned=True
          )

        st.dataframe(
            styled_df_umb,
            use_container_width=True,
            hide_index=True,
            column_config=col_config_umb,
        )

        csv_umbrella = df_rechazados_final.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Reporte Umbrella (CSV)",
            data=csv_umbrella,
            file_name=(
                "sitios_rechazados_umbrella_"
                f"{datetime.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
        )
      else:
        st.info(
            "No se encontraron registros rechazados que coincidan con los"
            " criterios."
        )

    except Exception as e_umb:
      st.error(f"Error al cargar la pestaña umbrella: {e_umb}")
