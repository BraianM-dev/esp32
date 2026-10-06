# Tabla de consumo simulada (No necesita placa).
# Útil para practicar variables, bucles y condicionales antes de añadir sensores.
watts = (3, 5, 7, 9)
horas_por_dia = 4
for potencia in watts:
    energia_kwh = potencia * horas_por_dia * 30 / 1000
    print(potencia, "W ->", energia_kwh, "kWh/mes")
