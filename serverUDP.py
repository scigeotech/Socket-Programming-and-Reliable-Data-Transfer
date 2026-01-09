import os #file i/o
import sys #command line inputs
import socket #server stuff
import time #for timer

BUFFER_SIZE = 1000 #8kb
TIMEOUT = 1.0

def put_handler(server_socket, client_address, client_ip, file_path, filesize):
    message = "Accepting files from client.\n"
    server_socket.sendto(message.encode(), client_address) #send "ACK" to begin
    print(message)

    put_directory = os.path.join("uploads", client_ip) #uploads/ip
    os.makedirs(put_directory, exist_ok=True) #make directory if it doesn't already exist
    file_name = os.path.basename(file_path) #isolate file name
    download_path = os.path.join(put_directory, file_name) #uploads/ip/file_name

    #download
    file_size = int(filesize)
    print(f"Expecting {file_size} bytes")
    received_data = 0
    server_socket.settimeout(TIMEOUT)
    with open(download_path, "wb") as file: #write, binary
        while received_data < file_size:
            try:
                chunk, client_address = server_socket.recvfrom(min(BUFFER_SIZE, file_size - received_data))
                if not chunk: #if empty or done
                    break
                file.write(chunk)
                received_data = received_data + len(chunk)
                server_socket.sendto("ACK".encode(), client_address) #ACK the chunk
            except socket.timeout:
                print("Data transmission terminated prematurely.")
                return   
    
    #finish
    if received_data == file_size:
        message = "File successfully uploaded.\n"
    else:
        message = f"Error: Expected file size {file_size}, received file size {received_data}.\n"
    server_socket.sendto(message.encode(), client_address) #send and print message on both ends
    print(message)
    server_socket.settimeout(None)

def get_handler(server_socket, client_address, file_path):
    file_path = os.path.join("uploads", file_path) #download from uploads folder
    if not os.path.exists(file_path):
        server_socket.sendto(f"{file_path} does not exist on the server.\n".encode(), client_address)
        return
    
    #send expected size
    file_size = os.path.getsize(file_path)
    server_socket.sendto(f"LEN:{file_size}".encode(), client_address)
    ready, client_address = server_socket.recvfrom(BUFFER_SIZE) #client says "go!" (ACK)
    print(ready.decode())

    acked = 0
    server_socket.settimeout(TIMEOUT)
    #send data
    with open(file_path, 'rb') as file: #read, bytes
        while (True):
            chunk = file.read(BUFFER_SIZE) #read file into chunk
            if not chunk: #if done or empty
                break
            server_socket.sendto(chunk, client_address)
            
            #wait for ack
            try:
                ack, client_address = server_socket.recvfrom(BUFFER_SIZE) #obtain ack
                if not ack.decode() == "ACK":
                    print(f"Error: Expected ACK, received {ack.decode()}")
                    break
                elif ack.decode() == "ACK":
                    acked = acked + 1
                    print(f"Received ACK#{acked}")
            except socket.timeout: #timeout
                print("Did not receive ACK. Terminating.\n")
                return
    
    #finish
    message = "File delivered from server. FIN\n"
    server_socket.sendto(message.encode(), client_address)
    print(message)
    server_socket.settimeout(None)

# main
if __name__ == "__main__":
    if len(sys.argv) < 2: #start failure
        print("Example launch command: \npython3 serverUDP.py [server port]\n")
        sys.exit(1)
    server_port = int(sys.argv[1])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', server_port))
    print("Server ready!\n")
    
    while (True):
        try:
            server_socket.settimeout(None) #we can wait forever for an initiation
            #receive command
            client_command, client_address = server_socket.recvfrom(BUFFER_SIZE)
            client_ip = client_address[0] #retrieve client ip from address
            print(f"{client_ip} made contact with the server.\n") #not actually connecting, i think

            client_command = client_command.decode().strip() #cleanup
            command_parts = client_command.split() #dissection
            command = command_parts[0]
            
            if command == "put":
                file_name = command_parts[1]
                file_size = command_parts[2]
                file_size = int(file_size.split(':')[1])
                put_handler(server_socket, client_address, client_ip, file_name, file_size)
            elif command == "get":
                file_name = command_parts[1]
                get_handler(server_socket, client_address, file_name)
            elif command == "quit":
                #no connection to close, just leave
                print(f"{client_ip} has called quit().\n")
                server_socket.sendto(f"Server on port {server_port} is shutting down...\n".encode(), client_address) #notify client
                break
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("[-!-] Server shutting down! [-!-]\n")
            break
    
    server_socket.close() #finished, shut it down