import json
import logging
import re
import os
import pandas as pd
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class CallCenterProcessor:

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"No se encontró config.json en: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        for semana, rango in config.get("semanas", {}).items():
            try:
                datetime.strptime(rango["fecha_inicio"], "%Y-%m-%d")
                datetime.strptime(rango["fecha_fin"], "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Fecha inválida en {semana}: {e}")

        return config

    def convertir_duracion_a_segundos(self, duracion_str) -> int:
        if pd.isna(duracion_str) or duracion_str is None:
            return 0
        s = str(duracion_str).strip()
        if not s or s in ("nan", "None", ""):
            return 0
        # Formato "252s (4m 12s)" o "13s" — tomar el número inicial en segundos
        match = re.match(r"^(\d+)s", s)
        if match:
            return int(match.group(1))
        # Formato "2m30s" o "2m"
        match = re.fullmatch(r"(?:(\d+)m)?(?:(\d+)s)?", s)
        if match and (match.group(1) or match.group(2)):
            minutos = int(match.group(1)) if match.group(1) else 0
            segundos = int(match.group(2)) if match.group(2) else 0
            return minutos * 60 + segundos
        return 0

    def _buscar_excel_entrada(self) -> str:
        carpeta = "data/entrada"
        for nombre in os.listdir(carpeta):
            if nombre.lower().endswith((".xls", ".xlsx")):
                ruta = os.path.join(carpeta, nombre)
                logger.info(f"Archivo detectado: {ruta}")
                return ruta
        raise FileNotFoundError(f"No se encontró ningún archivo .xls/.xlsx en '{carpeta}'")

    def _leer_excel(self) -> pd.DataFrame:
        archivo = self._buscar_excel_entrada()
        engine = "xlrd" if archivo.lower().endswith(".xls") else "openpyxl"
        df = pd.read_excel(archivo, engine=engine)
        df.columns = [str(c).strip() for c in df.columns]
        logger.info(f"Excel leído: {len(df)} filas, columnas: {list(df.columns)}")
        return df

    def _detectar_columnas(self, df: pd.DataFrame) -> dict:
        """Detecta los nombres reales de las columnas clave de forma flexible."""
        cols = {c.strip(): c for c in df.columns}
        cols_lower = {c.lower(): c for c in df.columns}

        def buscar(candidatos):
            for cand in candidatos:
                if cand in cols:
                    return cols[cand]
                if cand.lower() in cols_lower:
                    return cols_lower[cand.lower()]
            return None

        mapa = {
            "duracion": buscar(["Duración", "Duracion", "duracion", "duración", "Duration", "duration", "Dur"]),
            "extension": buscar(["Fuente", "fuente", "Extensión", "Extension", "extension", "Ext", "ext", "Agente", "agente", "Agent"]),
            "fecha": buscar(["Fecha", "fecha", "Date", "date", "Fecha/Hora", "DateTime", "datetime"]),
            "destino": buscar(["Destino", "destino", "Destination", "destination"]),
        }
        return mapa

    def _limpiar_datos(self, df: pd.DataFrame) -> pd.DataFrame:
        mapa_cols = self._detectar_columnas(df)

        col_duracion = mapa_cols.get("duracion")
        col_extension = mapa_cols.get("extension")
        col_fecha = mapa_cols.get("fecha")
        col_destino = mapa_cols.get("destino")

        total_inicial = len(df)

        if col_destino:
            antes = len(df)
            df = df[~df[col_destino].astype(str).str.strip().str.lower().isin(["1", "s"])].copy()
            descartados_destino = antes - len(df)
            if descartados_destino:
                logger.info(f"Descartados por Destino '1' o 's': {descartados_destino}")

        asesores_cfg = self.config.get("asesores", {})

        if col_extension:
            def normalizar_ext(v):
                if pd.isna(v) or v == "":
                    return ""
                num = str(v).strip()
                try:
                    num = str(int(float(num)))
                except ValueError:
                    pass
                return num

            df["_ext_norm"] = df[col_extension].apply(normalizar_ext)
            antes = len(df)
            df = df[df["_ext_norm"].isin(asesores_cfg.keys())].copy()
            descartados_ext = antes - len(df)
            if descartados_ext:
                logger.info(f"Descartados por extensión no mapeada: {descartados_ext}")
            df["Nombre_Asesor"] = df["_ext_norm"].map(asesores_cfg)
            df.drop(columns=["_ext_norm"], inplace=True)
        else:
            logger.warning("No se encontró columna de extensión/asesor; se asignará 'DESCONOCIDO'")
            df["Nombre_Asesor"] = "DESCONOCIDO"

        if col_duracion:
            df["Duración_Segundos"] = df[col_duracion].apply(self.convertir_duracion_a_segundos)
        else:
            logger.warning("No se encontró columna de duración; se asignará 0")
            df["Duración_Segundos"] = 0

        if col_fecha:
            df["Fecha"] = pd.to_datetime(df[col_fecha], errors="coerce")
        else:
            df["Fecha"] = pd.NaT

        duracion_min = self.config.get("duracion_minima_segundos", 30)
        df_filtrado = df[df["Duración_Segundos"] >= duracion_min].copy()

        logger.info(
            f"Total inicial: {total_inicial} | Con asesor mapeado: {len(df)} | "
            f">= {duracion_min}s: {len(df_filtrado)}"
        )
        return df_filtrado

    def procesar(self) -> pd.DataFrame:
        logger.info("Iniciando procesamiento...")
        df_raw = self._leer_excel()
        df_limpio = self._limpiar_datos(df_raw)
        logger.info("Procesamiento completado.")
        return df_limpio
