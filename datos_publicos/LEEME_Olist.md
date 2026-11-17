# Datos públicos: Brazilian E-Commerce Public Dataset by Olist

**Fuente original:** Olist, Kaggle — https://www.kaggle.com/olistbr/brazilian-ecommerce (licencia CC BY-NC-SA 4.0, uso académico permitido citando la fuente)
**Copia descargada desde:** https://github.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist (mismos archivos, sin login)
**Descarga:** 15-11-2026

Cita sugerida para el informe:
> Olist (2018). *Brazilian E-Commerce Public Dataset by Olist*. Kaggle. https://www.kaggle.com/olistbr/brazilian-ecommerce

## Archivos

| Archivo | Filas | Clave | Columnas útiles |
|---|---|---|---|
| `olist_orders_dataset.csv` | 99.441 | `order_id` | `customer_id`, `order_status`, `order_purchase_timestamp`, fechas de entrega |
| `olist_customers_dataset.csv` | 99.441 | `customer_id` | `customer_unique_id`, `customer_city`, `customer_state` |
| `olist_order_payments_dataset.csv` | 103.886 | `order_id` (+ `payment_sequential`) | `payment_type`, `payment_installments`, `payment_value` |

Relaciones: orders.`customer_id` → customers.`customer_id` · orders.`order_id` → payments.`order_id` (un pedido puede tener varios pagos).

## Problemas reales encontrados (perfilado)

| Problema | Cantidad | Tratamiento sugerido en Power Query |
|---|---|---|
| Meses incompletos: 2016 (329 pedidos, con huecos) y sep–oct 2018 (20) | 349 | Filtrar período **ene-2017 a ago-2018** (supuesto: meses incompletos distorsionan la tendencia) |
| Pedidos no entregados (cancelados, unavailable, shipped, etc.) | 2.963 | Conservar solo `order_status = delivered` (supuesto: solo cuentan ventas concretadas) |
| Fechas nulas: aprobación 160, despacho 1.783, entrega 2.965 | — | No se usan para KPIs; quedan resueltas al filtrar `delivered` o se eliminan esas columnas |
| `payment_type = not_defined` | 3 | Eliminar |
| `payment_value <= 0` | 9 | Eliminar |
| Pedido sin registro de pago | 1 | Se elimina con combinación interna |
| Pedidos con varios pagos | 4.446 | Contar pedidos con `DISTINCTCOUNT(order_id)`, no con conteo de filas |
| Nombres en inglés y snake_case | — | Renombrar: `payment_value` → `Monto Pago`, etc. |
| Medio de pago en inglés (`credit_card`, `boleto`) | — | Reemplazar valores: Tarjeta de crédito, Boleto, Voucher, Tarjeta de débito |
| Ciudades en minúsculas sin tildes (`sao paulo`) | — | **Normalización:** Poner en mayúsculas cada palabra |
| Fecha con hora (`2017-10-02 10:56:33`) | — | **Normalización:** cambiar a tipo Fecha y crear columna Año-Mes |
| Sin columna de región (solo 27 estados) | — | Columna condicional Estado → Región (tabla abajo) |

## Estado → Región de Brasil

| Región | Estados |
|---|---|
| Norte | AC, AP, AM, PA, RO, RR, TO |
| Nordeste | AL, BA, CE, MA, PB, PE, PI, RN, SE |
| Centro-Oeste | DF, GO, MT, MS |
| Sudeste | ES, MG, RJ, SP |
| Sul | PR, RS, SC |

## Mapeo a los requisitos del dashboard

- **KPI 1:** Ventas totales = `SUM(Monto Pago)` (≈ R$ 15,4 millones tras limpiar)
- **KPI 2:** Clientes únicos = `DISTINCTCOUNT(customer_unique_id)` (≈ 93 mil). Usar `customer_unique_id`, no `customer_id`, porque Olist genera un `customer_id` nuevo en cada pedido.
- **Comparativo (barras):** ventas por región/estado o por medio de pago ("canal")
- **Tendencia (línea):** ventas por mes, ene-2017 → ago-2018
- **Filtro:** región, estado o medio de pago

## Primeros hallazgos (para orientar el análisis; verificar en el dashboard)

- Fuerte crecimiento 2017 → 2018 y peak en **noviembre 2017** (Black Friday: 7.544 pedidos, casi el doble que octubre).
- **SP** concentra cerca del 42 % de los clientes; el Sudeste domina.
- Tarjeta de crédito ≈ 78 % del monto; boleto ≈ 18 %.
