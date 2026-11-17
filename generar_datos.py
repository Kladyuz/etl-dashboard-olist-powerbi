"""Genera datasets de ventas con errores intencionales para practicar ETL.

Salida (carpeta datos/):
  - ventas.csv      transacciones 2025
  - clientes.xlsx   maestro de clientes
  - productos.json  catálogo de productos

Uso:  python generar_datos.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(139)
OUT = Path(__file__).parent / "datos"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- productos
productos = [
    (1, "Notebook 14\"", "Electrónica", 549990),
    (2, "Audífonos Bluetooth", "Electrónica", 39990),
    (3, "Smartwatch", "Electrónica", 129990),
    (4, "Monitor 24\"", "Electrónica", 159990),
    (5, "Hervidor eléctrico", "Hogar", 24990),
    (6, "Set de sartenes", "Hogar", 49990),
    (7, "Aspiradora", "Hogar", 119990),
    (8, "Lámpara de escritorio", "Hogar", 19990),
    (9, "Polerón", "Ropa", 29990),
    (10, "Zapatillas urbanas", "Ropa", 59990),
    (11, "Chaqueta impermeable", "Ropa", 79990),
    (12, "Bicicleta aro 29", "Deportes", 349990),
    (13, "Mancuernas 10 kg", "Deportes", 34990),
    (14, "Mat de yoga", "Deportes", 14990),
    (15, "Botella térmica", "Deportes", 12990),
]
prod_json = []
for pid, nombre, cat, precio in productos:
    prod_json.append({"id_producto": pid, "nombre_producto": nombre,
                      "categoria": cat, "precio_lista": precio})
# Errores: mayúsculas/espacios inconsistentes, categoría nula, duplicado
prod_json[5]["categoria"] = "hogar"
prod_json[9]["categoria"] = " ROPA "
prod_json[13]["categoria"] = None
prod_json.append(dict(prod_json[2]))  # producto 3 duplicado
(OUT / "productos.json").write_text(
    json.dumps(prod_json, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- clientes
REGIONES = ["Metropolitana", "Norte", "Centro", "Sur"]
REG_W = [0.40, 0.15, 0.20, 0.25]
CANALES = ["Online", "Tienda", "Distribuidor"]
CAN_W = [0.40, 0.40, 0.20]
NOMBRES = ["Ana", "Benjamín", "Camila", "Diego", "Elena", "Felipe", "Gabriela",
           "Hernán", "Isidora", "Javiera", "Kevin", "Lucía", "Matías", "Nicole",
           "Óscar", "Paula", "Rodrigo", "Sofía", "Tomás", "Valentina"]
APELLIDOS = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras",
             "Silva", "Martínez", "Sepúlveda", "Morales", "Rodríguez", "López",
             "Fuentes", "Hernández", "Torres", "Araya", "Flores", "Espinoza"]


def fecha_mixta(d: date) -> str:
    """Devuelve la fecha en uno de tres formatos distintos."""
    r = random.random()
    if r < 0.6:
        return d.strftime("%Y-%m-%d")
    if r < 0.85:
        return d.strftime("%d/%m/%Y")
    return d.strftime("%d-%m-%Y")


N_CLIENTES = 150
clientes = []
for cid in range(1001, 1001 + N_CLIENTES):
    reg = random.choices(REGIONES, REG_W)[0]
    can = random.choices(CANALES, CAN_W)[0]
    alta = date(2023, 1, 1) + timedelta(days=random.randint(0, 700))
    clientes.append({
        "ID Cliente": cid,
        "Nombre Cliente": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
        "Región": reg,
        "Canal Venta": can,
        "Fecha Registro": fecha_mixta(alta),
    })
cli_info = {c["ID Cliente"]: (c["Región"], c["Canal Venta"]) for c in clientes}

# Errores en clientes
idx = random.sample(range(N_CLIENTES), 40)
for i in idx[:10]:
    clientes[i]["Región"] = clientes[i]["Región"].upper()
for i in idx[10:18]:
    clientes[i]["Región"] = " " + clientes[i]["Región"].lower() + " "
for i in idx[18:24]:
    clientes[i]["Canal Venta"] = clientes[i]["Canal Venta"].lower()
for i in idx[24:29]:
    clientes[i]["Región"] = None
for i in idx[29:32]:
    clientes[i]["Nombre Cliente"] = None
for i in idx[32:35]:
    clientes.append(dict(clientes[i]))  # filas duplicadas
random.shuffle(clientes)
pd.DataFrame(clientes).to_excel(OUT / "clientes.xlsx", index=False,
                                sheet_name="Clientes")

# ---------------------------------------------------------------- ventas
# Patrones para que el análisis tenga hallazgos:
#  - Estacionalidad: peak nov-dic (Cyber/Navidad), caída en julio
#  - Online crece durante el año; Tienda estable; Distribuidor baja
#  - Metropolitana domina en monto; Sur con ticket alto (bicicletas)
MES_W = {1: 0.9, 2: 0.8, 3: 1.0, 4: 1.0, 5: 1.1, 6: 1.0,
         7: 0.6, 8: 0.9, 9: 1.1, 10: 1.1, 11: 1.6, 12: 1.9}
CAT_REG = {"Sur": {"Deportes": 2.5}, "Norte": {"Electrónica": 1.6}}

prod_by_id = {p[0]: p for p in productos}
ids_cli = list(cli_info)
dias = [date(2025, 1, 1) + timedelta(days=i) for i in range(365)]

ventas = []
vid = 50001
N_OBJ = 1800
peso_dia = [MES_W[d.month] for d in dias]
for _ in range(N_OBJ):
    d = random.choices(dias, peso_dia)[0]
    cid = random.choice(ids_cli)
    reg, can = cli_info[cid]
    # tendencia por canal según el mes
    t = (d.month - 1) / 11
    keep = {"Online": 0.45 + 0.55 * t, "Tienda": 0.8,
            "Distribuidor": 0.9 - 0.4 * t}[can]
    if random.random() > keep:
        continue
    pesos = [CAT_REG.get(reg, {}).get(p[2], 1.0) for p in productos]
    pid, _, cat, precio = random.choices(productos, pesos)[0]
    cant = random.choices([1, 2, 3, 4, 5], [0.55, 0.25, 0.1, 0.06, 0.04])[0]
    if can == "Distribuidor":
        cant += random.randint(2, 8)
    descuento = random.choice([1, 1, 1, 0.95, 0.9])
    if d.month == 11 and 3 <= d.day <= 6:  # Cyber
        descuento = 0.8
    ventas.append({
        "id_venta": vid,
        "fecha": fecha_mixta(d),
        "cliente_id": cid,
        "prod_id": pid,
        "cant": cant,
        "precio_unit": round(precio * descuento),
    })
    vid += 1

# Errores en ventas
n = len(ventas)
sel = random.sample(range(n), 75)
for i in sel[:15]:
    ventas[i]["cliente_id"] = None                      # nulo en clave
for i in sel[15:25]:
    ventas[i]["cant"] = None                            # cantidad nula
for i in sel[25:30]:
    ventas[i]["cant"] = "N/A"                            # texto en numérico
for i in sel[30:38]:
    ventas[i]["precio_unit"] = -ventas[i]["precio_unit"]  # precio negativo
for i in sel[38:43]:
    ventas[i]["precio_unit"] = 0                         # precio cero
for i in sel[43:50]:
    ventas[i]["cliente_id"] = random.randint(2001, 2010)  # cliente inexistente
for i in sel[50:55]:
    ventas[i]["fecha"] = None                           # fecha nula
dups = [dict(ventas[i]) for i in sel[55:75]]            # 20 duplicados
ventas.extend(dups)
random.shuffle(ventas)

df = pd.DataFrame(ventas)
df["cliente_id"] = df["cliente_id"].astype("Int64")
df.to_csv(OUT / "ventas.csv", index=False, encoding="utf-8-sig")

print(f"productos.json: {len(prod_json)} filas")
print(f"clientes.xlsx : {len(clientes)} filas")
print(f"ventas.csv    : {len(ventas)} filas")
