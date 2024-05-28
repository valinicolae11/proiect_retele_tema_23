import socket
import threading
import json

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5555

BROADCAST_ADDRESS = "0.0.0.0"
BROADCAST_PORT = 5556

available_rooms = {}
current_room_info = None
joined_room = False

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            print(message)
        except:
            break

def receive_rooms():
    global available_rooms
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_socket.bind((BROADCAST_ADDRESS, BROADCAST_PORT))
    while True:
        data, _ = broadcast_socket.recvfrom(1024)
        available_rooms = json.loads(data.decode())
        print("Lista camerelor virtuale actualizata:", available_rooms)

def receive_multicast(client_socket, current_room_info):
    multicast_group = (current_room_info["address"], current_room_info["port"])
    multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_socket.bind(("", current_room_info["port"]))

    mreq = socket.inet_aton(current_room_info["address"]) + socket.inet_aton("0.0.0.0")
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        message, _ = multicast_socket.recvfrom(1024)
        print(f"Multicast: {message.decode()}")

def main():
    global current_room_info, joined_room, available_rooms

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_ADDRESS, SERVER_PORT))
    print("Conectat la server.")

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    broadcast_thread = threading.Thread(target=receive_rooms)
    broadcast_thread.start()

    while True:
        
        command = input("Introdu o comanda (JOIN nume_camera/LEAVE/MESSAGE nume_camera mesaj/ADD nume_camera/DELETE nume_camera): ")
        if command.startswith("JOIN"):
            room_name = command.split()[1]
            if room_name not in available_rooms:
                print("Camera virtuala nu exista!")
                continue  
            client_socket.send(command.encode())
            response = client_socket.recv(1024).decode()
            try:
                room_info = json.loads(response)
                current_room_info = room_info
                joined_room = True
                multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                multicast_socket.bind(("", current_room_info["port"]))

                mreq = socket.inet_aton(current_room_info["address"]) + socket.inet_aton("0.0.0.0")
                multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

                multicast_thread = threading.Thread(target=receive_multicast, args=(multicast_socket,))
                multicast_thread.start()
            except json.JSONDecodeError:
                print(response)
        elif command == "LEAVE" and joined_room:
            client_socket.send(command.encode())
            joined_room = False
        elif command.startswith("MESSAGE"):
            if joined_room:
                multicast_address = room_info["address"]
                port = room_info["port"]

                _, message = command.split(" ", 2)

                multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                multicast_socket.bind(("", port))

                mreq = socket.inet_aton(multicast_address) + socket.inet_aton("0.0.0.0")
                multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                multicast_socket.sendto(f"[USER {socket.gethostname()}] {message}".encode(), (multicast_address, port))
                multicast_socket.close()

                print("Mesaj trimis cu succes!")
            else:
                client_socket.send("Nu esti intr-o camera virtuala!".encode())
        else:
            client_socket.send(command.encode())
        print("Camerele disponibile:", available_rooms.keys())

if __name__ == "__main__":
    main()
