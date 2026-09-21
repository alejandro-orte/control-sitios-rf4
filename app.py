import re
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Control Semanal de Sitios", page_icon="📡", layout="wide"
)

st.markdown(
    """
    <style>
        div[data-testid="stRadio"] > label { display: none !important; }
        div[data-testid="stRadio"] { display: flex !important; justify-content: center !important; width: 100% !important; margin-top: 10px !important; margin-bottom: 30px !important; }
        div[data-testid="stRadio"] > div { display: inline-flex !important; flex-direction: row !important; justify-content: center !important; align-items: center !important; gap: 10px !important; background-color: #f1f5f9 !important; padding: 6px 10px !important; border-radius: 9999px !important; border: 1px solid #cbd5e1 !important; width: auto !important; }
        div[data-testid="stRadio"] label { background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 9999px !important; padding: 10px 28px !important; font-size: 15px !important; font-weight: 600 !important; color: #475569 !important; cursor: pointer !important; transition: all 0.25s ease !important; }
        div[data-testid="stRadio"] label > div:first-child { display: none !important; }
        div[data-testid="stRadio"] label:has(input:checked) { background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%) !important; color: #ffffff !important; border-color: #1d4ed8 !important; font-weight: 700 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_tarjeta_metrica(label, value, bg_color, border_color, text_color):
  st.markdown(
      f"""
        <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 16px 20px; text-align: center; margin-bottom: 10px;">
            <div style="font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 6px;">{label}</div>
            <div style="font-size: 30px; font-weight: 700; color: {text_color};">{value}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )


st.title("📡 Tablero de Control de Sitios")

SHEET_URL_GENERAL = st.secrets.get("SHEET_URL_GENERAL", "URL_CSV_GENERAL")
SHEET_URL_UMBRELLA = st.secrets.get("SHEET_URL_UMBRELLA", "URL_CSV_UMBRELLA")
PASSWORD_CORRECTA = st.secrets.get("SYNC_PASSWORD", "admin123")


@st.cache_data(ttl=60)
def cargar_datos(url):
  return pd.read_csv(url)


@st.dialog("🔐 Confirmación requerida")
def modal_autenticacion():
  pwd_input = st.text_input("Contraseña", type="password")
  if st.button("Confirmar y Sincronizar", use_container_width=True):
    if pwd_input == PASSWORD_CORRECTA:
      st.cache_data.clear()
      st.success("¡Datos actualizados correctamente!")
      st.rerun()
    else:
      st.error("❌ Contraseña incorrecta.")


with st.sidebar:
  if st.button("🔄 Actualizar Datos Ahora", use_container_width=True):
    modal_autenticacion()

tab_seleccionada = st.radio(
    "Selecciona el tablero:",
    ["📋 General BSS", "🚫 Sitios Rechazados (Umbrella)"],
    horizontal=True,
)

