import socket
import sys
import os
import argparse
from colorama import  Fore, Style, Back
from re import sub
import datetime

def colorize(stringa):
    """Prints the given string with cool custom colors"""
    while "$" in stringa:
        stringa=sub("\$BMAGENTA\((.*)\)",Back.MAGENTA+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$BLUE\((.*)\)",Fore.BLUE+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$CYAN\((.*)\)",Fore.CYAN+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$MAGENTA\((.*)\)",Fore.MAGENTA+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$GREEN\((.*)\)",Fore.GREEN+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$RED\((.*)\)",Fore.RED+"\g<1>"+Style.RESET_ALL,stringa)
        stringa=sub("\$YELLOW\((.*)\)",Fore.YELLOW+"\g<1>"+Style.RESET_ALL,stringa)
    return stringa
def cprint(stringa):
    """The same as writing print(colorize(stringa))"""
    print(colorize(stringa))

def rinput(stringa,valid_input_list,output_value=""):
    outvalue=output_value
    while outvalue not in valid_input_list:
        outvalue=input(stringa)
    return outvalue

settings_dict={"side":"","operation":"","ip":"","file_path":"","file_name":None,"port":9999,"print_server_ips":True,"choose_host_ip":True,"buffer":1024}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("--side",help="Choose this terminal's side. 0=server-side; 1=client-side")
    parser.add_argument("--operation",help="Choose which action to perform. 0=send file; 1=receive file")
    parser.add_argument("--ip",help="Specify the ipv4 adress which will host the server/to which the client will connect")
    parser.add_argument("--file_path",help="Specify the path of the file to upload/where to download the file")
    parser.add_argument("--file_name",help="Specify the name of the file you will download")
    parser.add_argument("--buffer",help="Specify how many bytes are sent at once")
    args=parser.parse_args()
    
    settings_dict["side"]=args.side if args.side!=None else ""
    settings_dict["operation"]=args.operation if args.operation!=None else ""
    settings_dict["ip"]=args.ip if args.ip!=None else ""
    settings_dict["file_path"]=args.file_path if args.file_path!=None else ""
    settings_dict["file_name"]=args.file_name if args.file_name!=None else None
    settings_dict["buffer"]=int(args.buffer) if args.buffer!=None else 1024

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
        self.send_string("")
        out=self.receive_string()
        if out!="":
            print(out)
    
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
        #SENDER
        if self.mode=="0":
            file_path=""
            second_time=False
            while file_path=="":
                if settings_dict["file_path"]=="" or second_time:
                    file_path=input(colorize("$MAGENTA(Enter the path of the file you want to send)\n>"))
                else:
                    file_path=settings_dict["file_path"]
                if not os.path.isfile(file_path):#Redo if unvalid file
                    cprint("$YELLOW(The path you entered does not lead to a file)")
                    file_path=""
                    second_time=True
            print(colorize("$GREEN(Waiting for receiver to choose destination directory...)"))
            self.send_string(os.path.basename(file_path))#Link2#
            self.wait_for_both()

            self.send_string(str(settings_dict["buffer"]))#Link3#
            cprint("$CYAN(Started sending file with byte buffer of %i)"%(settings_dict["buffer"]))
            self.wait_for_both()

            filesize=int(os.path.getsize(file_path))#Get file size
            self.send_string(str(filesize))#Send file size
            self.wait_for_both()

            #This thing is when it actually sends the file
            send_file=open(file_path,"rb")
            some_bytes=send_file.read(settings_dict["buffer"])
            self.connection.send(some_bytes)
            
            current_size=settings_dict["buffer"]
            
            #Time calculation
            start_time=datetime.datetime.now()
            eta=0
            total_time=0
            while some_bytes:
                print("Progress: %i/%i-%i"%(current_size,filesize,((current_size*100)/filesize))+"%"+" | ETA: %s | Elapsed: %s"%(str(datetime.timedelta(seconds=int(eta))),str(datetime.timedelta(seconds=int(total_time)))),end="\r")
                some_bytes=send_file.read(settings_dict["buffer"])
                self.connection.send(some_bytes)

                #Time calculation
                end_time=datetime.datetime.now()
                total_time=(end_time-start_time).total_seconds()
                eta=(((filesize-current_size)*total_time)/current_size)

                current_size+=settings_dict["buffer"]
                current_size=filesize if current_size>filesize else current_size
            print("\nDone!")

        #RECEIVER
        if self.mode=="1":
            file_path=""
            while file_path=="":
                if settings_dict["file_path"]!="":
                    file_path=settings_dict["file_path"]
                else:
                    file_path=input(colorize("$MAGENTA(Enter the directory where you want to save the file)\n>"))
                if not os.path.isdir(file_path):
                    if settings_dict["file_path"]!="":
                        handling_directory="0"
                    else:
                        handling_directory=rinput(colorize("$YELLOW(The directory you entered does not exist or is not valid)\n$MAGENTA(Select the option you prefer)\n$BMAGENTA(0|Create directory)\n$BMAGENTA(1|Enter a different directory)\n>"),["0","1"])
                    if handling_directory=="0":
                        os.makedirs(file_path)
                        cprint("$CYAN(Created a new directory: %s)"%(file_path))
                    else:
                        file_path=""
            print(colorize("$GREEN(Waiting for sender to choose file...)"))

            #Choose file name
            filename=self.receive_string()#Link2#
            if settings_dict["file_name"]==None:
                custom_file_name=input(colorize("$MAGENTA(Host is sending a file named %s. Press enter to save it as such or type a different name)\n>"%(filename)))
            else:
                custom_file_name=settings_dict["file_name"]

            #Create path
            if custom_file_name=="":
                file_path=file_path+filename
            else:
                file_path=file_path+custom_file_name
            self.wait_for_both()

            buffer=int(self.receive_string())#Link3#
            cprint("$CYAN(Started receiving file with byte buffer of %i)"%(buffer))
            self.wait_for_both()

            filesize=int(self.receive_string())
            self.wait_for_both()

            write_file=open(file_path,"wb")
            some_bytes=self.connection.recv(buffer)
            
            current_size=len(some_bytes)

            #Time calculation
            start_time=datetime.datetime.now()
            eta=0
            total_time=0
            while some_bytes:
                print("Progress: %i/%i-%i"%(current_size,filesize,((current_size*100)/filesize))+"%"+" | ETA: %s | Elapsed: %s"%(str(datetime.timedelta(seconds=int(eta))),str(datetime.timedelta(seconds=int(total_time)))),end="\r")
                write_file.write(some_bytes)
                some_bytes=self.connection.recv(buffer)
                
                #Time calculation
                end_time=datetime.datetime.now()
                total_time=(end_time-start_time).total_seconds()
                eta=(((filesize-current_size)*total_time)/current_size)

                current_size+=len(some_bytes)
            write_file.close()
            print("\nDone!")

operation_type=settings_dict["side"]
while operation_type not in ["0","1"]:
    operation_type=input(colorize("$MAGENTA(Select which one you want to be)\n$BMAGENTA(0|server)\n$BMAGENTA(1|client)\n>"))

if operation_type=="0":
    print(colorize("$CYAN(Started as server)"))
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
            host_ip=input(colorize("$MAGENTA(Insert the ip you want to use as host)\n>"))
    else:
        host_ip=useable_ip_list[0]
    socket_handler.class_socket.bind((host_ip,settings_dict["port"]))
    socket_handler.class_socket.listen(1)
    print(colorize("$GREEN(Waiting for connection...)"))
    socket_handler.connection, socket_handler.adress=socket_handler.class_socket.accept()

    #Choosing mode: server only; between send and receive
    print(colorize("$CYAN(Connection established with %s:%s)"%(str(socket_handler.adress[0]),str(socket_handler.adress[1]))))
    mode=settings_dict["operation"]
    while mode not in ["0","1"]:
        mode=input(colorize("$MAGENTA(Do you want to send or to receive a file?)\n$BMAGENTA(0|send)\n$BMAGENTA(1|receive)\n>"))
    print(colorize("$CYAN(You chose sending a file)" if mode=="0" else "$CYAN(You chose receiving a file)"))
    socket_handler.set_handling(mode)#Sends send/receive mode; #Link1#
    socket_handler.transfer_file()

if operation_type=="1":
    print(colorize("$CYAN(Started as client)"))
    this_socket=socket.socket()
    socket_handler=SocketHandler(this_socket)
    host_ip=settings_dict["ip"]
    while host_ip=="":
        host_ip=input(colorize("$MAGENTA(Write the host ip)\n>"))
    print(colorize("$GREEN(Waiting for connection...)"))
    socket_handler.class_socket.connect((host_ip,settings_dict["port"]))
    print(colorize("$CYAN(Connection established with %s:%s)"%(str(host_ip),str(settings_dict["port"]))))
    print(colorize("$GREEN(Waiting for host to choose mode...)"))
    socket_handler.mode=socket_handler.receive_string()#Expects to receive send/receive mode; seems to cause bugs by getting what it should not get; #Link1#
    print(colorize("$CYAN(Host chose you will send a file)" if socket_handler.mode=="0" else "$CYAN(Host chose you will receive a file)"))
    socket_handler.transfer_file()
