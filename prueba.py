import socket
import threading
import time
import json
from collections import deque
from queue import Queue

class Node:
    def __init__(self, node_id, capacity, neighbors):
        self.node_id = node_id
        self.capacity = capacity
        self.inventory = {}
        self.clients = {}
        self.master_alive = True
        self.master_id = None
        self.neighbors = neighbors
        self.mutex = False #threading.Lock()
        self.token_stack = deque()  # Pila de tokens
        self.request_queue = Queue()  # Cola de solicitudes

    def start(self, host, port):
        self.host = host
        self.port = port

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        self.client_thread = threading.Thread(target=self.start_client)
        self.client_thread.start()

        self.check_master_thread = threading.Thread(target=self.check_master_alive)
        self.check_master_thread.start()

        self.token_thread = threading.Thread(target=self.token_handler)
        self.token_thread.start()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.bind((self.host, self.port))

            while True:
                mensaje_recibido, direccion = server_socket.recvfrom(1024)
                mensaje_decodificado = mensaje_recibido.decode('utf-8')
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                mensaje_completo = f"{timestamp} - Mensaje RECIBIDO de {direccion}: {mensaje_decodificado}"
                print(mensaje_completo)

                # Procesar el mensaje según la acción
                message = json.loads(mensaje_decodificado)
                action = message.get('action')
                if action == 'request_access':
                    self.handle_request_access(message)
                elif action == 'update_inventory':
                    self.handle_update_inventory(message)
                elif action == 'get_inventory':
                    self.handle_get_inventory(direccion)
                elif action == 'buy_item':
                    self.handle_buy_item(message)

    def start_client(self):
        while True:
            time.sleep(5)
            if self.master_alive and self.master_id is not None:
                neighbor_id = self.neighbors[self.master_id]
                neighbor_address = self.get_node_address(neighbor_id)

                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                    try:
                        client_socket.sendto(b'heartbeat', neighbor_address)
                    except:
                        self.master_alive = False

    def check_master_alive(self):
        while True:
            time.sleep(10)
            if not self.master_alive:
                self.elect_master()

    def elect_master(self):
        # Implementar lógica de elección de nuevo nodo maestro
        pass

    def handle_request_access(self, message):
        with self.mutex:
            action = message.get('action')
            if action == 'request_access':
                if not self.token_stack:
                    # No hay tokens disponibles, encolar solicitud
                    self.request_queue.put(message['node_id'])
                else:
                    # Hay un token disponible, enviarlo al nodo que solicitó acceso
                    token = self.token_stack.pop()
                    response = {'action': 'grant_access', 'token': token}
                    self.send_message(message['node_id'], response)

    def handle_update_inventory(self, message):
        with self.mutex:
            # Implementar lógica de consenso para actualizar el inventario
            # Aquí se debe considerar la distribución equitativa y la verificación del espacio en cada sucursal
            pass

    def handle_get_inventory(self, client_address):
        with self.mutex:
            # Enviar el inventario al nodo cliente
            response = {'action': 'send_inventory', 'inventory': self.inventory}
            response_json = json.dumps(response).encode('utf-8')
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as response_socket:
                response_socket.sendto(response_json, client_address)

    def handle_buy_item(self, message):
        with self.mutex:
            # Implementar lógica de exclusión mutua para la compra de un artículo
            pass

    def send_token(self, recipient_id, token):
        recipient_address = self.get_node_address(recipient_id)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            message = {'action': 'token', 'token': token}
            message_json = json.dumps(message).encode('utf-8')
            client_socket.sendto(message_json, recipient_address)

    def token_handler(self):
        while True:
            time.sleep(1)

            with self.mutex:
                if not self.token_stack and not self.request_queue.empty():
                    # Si no hay tokens disponibles y hay solicitudes en la cola, generar un nuevo token
                    new_token = f'Token-{time.time()}'
                    self.token_stack.append(new_token)

                    # Desencolar la solicitud y enviar el token al nodo que solicitó acceso
                    node_id = self.request_queue.get()
                    self.send_token(node_id, new_token)

    def get_node_address(self, node_id):
        neighbor_port = 5000 + node_id  # Asumiendo que los nodos están en puertos consecutivos
        return ('192.168.1.104', neighbor_port)

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

# Definir la malla cerrada de nodos (cada nodo tiene un vecino a la izquierda y uno a la derecha)
neighbors = {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}

# Crear instancias de nodos
node1 = Node(node_id=1, capacity=100, neighbors=neighbors)
node2 = Node(node_id=2, capacity=150, neighbors=neighbors)
node3 = Node(node_id=3, capacity=120, neighbors=neighbors)
node4 = Node(node_id=4, capacity=80, neighbors=neighbors)
node5 = Node(node_id=5, capacity=200, neighbors=neighbors)

# Iniciar nodos
node1.start(host='192.168.253.104', port=5001)
node2.start(host='192.168.1.104', port=5002)
node3.start(host='192.168.1.104', port=5003)
node4.start(host='192.168.1.104', port=5004)
node5.start(host='192.168.1.104', port=5005)

# Esperar a que los hilos finalicen
node1.server_thread.join()
node1.client_thread.join()
node1.check_master_thread.join()
node1.token_thread.join()