# ==========================================
# PESTAÑA 2: SITIOS RECHAZADOS (UMBRELLA)
# ==========================================
if tab_seleccionada == "🚫 Sitios Rechazados (Umbrella)":
  st.header("🚫 Control Umbrella: Rechazos RF / NOC Activos")

  try:
    df_umbrella = cargar_datos(SHEET_URL_UMBRELLA)
    df_base = df_umbrella.copy()

    # Identificación dinámica de columnas
    col_estado = next(
        (
            c
            for c in df_base.columns
            if str(c).strip().lower() in ["estado", "status", "condicion"]
        ),
        None,
    )
    col_plantilla = next(
        (
            c
            for c in df_base.columns
            if "plantilla" in str(c).strip().lower()
            or "tarea" in str(c).strip().lower()
        ),
        None,
    )
    col_sitio = next(
        (
            c
            for c in df_base.columns
            if str(c)
            .strip()
            .lower()
            in ["nombre sitio", "nombre_sitio", "sitio b", "sitio"]
        ),
        None,
    )
    col_uuid = next(
        (
            c
            for c in df_base.columns
            if "uuid" in str(c).strip().lower()
            or "flujo" in str(c).strip().lower()
        ),
        None,
    )
    col_estado_final = next(
        (
            c
            for c in df_base.columns
            if "estado final" in str(c).strip().lower()
            or "estado_final" in str(c).strip().lower()
        ),
        None,
    )

    if not col_estado:
      st.error("No se encontró una columna de 'Estado' en la hoja cargada.")
    else:

      def es_rechazo_rf_noc(txt):
        txt_str = str(txt).upper()
        tiene_rechazo = bool(re.search(r"RECHAZ|DEVUEL", txt_str))
        tiene_rf_noc = bool(re.search(r"\bRF\b|\bNOC\b", txt_str))
        return tiene_rechazo and tiene_rf_noc

      def es_aprobado(txt):
        return bool(
            re.search(r"APROBAD|APPROVED|ONAIR|ON-AIR", str(txt).upper())
        )

      col_grupo = (
          col_uuid if col_uuid else (col_sitio if col_sitio else df_base.index)
      )

      indices_validos = []

      # Evaluamos cada grupo/flujo por separado
      for _, group in df_base.groupby(col_grupo, sort=False):
        # 1. Si el Estado Final del flujo completo ya es Aprobado, descartar
        if col_estado_final and col_estado_final in group.columns:
          if es_aprobado(group[col_estado_final].iloc[0]):
            continue

        # 2. Buscar si dentro del flujo existe alguna etapa con rechazo RF o NOC
        posiciones_rechazo = []
        group_list = group.to_dict("records")

        for idx, row in enumerate(group_list):
          texto_eval = (
              f"{row.get(col_estado, '')} {row.get(col_plantilla, '')}"
          )
          if es_rechazo_rf_noc(texto_eval):
            posiciones_rechazo.append(idx)

        if not posiciones_rechazo:
          continue

        # Nos enfocamos en el último rechazo RF/NOC registrado en el flujo
        idx_ultimo_rechazo = posiciones_rechazo[-1]

        # 3. Validar si en las ETAPAS FUTURAS (posteriores al rechazo) hay algún 'Aprobado'
        etapas_futuras = group_list[idx_ultimo_rechazo + 1 :]
        tiene_aprobado_futuro = False

        for row_futura in etapas_futuras:
          texto_futuro = f"{row_futura.get(col_estado, '')} {row_futura.get(col_plantilla, '')}"
          if es_aprobado(texto_futuro):
            tiene_aprobado_futuro = True
            break

        # Si NO hay ningún Aprobado futuro, conservamos este registro rechazado
        if not tiene_aprobado_futuro:
          # Guardar el índice real de la fila del DataFrame original
          idx_real = group.index[idx_ultimo_rechazo]
          indices_validos.append(idx_real)

      df_rechazados = df_base.loc[indices_validos].copy()

      # FILTROS EN BARRA LATERAL
      st.sidebar.markdown("---")
      st.sidebar.header("🔍 Filtros Umbrella")
      tipo_filtro = st.sidebar.radio(
          "Filtrar por Área:",
          [
              "Todos (Rechazados RF y NOC pendientes)",
              "Solo Rechazados RF",
              "Solo Rechazados NOC",
          ],
      )

      if tipo_filtro == "Solo Rechazados RF":
        df_rechazados = df_rechazados[
            df_rechazados.apply(
                lambda r: bool(
                    re.search(
                        r"\bRF\b",
                        f"{r.get(col_estado, '')} {r.get(col_plantilla, '')}".upper(),
                    )
                ),
                axis=1,
            )
        ]
      elif tipo_filtro == "Solo Rechazados NOC":
        df_rechazados = df_rechazados[
            df_rechazados.apply(
                lambda r: bool(
                    re.search(
                        r"\bNOC\b",
                        f"{r.get(col_estado, '')} {r.get(col_plantilla, '')}".upper(),
                    )
                ),
                axis=1,
            )
        ]

      # BÚSQUEDA Y MÉTRICAS
      search_query = st.text_input(
          "🔍 **Buscar por Sitio, Plantilla o Flujo_UUID:**",
          placeholder="Ej: BOG.RB TIBABITA / Control NOC...",
      )
      if search_query.strip():
        df_rechazados = df_rechazados[
            df_rechazados.astype(str)
            .apply(
                lambda r: r.str.contains(
                    search_query.strip(), case=False, na=False
                )
            )
            .any(axis=1)
        ]

      c1, c2 = st.columns(2)
      with c1:
        render_tarjeta_metrica(
            "Rechazos Activos (RF / NOC)",
            len(df_rechazados),
            "#fdf2f2",
            "#f8b4b4",
            "#9b2c2c",
        )
      with c2:
        render_tarjeta_metrica(
            "Sitios Únicos Afectados",
            (
                df_rechazados[col_sitio].nunique()
                if col_sitio and not df_rechazados.empty
                else 0
            ),
            "#f8fafc",
            "#cbd5e1",
            "#0f172a",
        )

      st.markdown("---")

      if not df_rechazados.empty:
        st.dataframe(df_rechazados, use_container_width=True, hide_index=True)
        csv = df_rechazados.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar Reporte (CSV)",
            data=csv,
            file_name=f"rechazos_rf_noc_pendientes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
      else:
        st.info(
            "No se encontraron sitios con rechazo activo en RF o NOC"
            " pendientes."
        )

  except Exception as e:
    st.error(f"Error al procesar la información de Umbrella: {e}")
