import socket
import threading
import time
import json

mensajes_para_guardar = []

class Nodo:
    def __init__(self):
        self.node_id = node_id
        self.capacity = capacity
        self.inventory = {}
        self.clients = {}
        self.master_alive = True
        self.master_id = None
        self.neighbors = neighbors
        self.mutex = threading.Lock()
        self.token_stack = deque()  # Pila de tokens
        self.request_queue = Queue()  # Cola de solicitudes

    def recibir_mensajes():
        mensaje_confirmado = False
        while True:
            try:
                mensaje_recibido, direccion = s.recvfrom(1024)
                mensaje_decodificado = mensaje_recibido.decode('utf-8')
                
                # Decodifica el mensaje JSON
                mensaje_json = json.loads(mensaje_decodificado)

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                mensaje_completo = f"{timestamp} - Mensaje RECIBIDO de {direccion}: {mensaje_json}"
                mensajes_para_guardar.append(mensaje_completo)

                if not mensaje_confirmado:
                    # Enviar un mensaje de confirmación al remitente
                    confirmacion = {"mensaje": "Confirmo la recepcion de tu mensaje"}
                    s.sendto(json.dumps(confirmacion).encode('utf-8'), direccion)
                    print(mensaje_completo)
                    mensaje_confirmado = True
            except socket.timeout:
                mensaje_confirmado = False


    def guardar_mensajes():
        while True:
            if mensajes_para_guardar:
                mensaje_para_guardar = mensajes_para_guardar.pop(0)
                with open("logMensajes.txt", "a") as log_file:
                    log_file.write(mensaje_para_guardar + "\n")
                time.sleep(1)  # Espera un segundo antes de intentar guardar el siguiente mensaje


    def enviar_mensajes():
        while True:
            destino_ip = input("Ingrese la dirección IP de destino: ")
            mensaje = input("Ingrese su mensaje: ")

            # Estructura el mensaje como un diccionario JSON
            mensaje_json = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "mensaje": mensaje
            }

            mensaje_completo = f"{mensaje_json['timestamp']} - Mensaje ENVIADO a {destino_ip}: {mensaje_json}"
            
            # Envía el mensaje a la dirección IP de destino especificada
            destino_puerto = 12345
            s.sendto(json.dumps(mensaje_json).encode('utf-8'), (destino_ip, destino_puerto))
            mensajes_para_guardar.append(mensaje_completo)


# Configura la dirección y el puerto en esta máquina virtual
mi_ip = "192.168.253.129"
mi_puerto = 12345 

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((mi_ip, mi_puerto))
s.settimeout(1)

# Crea hilos para recibir, enviar y guardar mensajes
thread_recibir = threading.Thread(target=recibir_mensajes)
thread_enviar = threading.Thread(target=enviar_mensajes)
thread_guardar = threading.Thread(target=guardar_mensajes)

# Que corran en segundo plano
thread_recibir.daemon = True
thread_enviar.daemon = True
thread_guardar.daemon = True

# Los inicializa
thread_recibir.start()
thread_enviar.start()
thread_guardar.start()

# El programa principal no hace nada más que esperar
while True:
    pass
