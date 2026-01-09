import os #file i/o
import sys #command line inputs
import socket #server stuff
import time #for timer

BUFFER_SIZE = 1000 #1kb

def put_handler(connection_socket, client_ip, file_path, filesize):
    message = "Accepting files from client.\n"
    connection_socket.send(message.encode())
    print(message)
    #connection_socket = socket.socket(connection_socket)
    put_directory = os.path.join("uploads", client_ip) #uploads/ip
    os.makedirs(put_directory, exist_ok=True) #make directory if it doesn't already exist
    file_name = os.path.basename(file_path) #isolate file name
    download_path = os.path.join(put_directory, file_name) #uploads/ip/file_name

    #download
    file_size = int(filesize)
    received_data = 0
    with open(download_path, "wb") as file: #write, binary
        while received_data < file_size:
            chunk = connection_socket.recv(min(BUFFER_SIZE, file_size - received_data))
            if not chunk: #if empty or done
                break
            file.write(chunk)
            received_data = received_data + len(chunk)
    
    #finish
    if received_data == file_size:
        message = "File successfully uploaded.\n"
    else:
        message = f"Error: Expected file size {file_size}, received file size {received_data}.\n"
    connection_socket.send(message.encode()) #send and print message on both ends
    print(message)
    connection_socket.close()

def get_handler(connection_socket, file_path):
    file_path = os.path.join("uploads", file_path) #download from uploads folder
    if not os.path.exists(file_path):
        connection_socket.send(f"{file_path} does not exist on the server.\n".encode())
        return
    
    #send expected size
    file_size = os.path.getsize(file_path)
    connection_socket.send(f"Size={file_size}".encode())
    ready = connection_socket.recv(BUFFER_SIZE).decode() #client says "go!"
    print(ready)
    time.sleep(3)

    #send data
    with open(file_path, 'rb') as file: #read, bytes
        while (True):
            chunk = file.read(BUFFER_SIZE)
            if not chunk: #if done or empty
                break
            connection_socket.send(chunk)
    
    #finish
    message = "File delivered from server.\n"
    connection_socket.send(message.encode())
    print(message)
    connection_socket.close()

# main
if __name__ == "__main__":
    if len(sys.argv) < 2: #start failure
        print("Example launch command: \npython3 serverTCP.py [server port]\n")
        sys.exit(1)
    server_port = int(sys.argv[1])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(1)
    print("Server ready!\n")
    
    while (True):
        try:
            connection_socket, addr = server_socket.accept()
            client_ip = addr[0]
            print(f"{client_ip} has connected.\n")

            #receive command
            client_command = connection_socket.recv(BUFFER_SIZE).decode().strip()
            command_parts = client_command.split()
            command = command_parts[0]
            
            if command == "put":
                file_name = command_parts[1]
                file_size = command_parts[2]
                put_handler(connection_socket, client_ip, file_name, file_size)
            elif command == "get":
                file_name = command_parts[1]
                get_handler(connection_socket, file_name)
            elif command == "quit":
                print(f"{client_ip} has called quit().\n")
                connection_socket.send(f"Server on port {server_port} is shutting down...\n".encode()) #notify client
                connection_socket.close()
                break
            
        except KeyboardInterrupt:
            print("[-!-] Server shutting down! [-!-]\n")
            break
    
    server_socket.close() #finished, shut it down