# Registro de limpieza — Olist

| Tabla | Paso | Filas antes | Filas después | Eliminadas |
|---|---|---:|---:|---:|
| pedidos | Quitar duplicados por order_id | 99,441 | 99,441 | 0 |
| pedidos | Quitar fecha de compra o cliente nulos | 99,441 | 99,441 | 0 |
| pedidos | Conservar solo pedidos entregados (delivered) | 99,441 | 96,478 | 2,963 |
| pedidos | Filtrar período ene-2017 a ago-2018 | 96,478 | 96,211 | 267 |
| clientes | Quitar duplicados por customer_id | 99,441 | 99,441 | 0 |
| pagos | Quitar duplicados por pedido + secuencia | 103,886 | 103,886 | 0 |
| pagos | Quitar medio de pago 'not_defined' | 103,886 | 103,883 | 3 |
| pagos | Quitar montos <= 0 | 103,883 | 103,877 | 6 |
| combinado | Pedidos + clientes (inner por customer_id) | 96,211 | 96,211 | 0 |
| combinado | + pagos (inner por order_id); pedidos sin pago válido eliminados | 96,211 | 96,211 | 0 |

Otras transformaciones (no eliminan filas):
- Fecha de compra: texto con hora -> fecha; columnas Año, Mes y Año-Mes.
- Ciudad en formato Título; Estado en mayúsculas sin espacios.
- Nueva columna Región (5 regiones de Brasil) a partir del Estado.
- Medio de pago traducido al español.
- Columnas renombradas al español; columnas de logística descartadas.
- Cliente identificado con customer_unique_id (customer_id cambia en cada pedido).

Resultado final:
- 100,469 filas de pago, 96,211 pedidos, 93,104 clientes únicos.
- Ventas totales: R$ 15,375,875.44.