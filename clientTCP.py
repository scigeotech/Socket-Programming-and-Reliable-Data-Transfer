import os #file i/o
import sys #command line inputs
import socket #server stuff

BUFFER_SIZE = 1000 #1kb

def put_file(file_path, server_ip, server_port):
    file_path = os.path.join("downloads", file_path)
    if not os.path.isfile(file_path):
        print(f"{file_path} does not exist on the client.\n")
        return
    
    #connect
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
    client_socket.connect((server_ip, server_port)) #connect socket to provided server

    #send command
    file_size = os.path.getsize(file_path)
    client_command = f"put {file_path} {file_size}" #send base file name since server won't need dir data
    client_socket.send(client_command.encode())
    
    response = client_socket.recv(BUFFER_SIZE).decode()
    print(f"Server said: {response}")

    #send file
    with open(file_path, "rb") as file: #open to read in binary, file automatically closes
        while (True):
            chunk = file.read(BUFFER_SIZE) #read file into chunk
            if not chunk: #if empty
                break
            client_socket.send(chunk)
    
    #accept response
    response = b""
    while (True):
        data = client_socket.recv(BUFFER_SIZE)
        if not data: #if empty
            break
        response = response + data
        if b"\n" in response: #if end of line
            break
    print(f"Server Message: {response.decode().strip()}\n")
    client_socket.close() # --- END ---

def get_file(file_name, server_ip, server_port):
    #connect
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
    client_socket.connect((server_ip, server_port)) #connect socket to provided server

    #send command
    client_command = f"get {file_name}" #
    client_socket.send(client_command.encode())

    #receive filesize
    file_size = client_socket.recv(BUFFER_SIZE).decode()
    if not file_size.startswith("Size="):
        print(f"Get Failure: {file_size}\n")
        client_socket.close()
        return
    file_size = int(file_size.split('=')[1])
    print(f"Expected File Size: {file_size}\n")
    client_socket.send("ready".encode()) #say "go!""
    
    received_data = 0 #count received file size to make sure it matches

    write_file = os.path.basename(file_name) #isolate file name
    write_file = os.path.join("downloads", write_file) #download to downloads folder
    with open(write_file, 'wb+') as file:
        while received_data < file_size:
            chunk = client_socket.recv(min(BUFFER_SIZE, file_size - received_data))
            if not chunk: #if empty or done
                break
            file.write(chunk)
            received_data = received_data + len(chunk)
    if not received_data == file_size:
        print(f"Error: Expected file size {file_size}, received file size {received_data}. Consider redownloading the file.\n")
    
    #accept server control message
    finish = b""
    while (True):
        data = client_socket.recv(BUFFER_SIZE)
        if not data: #if empty
            break
        finish = finish + data
        if b"\n" in finish: #if end of line
            break
    print(f"Server Message: {finish.decode().strip()}\n")
    client_socket.close() # --- END ---

def quit(server_ip, server_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create socket
    client_socket.connect((server_ip, server_port)) #connect socket to provided server

    #send command
    client_command = f"quit" #self-explanatory
    client_socket.send(client_command.encode())
    print(client_socket.recv(BUFFER_SIZE).decode()) #server response

    client_socket.close() #end

# main
if __name__ == "__main__":
    #start client
    if len(sys.argv) < 3: #start failure
        print("Example launch command: \npython3 clientTCP.py [server ip] [server port]\n")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    print("Client ready!\n")
    print("Available Commands:\nput [file_path]\nget [file_path]\nquit\n")

    while(True):
        file_name = None #generic descriptor -- can be a file name or a file path
        command = input("CMD: ").strip() #ask user for input
        if not command:
            continue
        if command.lower().startswith("put "): #upload to server
            command_parts = command.split()
            file_name = command_parts[1]
            put_file(file_name, server_ip, server_port) #finally upload
        elif command.lower().startswith("get "): #download to client
            command_parts = command.split()
            file_name = command_parts[1]
            get_file(file_name, server_ip, server_port)
        elif command.lower() == "quit":
            print("Client quitting...")
            quit(server_ip, server_port) #call quit
            break
        else:
            print(f"{command} is not a correct command, try again.\n")
