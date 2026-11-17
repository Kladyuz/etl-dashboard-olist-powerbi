# %% [markdown]
# # Limpieza y transformación — Olist (ESP139)
# Combina pedidos + clientes + pagos en un solo dataset limpio para Power BI.
#
# Ejecutar completo:  python limpieza_olist.py
# O celda por celda en VS Code / Jupyter (cada "# %%" es una celda) — útil
# para tomar capturas de cada transformación.
#
# Salidas (carpeta datos_limpios/):
#   - olist_ventas_limpio.xlsx   dataset final (recomendado para Power BI)
#   - olist_ventas_limpio.csv    mismo dataset en CSV (separador ; y coma decimal)
#   - registro_limpieza.md       tabla con cada paso y filas antes/después

# %% 0. Configuración
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
ENTRADA = BASE / "datos_publicos"
SALIDA = BASE / "datos_limpios"
SALIDA.mkdir(exist_ok=True)

FECHA_INICIO = "2017-01-01"   # supuesto: 2016 tiene meses con muy pocos pedidos
FECHA_FIN = "2018-09-01"      # supuesto: sep-oct 2018 están incompletos (exclusivo)

registro = []  # (tabla, paso, filas_antes, filas_despues)


def anotar(tabla, paso, antes, despues):
    registro.append((tabla, paso, antes, despues))
    print(f"[{tabla}] {paso}: {antes:,} -> {despues:,} filas ({antes - despues:,} eliminadas)")


# %% 1. Extracción
pedidos = pd.read_csv(ENTRADA / "olist_orders_dataset.csv")
clientes = pd.read_csv(ENTRADA / "olist_customers_dataset.csv",
                       dtype={"customer_zip_code_prefix": str})
pagos = pd.read_csv(ENTRADA / "olist_order_payments_dataset.csv")

for nombre, df in [("pedidos", pedidos), ("clientes", clientes), ("pagos", pagos)]:
    print(f"{nombre}: {df.shape[0]:,} filas x {df.shape[1]} columnas")
    print("  nulos:", {k: int(v) for k, v in df.isna().sum().items() if v} or "ninguno")

# %% 2. Pedidos
n = len(pedidos)
pedidos = pedidos.drop_duplicates(subset="order_id")
anotar("pedidos", "Quitar duplicados por order_id", n, len(pedidos))

# Normalización de fecha: texto con hora -> tipo fecha
pedidos["order_purchase_timestamp"] = pd.to_datetime(
    pedidos["order_purchase_timestamp"], errors="coerce")
n = len(pedidos)
pedidos = pedidos.dropna(subset=["order_purchase_timestamp", "customer_id"])
anotar("pedidos", "Quitar fecha de compra o cliente nulos", n, len(pedidos))

n = len(pedidos)
pedidos = pedidos[pedidos["order_status"] == "delivered"]
anotar("pedidos", "Conservar solo pedidos entregados (delivered)", n, len(pedidos))

n = len(pedidos)
pedidos = pedidos[(pedidos["order_purchase_timestamp"] >= FECHA_INICIO)
                  & (pedidos["order_purchase_timestamp"] < FECHA_FIN)]
anotar("pedidos", "Filtrar período ene-2017 a ago-2018", n, len(pedidos))

# Columnas de logística no se usan en el dashboard (y concentran los nulos)
pedidos = pedidos[["order_id", "customer_id", "order_purchase_timestamp"]]

# %% 3. Clientes
n = len(clientes)
clientes = clientes.drop_duplicates(subset="customer_id")
anotar("clientes", "Quitar duplicados por customer_id", n, len(clientes))

# Normalización de texto
clientes["customer_city"] = clientes["customer_city"].str.strip().str.title()
clientes["customer_state"] = clientes["customer_state"].str.strip().str.upper()

REGIONES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
estado_a_region = {uf: reg for reg, ufs in REGIONES.items() for uf in ufs}
clientes["region"] = clientes["customer_state"].map(estado_a_region)
sin_region = clientes["region"].isna().sum()
print(f"Estados sin región asignada: {sin_region}")
clientes["region"] = clientes["region"].fillna("Sin región")

# %% 4. Pagos
n = len(pagos)
pagos = pagos.drop_duplicates(subset=["order_id", "payment_sequential"])
anotar("pagos", "Quitar duplicados por pedido + secuencia", n, len(pagos))

n = len(pagos)
pagos = pagos[pagos["payment_type"] != "not_defined"]
anotar("pagos", "Quitar medio de pago 'not_defined'", n, len(pagos))

n = len(pagos)
pagos = pagos[pagos["payment_value"] > 0]
anotar("pagos", "Quitar montos <= 0", n, len(pagos))

