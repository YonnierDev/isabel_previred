import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class WeeklyAggregator:

    def __init__(self, config: dict):
        self.config = config
        self.semanas = self._parsear_semanas()

    def _parsear_semanas(self) -> list[dict]:
        semanas = []
        for clave, rango in self.config.get("semanas", {}).items():
            num = clave.split("_")[-1]
            inicio = datetime.strptime(rango["fecha_inicio"], "%Y-%m-%d").date()
            fin = datetime.strptime(rango["fecha_fin"], "%Y-%m-%d").date()
            semanas.append({
                "clave": clave,
                "label": f"SEM{num}",
                "inicio": inicio,
                "fin": fin,
                "fechas": f"{inicio.strftime('%d/%m')} - {fin.strftime('%d/%m')}",
            })
        return sorted(semanas, key=lambda s: s["inicio"])

    def obtener_semana_de_fecha(self, fecha) -> str | None:
        if pd.isna(fecha):
            return None
        try:
            d = fecha.date() if hasattr(fecha, "date") else fecha
            for s in self.semanas:
                if s["inicio"] <= d <= s["fin"]:
                    return s["label"]
        except Exception:
            pass
        return None

    def agrupar_por_asesor(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["Asesor", ">= 30 Seg"])

        resultado = (
            df.groupby("Nombre_Asesor", sort=True)
            .agg(**{">= 30 Seg": ("Nombre_Asesor", "count")})
            .reset_index()
            .rename(columns={"Nombre_Asesor": "Asesor"})
        )
        resultado[">= 30 Seg"] = resultado[">= 30 Seg"].astype(int)
        return resultado

    def agrupar_por_semana(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["Semana", ">= 30 Seg"])

        df = df.copy()
        df["Semana"] = df["Fecha"].apply(self.obtener_semana_de_fecha)

        fuera_rango = df["Semana"].isna().sum()
        if fuera_rango:
            logger.info(f"Llamadas fuera de rangos de semanas configurados: {fuera_rango}")

        df_con_semana = df[df["Semana"].notna()]
        orden_semanas = [s["label"] for s in self.semanas]

        resultado = (
            df_con_semana.groupby("Semana", sort=False)
            .agg(**{">= 30 Seg": ("Nombre_Asesor", "count")})
            .reset_index()
        )
        resultado[">= 30 Seg"] = resultado[">= 30 Seg"].astype(int)

        resultado["_orden"] = resultado["Semana"].apply(
            lambda x: orden_semanas.index(x) if x in orden_semanas else 999
        )
        resultado = resultado.sort_values("_orden").drop(columns=["_orden"]).reset_index(drop=True)
        return resultado

    def agrupar_por_semana_y_asesor(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["Semana", "Fechas", "Asesor", ">= 30 Seg"])

        df = df.copy()
        df["Semana"] = df["Fecha"].apply(self.obtener_semana_de_fecha)
        df_con_semana = df[df["Semana"].notna()]

        label_a_fechas = {s["label"]: s["fechas"] for s in self.semanas}
        orden_semanas = [s["label"] for s in self.semanas]

        resultado = (
            df_con_semana.groupby(["Semana", "Nombre_Asesor"], sort=False)
            .agg(**{">= 30 Seg": ("Nombre_Asesor", "count")})
            .reset_index()
            .rename(columns={"Nombre_Asesor": "Asesor"})
        )
        resultado[">= 30 Seg"] = resultado[">= 30 Seg"].astype(int)
        resultado["Fechas"] = resultado["Semana"].map(label_a_fechas)

        resultado["_orden"] = resultado["Semana"].apply(
            lambda x: orden_semanas.index(x) if x in orden_semanas else 999
        )
        resultado = (
            resultado.sort_values(["_orden", "Asesor"])
            .drop(columns=["_orden"])
            .reset_index(drop=True)
            [["Semana", "Fechas", "Asesor", ">= 30 Seg"]]
        )
        return resultado
