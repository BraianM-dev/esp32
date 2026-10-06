# EspWebStudio: interactivo
# Mi primer ChatBot (No necesita placa).
# Practica input(), while, if/elif/else y búsqueda de palabras.
# La respuesta del clima es ficticia: este ejemplo no consulta Internet.
BOT_NAME = "ChatBot 9000"
EXIT_WORD = "chau"

print("Hola, soy un chatbot. ¿En qué puedo ayudarte hoy?")
print("Escribe '" + EXIT_WORD + "' para salir.\n")

# El chat continúa hasta recibir la palabra de salida.
while True:
    mensaje = input("Tú: ").strip().lower()

    if mensaje == EXIT_WORD:
        print("Chatbot: Adiós, que tengas un buen día.")
        break
    elif "tiempo" in mensaje or "clima" in mensaje:
        print("Chatbot: Como ejemplo, hoy está soleado y cálido (no es un pronóstico real).")
    elif "nombre" in mensaje:
        print("Chatbot: Mi nombre es " + BOT_NAME + ".")
    elif "saludo" in mensaje or "hola" in mensaje:
        print("Chatbot: ¡Hola! ¿Cómo estás?")
    elif "edad" in mensaje:
        print("Chatbot: Soy un programa, así que no tengo edad.")
    else:
        print("Chatbot: No entiendo. ¿Puedes reformular tu pregunta?")