MEDIOS = {
    "credit_card": "Tarjeta de crédito",
    "boleto": "Boleto",
    "voucher": "Voucher",
    "debit_card": "Tarjeta de débito",
}
pagos["payment_type"] = pagos["payment_type"].map(MEDIOS)

# %% 5. Combinación (merge) de las 3 fuentes
n = len(pedidos)
ventas = pedidos.merge(clientes, on="customer_id", how="inner")
anotar("combinado", "Pedidos + clientes (inner por customer_id)", n, len(ventas))

n = len(ventas)
ventas = ventas.merge(pagos, on="order_id", how="inner")
# Un pedido puede tener varios pagos: el número de filas puede subir
print(f"[combinado] + pagos (inner por order_id): {n:,} pedidos -> {len(ventas):,} filas de pago")
pedidos_sin_pago = n - ventas["order_id"].nunique()
registro.append(("combinado", "+ pagos (inner por order_id); pedidos sin pago válido eliminados",
                 n, ventas["order_id"].nunique()))

# %% 6. Columnas derivadas, renombre y orden final
ventas["fecha_compra"] = ventas["order_purchase_timestamp"].dt.normalize()
ventas["anio"] = ventas["fecha_compra"].dt.year
ventas["mes"] = ventas["fecha_compra"].dt.month
ventas["anio_mes"] = ventas["fecha_compra"].dt.strftime("%Y-%m")

ventas = ventas.rename(columns={
    "order_id": "ID Pedido",
    "customer_unique_id": "ID Cliente",
    "fecha_compra": "Fecha Compra",
    "anio": "Año",
    "mes": "Mes",
    "anio_mes": "Año-Mes",
    "region": "Región",
    "customer_state": "Estado",
    "customer_city": "Ciudad",
    "payment_type": "Medio de Pago",
    "payment_installments": "Cuotas",
    "payment_value": "Monto Pago",
})
COLUMNAS = ["ID Pedido", "ID Cliente", "Fecha Compra", "Año", "Mes", "Año-Mes",
            "Región", "Estado", "Ciudad", "Medio de Pago", "Cuotas", "Monto Pago"]
ventas = ventas[COLUMNAS].sort_values(["Fecha Compra", "ID Pedido"]).reset_index(drop=True)

# %% 7. Validaciones
assert ventas.isna().sum().sum() == 0, "Quedaron nulos"
assert (ventas["Monto Pago"] > 0).all()
assert ventas["Región"].ne("Sin región").all()

print("\n--- Dataset final ---")
print(f"Filas (pagos):        {len(ventas):,}")
print(f"Pedidos únicos:       {ventas['ID Pedido'].nunique():,}")
print(f"Clientes únicos:      {ventas['ID Cliente'].nunique():,}")
print(f"Ventas totales (R$):  {ventas['Monto Pago'].sum():,.2f}")
print(f"Período:              {ventas['Fecha Compra'].min():%d-%m-%Y} a {ventas['Fecha Compra'].max():%d-%m-%Y}")
print(ventas.head())

# %% 8. Exportación
ventas.to_excel(SALIDA / "olist_ventas_limpio.xlsx", index=False, sheet_name="Ventas")
ventas.to_csv(SALIDA / "olist_ventas_limpio.csv", index=False, sep=";", decimal=",",
              encoding="utf-8-sig", date_format="%Y-%m-%d")

lineas = ["# Registro de limpieza — Olist", "",
          "| Tabla | Paso | Filas antes | Filas después | Eliminadas |",
          "|---|---|---:|---:|---:|"]
for tabla, paso, a, d in registro:
    lineas.append(f"| {tabla} | {paso} | {a:,} | {d:,} | {a - d:,} |")
lineas += ["", "Otras transformaciones (no eliminan filas):",
           "- Fecha de compra: texto con hora -> fecha; columnas Año, Mes y Año-Mes.",
           "- Ciudad en formato Título; Estado en mayúsculas sin espacios.",
           "- Nueva columna Región (5 regiones de Brasil) a partir del Estado.",
           "- Medio de pago traducido al español.",
           "- Columnas renombradas al español; columnas de logística descartadas.",
           "- Cliente identificado con customer_unique_id (customer_id cambia en cada pedido).",
           "", "Resultado final:",
           f"- {len(ventas):,} filas de pago, {ventas['ID Pedido'].nunique():,} pedidos, "
           f"{ventas['ID Cliente'].nunique():,} clientes únicos.",
           f"- Ventas totales: R$ {ventas['Monto Pago'].sum():,.2f}."]
(SALIDA / "registro_limpieza.md").write_text("\n".join(lineas), encoding="utf-8")
print(f"\nArchivos guardados en {SALIDA}")
