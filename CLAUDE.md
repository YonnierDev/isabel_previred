# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ejecutar

```bash
python main.py
```

Debe ejecutarse desde `c:\automatizaciones\informes\isabel\` con el archivo Excel en `data/entrada/`. El script detecta automáticamente el primer `.xls` o `.xlsx` que encuentre en esa carpeta.

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configuración mensual

Todo lo que cambia mes a mes está en `config.json`:
- `mes` — etiqueta del mes (aparece en la salida)
- `asesores` — mapeo `"código"` → nombre; los códigos vienen de la columna **Fuente** del Excel
- `semanas` — 4 rangos de fechas (`fecha_inicio` / `fecha_fin` en formato `YYYY-MM-DD`)
- `archivo_salida` — ruta del `.xlsx` generado (la extensión se fuerza a `.xlsx` aunque se escriba `.xls`)

## Arquitectura

El flujo es lineal: `main.py` instancia las tres clases en orden y pasa datos entre ellas.

```
CallCenterProcessor.procesar()
    → WeeklyAggregator.agrupar_por_semana_y_asesor()
    → ReportGenerator.generar_excel()
```

### `modules/data_processor.py` — `CallCenterProcessor`
Responsable de leer y filtrar. Pasos internos en `_limpiar_datos`:
1. Descarta filas donde **Destino** sea `"1"` o `"s"`
2. Normaliza la columna **Fuente** a string entero (`"1304.0"` → `"1304"`) y descarta códigos no presentes en `asesores`
3. Convierte **Duración** a segundos — formato real del sistema: `"252s (4m 12s)"` (se extrae el número inicial)
4. Filtra `Duración_Segundos >= duracion_minima_segundos` (default 30)
5. Convierte **Fecha** a datetime

El DataFrame devuelto por `procesar()` ya solo contiene filas que pasaron todos los filtros.

### `modules/week_calculator.py` — `WeeklyAggregator`
Recibe el DataFrame filtrado y agrupa por semana. Las etiquetas de semana se generan como `SEM1`…`SEM4` a partir de las claves `semana_1`…`semana_4` del config. Las fechas del rango se muestran como `"01/04 - 11/04"`. Registros cuya fecha cae fuera de todos los rangos se descartan con log.

### `modules/report_builder.py` — `ReportGenerator`
Escribe el Excel de salida con `openpyxl`. Actualmente genera una sola hoja **"Informe"** con columnas `Semana | Fechas | Asesor | >= 30 Seg`. Los métodos `_hoja_*` adicionales están presentes pero no se llaman — son candidatos si se necesitan hojas extra.

## Columnas del Excel de entrada

| Columna | Uso |
|---------|-----|
| Fecha | Asignación de semana |
| Fuente | Código del asesor (columna B) |
| Destino | Filtro de exclusión (`"1"` y `"s"`) |
| Duración | Formato `Xs` o `Xs (Xm Ys)` |

El resto de columnas (Estado, UniqueID, Recording, etc.) se ignoran.

## Notas de operación

- Si el Excel de salida está abierto en Excel al ejecutar el script, aparecerá `Permission denied` — hay que cerrarlo primero.
- Solo debe haber un archivo Excel en `data/entrada/` a la vez; si hay más de uno se toma el primero que devuelve `os.listdir`.
