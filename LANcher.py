import socket
import sys
import os
import argparse

def pget(stringa):
    print(stringa)
    return stringa
def random_return(stringa):
    return stringa

settings_dict={"side":"","operation":"","ip":"","file_path":"","port":9999,"print_server_ips":True,"choose_host_ip":True}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("--side",help="Choose this terminal's side. 0=server-side; 1=client-side")
    parser.add_argument("--operation",help="Choose which action to perform. 0=send file; 1=receive file")
    parser.add_argument("--ip",help="Specify the ipv4 adress which will host the server/to which the client will connect")
    parser.add_argument("--file_path",help="Specify the path of the file to upload/where to download the file")
    args=parser.parse_args()
    
    settings_dict["side"]=args.side if args.side!=None else ""
    settings_dict["operation"]=args.operation if args.operation!=None else ""
    settings_dict["ip"]=args.ip if args.ip!=None else ""
    settings_dict["file_path"]=args.file_path if args.file_path!=None else ""

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
            self.send_string("1")
        elif mode=="1":
            self.mode="1"
            self.send_string("0")
    def wait_for_both(self):
        print("Waiting...",end="\r")
        self.send_string("")
        self.receive_string()
    
    def send_string(self,stringa,add_footer=True):
        """Send a string safely; the string is received through receive_string()"""
        if add_footer:
            stringa=str(stringa)+"§"
        i=0
        stringa=bytes(stringa,"utf-8")
        #print("Sending: "+str(stringa))
        byte_list=list(stringa)
        #print(byte_list)
        #print(bytes(stringa,"utf-8"))
        for single_byte in byte_list:
            #str(stringa[i])
            self.connection.send(bytes([single_byte]))
    def receive_string(self):
        """Receive a string safely; the string is sent through send_string()"""
        output_string=bytes("","utf-8")
        while bytes("§","utf-8") not in output_string:
            output_string=b"".join([output_string,self.connection.recv(1)])
            #output_string=output_string+pget(self.connection.recv(1))
        #print("---")
        #print(output_string)
        output_string=output_string.decode('utf-8')
        #print(output_string)
        return output_string.replace("§","")

    def transfer_file(self):
        if self.mode=="0":#SENDER
            file_path=settings_dict["file_path"]
            while file_path=="":
                file_path=input("Enter the path of the file you want to send\n>")
            self.wait_for_both()

            filesize=int(os.path.getsize(file_path))#Get file size
            self.send_string(str(filesize))#Send file size
            self.wait_for_both()

            #This thing is when it actually sends the file
            send_file=open(file_path,"rb")
            some_bytes=send_file.read(1024)
            self.connection.send(some_bytes)
            current_size=1024
            while some_bytes:
                print("Progress: %i/%i-%i"%(current_size,filesize,((current_size*100)/filesize))+"%",end="\r")
                some_bytes=send_file.read(1024)
                self.connection.send(some_bytes)
                self.send_string(str(current_size))
                #self.wait_for_both()
                current_size+=1024
                current_size=filesize if current_size>filesize else current_size
            print("\nDone!")


        if self.mode=="1":#RECEIVER
            file_path=settings_dict["file_path"]
            while file_path=="":
                file_path=input("Enter the path where you want to save the file\n>")
            self.wait_for_both()

            filesize=int(self.receive_string())
            self.wait_for_both()

            current_size=1024
            write_file=open(file_path,"wb")
            some_bytes=self.connection.recv(1024)
            while some_bytes:
                print("Progress: %i/%i-%i"%(current_size,filesize,((current_size*100)/filesize))+"%",end="\r")
                write_file.write(some_bytes)
                some_bytes=self.connection.recv(1024)
                current_size=int(self.receive_string())
            write_file.close()
            print("\nDone!")

operation_type=settings_dict["side"]
while operation_type not in ["0","1"]:
    operation_type=input("Select which one you want to be\n0=server\n1=client\n>")

if operation_type=="0":
    print("Started as server")
    #Socket creation
    this_socket=socket.socket()
    socket_handler=SocketHandler(this_socket)

    #Getting useable ips
    ip_list=socket.getaddrinfo(socket.gethostname(),settings_dict["port"])
    useable_ip_list=[pretty_ip(ip[4]) for ip in ip_list if len(ip[4])==2]
    #Eventual ip printing
    if settings_dict["print_server_ips"] and settings_dict["ip"]=="":#This "if" prints all the ips which the host can give to others in order for them to connect
        print("Here are all the useable ips: %s"%(str(useable_ip_list)))

    #Socket setup
    if settings_dict["choose_host_ip"]:
        host_ip=settings_dict["ip"]
        while host_ip=="":
            host_ip=input("Insert the ip you want to use as host\n>")
    else:
        host_ip=useable_ip_list[0]
    socket_handler.class_socket.bind((host_ip,settings_dict["port"]))
    socket_handler.class_socket.listen(1)
    print("Waiting for connection...")
    socket_handler.connection, socket_handler.adress=socket_handler.class_socket.accept()

    #Choosing mode: server only; between send and receive
    print("Connection established with %s:%s"%(str(socket_handler.adress[0]),str(socket_handler.adress[1])))
    mode=settings_dict["operation"]
    while mode not in ["0","1"]:
        mode=input("Do you want to send or to receive a file?\n0=send\n1=receive\n>")
    socket_handler.set_handling(mode)#Sends send/receive mode; #Link1#
    socket_handler.transfer_file()

if operation_type=="1":
    print("Started as client")
    this_socket=socket.socket()
    socket_handler=SocketHandler(this_socket)
    host_ip=settings_dict["ip"]
    while host_ip=="":
        host_ip=input("Write the host ip\n>")
    print("Waiting for connection...")
    socket_handler.class_socket.connect((host_ip,settings_dict["port"]))
    print("Connection established with %s:%s"%(str(host_ip),str(settings_dict["port"])))
    socket_handler.mode=socket_handler.receive_string()#Expects to receive send/receive mode; seems to cause bugs by getting what it should not get; #Link1#
    socket_handler.transfer_file()
