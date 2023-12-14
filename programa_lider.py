import socket
import threading
import time
import json
import random
from collections import deque
from queue import Queue

HEARTBEAT_INTERVAL = 2
MAX_INACTIVE_TIME = 5
# Clase Nodo deberia tener la capacidad de responder y hacer todo si fuera "maestro"
# De no ser asi, envia peticiones al nodo maestro, cada nodo sabe quien es el nodo maestro 
# Cada nodo tiene exclusivamente un nodo vecino
# Cada nodo tiene un "acess" que se lo otorga el nodo "maestro", sin el, se encolan en una cola de solicitudes
# Este "Acess" se ocupa para asegurarse que no puedan hacerse cambios al mismo tiempo
# Todas las solicitudes las "coordina" el nodo maestro y les da el permiso para poder 
#       realizar cualquier cosa que podria entrar en una exclusion mutua

class Node:
    #Listado de los nodos. Todos saben de todos. Se hace la busqueda por IP
    lista_ip_nodo = {"192.168.253.129":1,"192.168.253.130":2,"192.168.253.132":3,"192.168.253.133":4,"192.168.253.134":5}
    lista_nodo_ip = {1:"192.168.253.129",2:"192.168.253.130",3:"192.168.253.132",4:"192.168.253.133",5:"192.168.253.134"}

    def __init__(self, node_id, capacity):
        self.last_heartbeat = {}  # Inicializar el registro de heartbeats
        self.master_lock = threading.Lock()  # Inicializar el lock
        self.master_node = None  # Inicializar el nodo maestro
        self.token_stack = deque()  # Inicializar la pila de tokens
        self.node_id = node_id
        self.capacity = capacity
        self.inventory = {}
        self.clients = {}
        self.master_alive = True
        self.master_id = None
        self.neighbors = None   #Exclusivamente para consenso y decisiones (Mensajeria entre nodos)
        self.access = False
        self.failed_nodes = set()
        self.request_queue = Queue()  # Cola de solicitudes

    def make_master(self, node_id):
        self.master_id = node_id

    def start(self, host):
        self.host = host
        self.port = 5000

        send_thread = threading.Thread(target=self.send_heartbeats)
        receive_thread = threading.Thread(target=self.receive_heartbeats_modified)

        send_thread.start()
        receive_thread.start()

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.start()

        self.client_thread = threading.Thread(target=self.start_client)
        self.client_thread.start()

        self.check_master_thread = threading.Thread(target=self.check_master_alive)
        self.check_master_thread.start()

        self.token_thread = threading.Thread(target=self.token_handler)
        self.token_thread.start()

        self.send_thread = threading.Thread(target=self.send_heartbeats)
        self.send_thread.start()

        self.receive_thread = threading.Thread(target=self.receive_heartbeats_modified)
        self.receive_thread.start()

    

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.bind((self.host, self.port))

            while True:
                mensaje_recibido, direccion = server_socket.recvfrom(1024)
                mensaje_decodificado = mensaje_recibido.decode('utf-8')

                # Add timestamp, node, and action to the message
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                message_data = json.loads(mensaje_decodificado)
                message_data['time'] = timestamp
                message_data['node'] = self.node_id
                action = message_data.get('action')

                # Further processing based on the action
                if action == 'request_access':
                    self.handle_request_access(message_data)
                elif action == 'update_inventory':
                    self.handle_update_inventory(message_data)
                elif action == 'get_inventory':
                    self.handle_get_inventory(direccion, message_data)
                elif action == 'buy_item':
                    self.handle_buy_item(message_data)

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

    def handle_update_inventory(self, message):
        # Implementar lógica de consenso para actualizar el inventario
        # Aquí se debe considerar la distribución equitativa y la verificación del espacio en cada sucursal
        pass

    def handle_get_inventory(self, client_address):
        # Enviar el inventario al nodo cliente
        response = {'action': 'send_inventory', 'inventory': self.inventory}
        response_json = json.dumps(response).encode('utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as response_socket:
            response_socket.sendto(response_json, client_address)

    def handle_buy_item(self, message):
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

            if not self.token_stack and not self.request_queue.empty():
                # Si no hay tokens disponibles y hay solicitudes en la cola, generar un nuevo token
                new_token = f'Token-{time.time()}'
                self.token_stack.append(new_token)

                # Desencolar la solicitud y enviar el token al nodo que solicitó acceso
                node_id = self.request_queue.get()
                self.send_token(node_id, new_token)

    def recibir_mensajes(self):
        mensaje_confirmado = False
        while True:
            try:
                mensaje_recibido, direccion = server_socket.recvfrom(1024)
                mensaje_decodificado = mensaje_recibido.decode('utf-8')
                
                # Decodifica el mensaje JSON
                mensaje_json = json.loads(mensaje_decodificado)

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                mensaje_completo = f"{timestamp} - Mensaje RECIBIDO de {direccion}: {mensaje_json}"
                mensajes_para_guardar.append(mensaje_completo)

                if not mensaje_confirmado:
                    # Enviar un mensaje de confirmación al remitente
                    confirmacion = {"mensaje": "Confirmo la recepcion de tu mensaje"}
                    socket.sendto(json.dumps(confirmacion).encode('utf-8'), direccion)
                    print(mensaje_completo)
                    mensaje_confirmado = True
            except socket.timeout:
                mensaje_confirmado = False

    def guardar_mensajes(self):
        while True:
            if mensajes_para_guardar:
                mensaje_para_guardar = mensajes_para_guardar.pop(0)
                with open("logMensajes.txt", "a") as log_file:
                    log_file.write(mensaje_para_guardar + "\n")
                time.sleep(1)  # Espera un segundo antes de intentar guardar el siguiente mensaje

    def enviar_mensajes(self):
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
            destino_puerto = 5000
            socket.sendto(json.dumps(mensaje_json).encode('utf-8'), (destino_ip, destino_puerto))
            mensajes_para_guardar.append(mensaje_completo)

    def consultar(self, nodo):
        pass

    def vender(self, item_id, cantidad):
        pass

    def agregar(self, item_id, cantidad):
        pass

    def is_master(self):
        # Comprueba si este nodo es el maestro
        return self.node_id == self.master_node
    
    def handle_node_failure(self, node_ip):#######################################################
        if node_ip not in self.failed_nodes:
            # Acciones a realizar cuando se detecta un nodo caído por primera vez
            print(f"Nodo caído detectado: {node_ip}")
            # Implementar acciones específicas por la caída del nodo
            self.failed_nodes.add(node_ip)  # Agrega el nodo al conjunto de nodos caídos

    def load_inventory_from_file(file_path="inventario.json"):
            try:
                with open(file_path, "r") as file:
                    inventory_data = json.load(file)
                return inventory_data
            except FileNotFoundError:
                print(f"Error: File '{file_path}' not found.")
                return None
            except json.JSONDecodeError:
                print(f"Error: Unable to decode JSON in file '{file_path}'.")
                return None

    def send_heartbeats(self):
                while True:
                    heartbeat_msg = "Heartbeat"
                    if self.is_master():
                        heartbeat_msg += ":Master" ##AQUI PUEDE REALIZAR FUNCIONES EL NODO MAESTRO ########################################
                    for node_ip in self.lista_ip_nodo:
                        try:
                            server_socket.sendto(heartbeat_msg.encode(), (node_ip, self.port))
                        except Exception as e:
                            print(f"Error al enviar heartbeat a {node_ip}: {e}")
                            pass
                    time.sleep(HEARTBEAT_INTERVAL)

        # Esta función recibe heartbeats y actualiza el estado de los nodos
    def receive_heartbeats_modified(self):
                while True:
                    current_time = time.time()
                    for node_ip, last_hb_time in list(self.last_heartbeat.items()):
                        if current_time - last_hb_time > MAX_INACTIVE_TIME and node_ip != self.host:
                            self.handle_node_failure(node_ip)
                            # Actualiza el último heartbeat para evitar múltiples detecciones
                            self.last_heartbeat[node_ip] = current_time
                    try:
                        data, addr = self.server_socket.recvfrom(1024)
                        self.last_heartbeat[addr] = time.time()
                        if "Master" in data.decode():
                            if addr != self.master_node:
                                print(f"Nuevo nodo maestro elegido: {addr}")
                                self.master_node = addr
                        #print(f"Heartbeat recibido de {addr}, nodo activo")
                    except socket.timeout:
                        pass
                    self.determine_master()
                pass
            # Función para determinar el nodo maestro

    def determine_master(self):
                with self.master_lock:
                    current_time = time.time()
                    active_nodes = {ip: self.last_heartbeat[ip] for ip in self.lista_ip_nodo if current_time - self.last_heartbeat.get(ip, 0) <= MAX_INACTIVE_TIME}
                    if active_nodes:
                        highest_ip = max(active_nodes.keys())
                        if highest_ip != self.master_node:
                            self.master_node = highest_ip
                            print(f"El nodo maestro actual es: {self.master_node}")


    #Funcion para hacer la seleccion de comando (Punto de vista del usuario que controla todo)
def sel_comando():
        comando = input("Escribe un comando:").split()
        if not comando:
            pass
        elif(comando[0].startswith("/")):
            seleccion = comando[0]
            seleccion = seleccion[1:]
            if seleccion == "help":
                print("""La lista de comandos es:
        /consultar {nodo} #Regresa el listado de id, articulo y cantidad, del nodo, en pantalla
        /vender {item_id} {cantidad} #Regresa un "ticket" en pantalla con (IDARTICULO+SERIE+SUCURSAL+IDCLIENTE)
        /agregar {item_id} {cantidad} #Regresa una confirmacion en pantalla de que fue agregado exitosamente
    Gracias""")
            elif seleccion == "consultar":
                if (len(comando) == 2):
                    node.consultar(comando[1])
                else:
                    print("Especifica el nodo a consultar el inventario")
            elif seleccion == "vender":
                if (len(comando) == 3):
                    node.vender(comando[1],comando[2])
                else:
                    print("Especifica el id del item y la cantidad a vender")
            elif seleccion == "agregar":
                if (len(comando) == 3):
                    node.agregar(comando[1],comando[2])
                else:
                    print("Especifica el id del item y la cantidad a agregar")
            else:
                print("Comando no valido. Escribe /help para mayor informacion")
        else:
            print("Comando no valido. Escribe /help para mayor informacion")

    #Funcion de apoyo para automatizar la capacidad en un mismo codigo
def get_random_integer():
        pool = [100, 120, 150, 200, 230, 250]
        random_integer = random.choice(pool)
        return random_integer

    #Funcion exclusivamente para conseguir el ip local
def get_local_ip():
        try:
            # Create a socket connection to an external server
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Connecting to Google's public DNS server
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"Error: {e}")
            return None

def main():
        node = Node(node_id=Node.lista_ip_nodo[get_local_ip()], capacity=get_random_integer())
        node.start(host= get_local_ip())
        # Iniciar hilos para enviar y recibir heartbeats
        while True:
            sel_comando()

main()
