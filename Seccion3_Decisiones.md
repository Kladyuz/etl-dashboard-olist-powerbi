Se integraron tres fuentes públicas de Olist en formato CSV (pedidos, clientes y pagos) usando pandas. Los pedidos se combinaron con clientes por customer_id y luego con pagos por order_id, conservando solo coincidencias.

Se eliminaron 2.963 pedidos no entregados (cancelados, no disponibles o en tránsito), porque no representan ventas concretadas, y 267 pedidos fuera del período enero 2017 – agosto 2018, ya que 2016 y septiembre–octubre de 2018 tienen meses incompletos que distorsionarían la tendencia. En pagos se descartaron 3 registros con medio "not_defined" y 6 con monto menor o igual a cero, por ser errores de registro. Las columnas de logística, que concentraban los valores nulos, se excluyeron porque no se usan en el análisis.

Para normalizar, la fecha de compra pasó de texto con hora a tipo fecha y se derivaron año y mes; las ciudades quedaron en formato Título, los estados en mayúsculas y los medios de pago traducidos al español. Se creó la columna Región agrupando los 27 estados en las cinco regiones de Brasil.

Supuestos: se revisaron duplicados (no hubo) y los clientes se identificaron con customer_unique_id, porque customer_id cambia en cada pedido. Resultado: 100.469 pagos, 96.211 pedidos y 93.104 clientes.
