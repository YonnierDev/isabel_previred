import sys
from modules.data_processor import CallCenterProcessor
from modules.week_calculator import WeeklyAggregator
from modules.report_builder import ReportGenerator


def main():
    print("Iniciando procesamiento Call Center...")

    try:
        processor = CallCenterProcessor("config.json")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        df_limpio = processor.procesar()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR al procesar el archivo: {e}")
        sys.exit(1)

    print(f"{len(df_limpio)} llamadas >= 30 segundos procesadas")

    aggregator = WeeklyAggregator(processor.config)
    resumen_asesores = aggregator.agrupar_por_asesor(df_limpio)
    resumen_semanas = aggregator.agrupar_por_semana(df_limpio)
    resumen_semana_asesor = aggregator.agrupar_por_semana_y_asesor(df_limpio)

    try:
        generator = ReportGenerator(processor.config)
        generator.generar_excel(df_limpio, {
            "por_asesor": resumen_asesores,
            "por_semana": resumen_semanas,
            "por_semana_asesor": resumen_semana_asesor,
        })
    except Exception as e:
        print(f"ERROR al generar el reporte: {e}")
        sys.exit(1)

    print(f"Reporte generado: {processor.config['archivo_salida']}")
    print()
    print("--- Resumen por Asesor ---")
    print(resumen_asesores.to_string(index=False))
    print()
    print("--- Resumen por Semana ---")
    print(resumen_semanas.to_string(index=False))


if __name__ == "__main__":
    main()
