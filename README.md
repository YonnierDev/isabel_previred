# Procesador Call Center — Flashfactu

Automatiza el análisis mensual de llamadas exportadas desde el sistema de telecomunicaciones.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

1. Copiar el archivo `.xls` exportado del sistema en `data/entrada/`
2. Editar `config.json` con el nombre del archivo, mes y rangos de semanas
3. Ejecutar:

```bash
python main.py
```

4. El reporte aparece en `data/salida/informe_procesado.xlsx`

## config.json

| Campo | Descripción |
|---|---|
| `archivo_entrada` | Ruta al `.xls` de origen |
| `archivo_salida` | Ruta del `.xlsx` generado |
| `duracion_minima_segundos` | Umbral para "llamada efectiva" (default: 30) |
| `mes` | Etiqueta del mes (aparece en encabezados del Excel) |
| `asesores` | Mapeo `"extensión"` → nombre legible |
| `semanas` | 4 rangos de fechas con `fecha_inicio` y `fecha_fin` |

### Cambiar de mes

Editar en `config.json`:
- `mes`: el nuevo mes
- `semanas`: los 4 rangos de fechas del mes
- `asesores`: agregar o quitar extensiones si hubo cambios de personal

### Agregar un asesor nuevo

```json
"asesores": {
  "1304.0": "AGENTE4",
  "1403.0": "ASESOR MERCADEO",
  "1505.0": "NUEVO ASESOR"
}
```

## Columnas esperadas en el Excel de entrada

| Columna | Descripción |
|---|---|
| Estado | `ANSWERED` para llamadas contestadas |
| Duración | Formato `9s`, `1m30s`, `2m` |
| Extensión / Agente | Código numérico del asesor |
| Fecha | Fecha y hora de la llamada |

## Hojas del Excel generado

| Hoja | Contenido |
|---|---|
| Resumen Asesores | Totales por asesor |
| Resumen Semanas | Totales por semana |
| Detalles por Semana | Cruce semana × asesor |
| Datos Crudos | Todos los registros contestados |
| Totales | KPIs ejecutivos |
