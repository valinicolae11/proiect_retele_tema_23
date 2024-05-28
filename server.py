import socket
import threading
import json

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555

BROADCAST_ADDRESS = "255.255.255.255"
BROADCAST_PORT = 5556

rooms = {
    
}

def handle_client(client_socket):
    current_room = None

    while True:
        try:
            request = client_socket.recv(1024).decode()
            if request.startswith("JOIN"):
                room_name = request.split()[1]
                if room_name in rooms:
                    rooms[room_name]["clients"].append(client_socket)
                    room_info = {"address": rooms[room_name]["address"], "port": rooms[room_name]["port"]}
                    client_socket.send(json.dumps(room_info).encode())
                    current_room = room_name
                    client_socket.send("Ai intrat in camera cu succes!".encode())
                else:
                    client_socket.send("Camera virtuala nu exista!".encode())
            elif request == "LEAVE":
                if current_room:
                    rooms[current_room]["clients"].remove(client_socket)
                    client_socket.send(f"Ai iesit din camera {current_room}".encode())
                    current_room = None
            elif request.startswith("MESSAGE"):
                if current_room:
                    _, message = request.split(" ", 1)
                    multicast_message(current_room, message)
                    client_socket.send("Mesaj trimis cu succes!".encode()) 
                else:
                    client_socket.send("Nu esti intr-o camera virtuala!".encode())
            elif request.startswith("ADD"):
                room_name = request.split()[1]
                if room_name not in rooms:
                    new_address = f"224.1.1.{len(rooms) + 1}"
                    new_port = 5557 + len(rooms)
                    rooms[room_name] = {"address": new_address, "port": new_port, "clients": []}
                    broadcast_rooms()
            elif request.startswith("DELETE"):
                room_name = request.split()[1]
                if room_name in rooms:
                    del rooms[room_name]
                    broadcast_rooms()
        except Exception as e:
            print(f"Eroare la procesarea cererii: {e}")
            break

def broadcast_rooms():
    broadcast_data = {room_name: {"address": room_details["address"], "port": room_details["port"]} for room_name, room_details in rooms.items()}
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto(json.dumps(broadcast_data).encode(), (BROADCAST_ADDRESS, BROADCAST_PORT))
    broadcast_socket.close()

def multicast_message(room_name, message):
    multicast_group = (rooms[room_name]["address"], rooms[room_name]["port"])
    multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    multicast_socket.sendto(message.encode(), multicast_group)
    multicast_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))
    server_socket.listen(5)
    print("[SERVER] Serverul asculta pe adresa", SERVER_ADDRESS, "si portul", SERVER_PORT)

    while True:
        client_socket, _ = server_socket.accept()
        print("[SERVER] S-a conectat un client.")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

start_server()
