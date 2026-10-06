# EspWebStudio: interactivo
# Dungeon Master de Calabozos y Código (No necesita placa).
# Aventura educativa: nombre, clase, dado d20, decisiones y puntos.
# Usa solo consola Python: funciona en el navegador o con MicroPython.
import random

DM_NAME = "Pip"
MAX_TURNS = 3

print("=== Calabozos y Código: aventura de consola ===")
print(DM_NAME + ": ¡Bienvenido al castillo! Escribe 'salir' durante una decisión para terminar.")
nombre = input("Nombre del jugador: ").strip()
if not nombre:
    nombre = "Viajero"

# Cada clase tiene una especialidad que influye en la puntuación.
print("Elige tu clase: 1 Mago, 2 Guerrero, 3 Arquero")
while True:
    clase = input("Clase (1/2/3): ").strip()
    if clase in ("1", "2", "3"):
        break
    print("Elige 1, 2 o 3.")

clases = {"1": "Mago", "2": "Guerrero", "3": "Arquero"}
clase_nombre = clases[clase]
vida = 10
puntos = 0
print(DM_NAME + ": " + nombre + " el " + clase_nombre + ", tu aventura comienza con 10 de vida.")

for turno in range(1, MAX_TURNS + 1):
    if vida <= 0:
        break

    # getrandbits está disponible en firmwares que no incluyen randint().
    dado = random.getrandbits(5)
    while dado >= 20:
        dado = random.getrandbits(5)
    dado += 1  # Resultado uniforme entre 1 y 20.
    print("\nSala", turno, "de", MAX_TURNS, "— dado d20:", dado)

    # El resultado del dado determina las acciones disponibles.
    if dado >= 15:
        print("¡Ventaja! 1 Investigar runas | 2 Atacar al guardián | 3 Descansar")
    elif dado >= 8:
        print("Situación incierta: 1 Abrir cofre | 2 Negociar | 3 Defenderse")
    else:
        print("¡Peligro! 1 Esquivar | 2 Lanzar distracción | 3 Retroceder")

    while True:
        opcion = input("Acción (1/2/3 o salir): ").strip().lower()
        if opcion in ("1", "2", "3", "salir"):
            break
        print("Escribe 1, 2, 3 o salir.")
    if opcion == "salir":
        print(DM_NAME + ": guardamos la historia para otra ocasión.")
        break

    if dado >= 15:
        if opcion == "1":
            ganancia = 4 if clase == "1" else 2
            puntos += ganancia
            print("Descifras las runas. +", ganancia, "puntos")
        elif opcion == "2":
            ganancia = 4 if clase == "2" else 2
            puntos += ganancia
            print("Vences al guardián. +", ganancia, "puntos")
        else:
            vida = min(10, vida + 2)
            print("Descansas y recuperas vida.")
    elif dado >= 8:
        if opcion == "1":
            puntos += 2
            print("El cofre contiene una pista. +2 puntos")
        elif opcion == "2":
            ganancia = 3 if clase == "3" else 1
            puntos += ganancia
            print("Encuentras un camino seguro. +", ganancia, "puntos")
        else:
            vida = min(10, vida + 1)
            print("Te proteges. +1 de vida")
    else:
        if opcion == "1":
            vida -= 1
            puntos += 1
            print("Esquivas por poco. -1 de vida, +1 punto")
        elif opcion == "2":
            ganancia = 2 if clase == "1" else 1
            puntos += ganancia
            vida -= 2
            print("La distracción funciona. +", ganancia, "puntos, -2 de vida")
        else:
            vida -= 1
            print("Retrocedes con cuidado. -1 de vida")
    print("Estado:", vida, "de vida |", puntos, "puntos")

if vida <= 0:
    print(DM_NAME + ": has caído, pero podrás intentar otra aventura.")
else:
    print(DM_NAME + ": fin de la aventura para", nombre + ".")
print("Clase:", clase_nombre, "| Vida:", vida, "| Puntos:", puntos)
