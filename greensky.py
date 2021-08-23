import socket
import sys
import threading

def pretty_ip(ip_tuple):
    """Takes a tuple of (host,port) and returns a string of host:port"""
    return str(ip_tuple[0])+":"+str(ip_tuple[1])
class SocketHandler():
    def __init__(self,custom_socket):
        self.class_socket=custom_socket
        self.connection=self.class_socket
        self.adress=None
        self.mode=None
    def set_handling(self,mode):
        """Either sends or receives a file, depending on the input mode"""
        if mode=="0":
            self.mode="0"
            self.connection.send(bytes("1","utf-8"))
        elif mode=="1":
            self.mode="1"
            self.connection.send(bytes("0","utf-8"))
    def wait_for_both(self):
        self.connection.send(bytes("0","utf-8"))
        self.connection.recv(1024)
    def transfer_file(self):
        if self.mode=="0":
            file_path=input("Enter the path to the file you want to send\n>")
            self.wait_for_both()

            #This thing is when it actually sends the file
            send_file=open(file_path,"rb")
            some_bytes=send_file.read(1024)
            while some_bytes:
                self.connection.send(some_bytes)
                some_bytes=send_file.read(1024)
        if self.mode=="1":
            file_path=input("Enter the path to which you want to receive the file\n>")
            self.wait_for_both()

            write_file=open(file_path,"wb")
            some_bytes=self.connection.recv(1024)
            while some_bytes:
                write_file.write(some_bytes)
                some_bytes=self.connection.recv(1024)

settings_dict={"port":9999,"print_server_ips":True,"choose_host_ip":True}

operation_type=""
while operation_type not in ["0","1"]:
    operation_type=input("Select which one you want to be\n0=server\n1=client\n>")

if operation_type=="0":
    #Socket creation
    this_socket=socket.socket()
    socket_handler=SocketHandler(this_socket)

    #Eventual ip printing
    if settings_dict["print_server_ips"]:#This "if" prints all the ips which the host can give to others in order for them to connect
        ip_list=socket.getaddrinfo(socket.gethostname(),settings_dict["port"])
        useable_ip_list=[pretty_ip(ip[4]) for ip in ip_list if len(ip[4])==2]
        print("Here are all the useable ips: %s"%(str(useable_ip_list)))

    #Socket setup
    socket_handler.class_socket.bind(("192.168.56.1",settings_dict["port"]))#TODO: make ip choosable
    socket_handler.class_socket.listen(1)
    print("Waiting for connection")
    socket_handler.connection, socket_handler.adress=socket_handler.class_socket.accept()

    print("Connection established with %s:%s"%(str(socket_handler.adress[0]),str(socket_handler.adress[1])))
    mode=""
    while mode not in ["0","1"]:
        mode=input("Do you want to send or to receive a file?\n0=send\n1=receive\n>")
    socket_handler.set_handling(mode)
    socket_handler.transfer_file()


if operation_type=="1":
    this_socket=socket.socket()
    socket_handler=SocketHandler(this_socket)
    host_ip=input("Write the host ip\n>")
    socket_handler.class_socket.connect((host_ip,settings_dict["port"]))
    socket_handler.mode=this_socket.recv(1024).decode("utf-8")
    socket_handler.transfer_file()
