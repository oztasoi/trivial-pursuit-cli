import json
import re
from threading import Thread
import subprocess 
import os
import select
import sys
import socket
import multiprocessing
from colorama import Fore, Style

# message = NAME, MY_IP, TYPE and PAYLOAD.
# Valid TYPE fields for packets are DISCOVER, GOODBYE, RESPOND and MESSAGE

# sendall and receive are non-blocking by default(?) they can be made blocking
# when you send a discover, wait for them to send a response for some time
# open it, send the data, close it
# there are two users named x which one do you want to send to?
# discover() -> reset the dictionary and discover again?
#               new discoveries in different color?

PORT = 12345
SIZE = 1024

EXIT_SIGNAL = str.encode("EXIT_SIG")

nameField = "NAME"
ipField = "MY_IP"
typeField = "TYPE"
payloadField = "PAYLOAD"

discoverType = "DISCOVER"
goodbyeType = "GOODBYE"
respondType = "RESPOND"
messageType = "MESSAGE"

# testing w hamachi
# hamachiIpList = ["25.47.190.102","25.47.190.104", "25.43.1.132", ""]

addressBook = {}
exitSignal = False
myIp = ""
myName = ""

def printAddressBook():
    print(f"{Fore.CYAN}Address book:")
    for ip, username in addressBook.items():
        print(f"{username} ({ip})")
    print(f"{Style.RESET_ALL}")    

# def addToAddressBook(ip,name):
#     exp = f"(?<!.){name}(_\d+)?(?!.)"
#     r = re.compile(exp)
#     targetNames = [u for u in addressBook.values() if r.match(u)]
#     targetIps = [i for i, u in addressBook.items() if r.match(u)]

#     nameCount = len(targetNames)
#     if nameCount>0:
#         if ip not in targetIps:
#             name = f"{name}_{nameCount+1}"
#             addressBook[ip]= name
#             print(f"{Fore.GREEN}Added ({ip}) {name} to the address book{Style.RESET_ALL}")    
#     else:
#         addressBook[ip]= name
#         print(f"{Fore.GREEN}Added ({ip}) {name} to the address book{Style.RESET_ALL}")    


def searchForIp(string):
    regexp ='(?<=inet )192.\d+.\d+.\d+'
    return re.findall(regexp,string)

def searchForHamachiIp(string):
    regexp ='(?<=inet )25.\d+.\d+.\d+'
    # regexp ='(?<=inet )\d+.\d+.\d+.\d+'
    return re.findall(regexp,string)

def findIpList():
    global myIp
    ifconfig = subprocess.run("ifconfig",stdout=subprocess.PIPE,text=True,stderr=subprocess.PIPE )
    l1 = searchForIp(ifconfig.stdout)
    l2 = searchForHamachiIp(ifconfig.stdout)
    finalList = l1 + l2
    if len(finalList) == 1:
        myIp = finalList[0]
        print(f"{Fore.MAGENTA}Your IP address is", myIp, f"{Style.RESET_ALL}")
    elif len(finalList) > 1:
        chosen = False
        while not chosen:
            chosenIp = input(f"{Fore.MAGENTA}Choose an IP from the list: " + ", ".join(finalList)+ f"\n{Style.RESET_ALL}")
            if chosenIp not in finalList:
                print(f"{Fore.MAGENTA}Chosen IP is not in the list{Style.RESET_ALL}")
            else:
                myIp = chosenIp
                print(f"{Fore.MAGENTA}Your IP address is", myIp, f"{Style.RESET_ALL}")
                chosen=True
    else:
        print(f"{Fore.MAGENTA}Your IP address is", myIp, f"{Style.RESET_ALL}")

def createJsonString(name="",ip="",packetType="",payload=""):
    return json.dumps({ 
        nameField: name,
        ipField: ip,
        typeField: packetType,
        payloadField: payload,
    }) + "\n"

def sendExitSignal():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  
        s.setblocking(1)
        s.settimeout(0.5)
        s.connect((myIp, PORT))
        s.sendall(EXIT_SIGNAL) 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: 
        #(TODO) BURADA SIKINTI VAR BENCE 
        # s.bind(('',PORT))
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        s.sendto(EXIT_SIGNAL,(myIp,PORT))

def send(targetIP,name="",ip="",packetType="",payload="",logError = False):
    #(TODO) type = bytes
    response = str.encode(createJsonString(name=name,ip=ip, packetType=packetType, payload=payload))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  
        # print(f"Sending {response} to {targetIP}")
        s.setblocking(1)
        s.settimeout(0.5)

        # maybe you can try to re-send if sending times out
        try:
            s.connect((targetIP, PORT))
        except:
            if logError == True:
                print(f"{Fore.RED}Could not connect to IP (unexpected offline client detected){Style.RESET_ALL}")
            return

        # print(f"{Fore.GREEN}Connected to IP {targetIP}{Style.RESET_ALL}")
        s.sendall(response) 
    if logError == True:        
        print(f"{Fore.GREEN}Message to ({targetIP}) {addressBook[targetIP]}:{Style.RESET_ALL} {payload}")    

# (TODO) "while True:"nun nerede olduğunu değiştir ve dene neler olduğunu
def tcpListener():
    while(myName== "" or myIp==""):
        pass
    
    while(not exitSignal):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((myIp, PORT))
            s.listen()
            while not exitSignal:
                # print("Waiting for TCP")
                allMsg = str.encode("")
                conn = s.accept()[0]
                with conn:
                    while True:
                        msg = conn.recv(SIZE)
                        allMsg = allMsg+msg
                        if not msg:
                            if allMsg == EXIT_SIGNAL:
                                # print( "Exit signal received tcp")
                                return
                            data = allMsg.decode("utf-8").strip().split('\n')

                            # print("Data received tcp: ",data)
                            for datum in data:
                                try:
                                    message = json.loads(datum)
                                except:
                                    # print(f"{Fore.RED}Wrong JSON format received:{Style.RESET_ALL} {datum} bu kadar ")
                                    continue
                                consumeTcp(message)
                            break

def udpListener():
    while(myName== "" or myIp==""):
        pass
    
    while(not exitSignal):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', PORT)) #(TODO) is that correct?
            s.setblocking(0)
            while not exitSignal:
                # print("Waiting for UDP")
                result = select.select([s],[],[])
                msg = result[0][0].recv(SIZE)
                if msg:
                    # print(msg)
                    if msg == EXIT_SIGNAL:
                        # print( "Exit signal received udp")
                        return
                    data = msg.decode("utf-8").strip().split('\n')

                    # print("Data received udp: ",data)
                    for datum in data:
                        try:
                            message = json.loads(datum)
                        except:
                            # print(f"{Fore.RED}Wrong JSON format received:{Style.RESET_ALL} {datum}, bu kadar udp")
                            continue
                        consumeUdp(message)
                    break

def consumeTcp(message):
    if typeField in message:
        if message[typeField] == respondType :
            # addToAddressBook(message[ipField],message[nameField])
            senderIp = message[ipField]
            if senderIp != myIp:
                addressBook[senderIp] = message[nameField]
                print(f"{Fore.GREEN}Added ({message[ipField]}) {message[nameField]} to the address book{Style.RESET_ALL}")    
        elif message[typeField] == messageType:
            print(f"{Fore.GREEN}Message from ({message[ipField]}) {message[nameField]}:{Style.RESET_ALL} {message[payloadField]}") 
        elif message[typeField] == discoverType or message[typeField] == goodbyeType :
            print(f"{Fore.RED}Discover/Goodbye TCP received\n{Style.RESET_ALL}")
        else: 
            print(f"{Fore.RED}Unknown message type\n{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No type field in message (TCP)\n{Style.RESET_ALL}")


def consumeUdp(message):
    if typeField in message:
        if message[typeField] == discoverType:
            # addToAddressBook(message[ipField],message[nameField])
            senderIp = message[ipField]
            if senderIp != myIp:
                addressBook[senderIp] = message[nameField]
                print(f"{Fore.GREEN}Added ({message[ipField]}) {message[nameField]} to the address book{Style.RESET_ALL}")    
                send(targetIP=senderIp,name=myName,ip=myIp, packetType=respondType)
        elif message[typeField] == goodbyeType:
            senderIp = message[ipField]
            addressBook.pop(senderIp,None)
        elif message[typeField] == messageType or message[typeField] == respondType:
            print(f"{Fore.RED}Message/Respond UDP received\n{Style.RESET_ALL}")
        else: 
            print(f"{Fore.RED}Unknown message type\n{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No type field in message (UDP)\n{Style.RESET_ALL}")

def sendBroadcast(broadcastType,count=1):
    global addressBook #(TODO) is this necessary? 
    addressBook = {} #(TODO) bu çalışıyor mu kontrol et
    print(f"{Fore.MAGENTA}Sending {broadcastType}{Style.RESET_ALL}")

    for _ in range(count):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('',0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
            msg = str.encode(createJsonString(name=myName,ip=myIp, packetType=broadcastType, payload=""))

            # s.sendto(msg,('25.255.255.255',PORT))
            broadcastIp = myIp.rsplit(".",1)[0]+".255"
            # s.sendto(msg,('<broadcast>',PORT)) #(TODO) değiştir
            s.sendto(msg,(broadcastIp,PORT)) #(TODO) değiştir
            # print("sending discover", msg)

def initializeClient():
    global myName
    subprocess.run(["clear"])
    print(f"{Fore.MAGENTA}Welcome to NetChat!{Style.RESET_ALL}")    

    myName = input(f"{Fore.MAGENTA}Enter your username:\n{Style.RESET_ALL}")
    while (myName == ""):
        print(f"{Fore.RED}Username cannot be blank\n{Style.RESET_ALL}")
        myName = input(f"{Fore.MAGENTA}Enter your username:\n{Style.RESET_ALL}")

    print(f"{Fore.MAGENTA}Hello {myName}! {Style.RESET_ALL}")    

    findIpList()

    print(f"{Fore.CYAN}Please wait until the client is initialized{Style.RESET_ALL}")   
    print(f"{Fore.CYAN}After the client is initialized, you will be able to type the following commands:{Style.RESET_ALL}")    
    print(f"{Fore.CYAN}\t'username; message':{Style.RESET_ALL} send a message to a person in your address book(ex. 'alex; how are you?')") 
    print(f"{Fore.CYAN}\t'addressBook()':{Style.RESET_ALL} show the ip addresses and usernames in your address book")    
    print(f"{Fore.CYAN}\t'discover()':{Style.RESET_ALL} send discover message again")    
    print(f"{Fore.CYAN}\t'exit()':{Style.RESET_ALL} terminate the app")    

    sendBroadcast(discoverType,3)
    print(f"{Fore.CYAN}Client is initialized, you can start chatting now{Style.RESET_ALL}")

def sendMessage(targetUsername, message):
    targetIp =""
    if targetUsername not in addressBook.values():
        print(f"{Fore.RED}Username not in address book{Style.RESET_ALL}")
        return
    elif sum(value == targetUsername for value in addressBook.values()) > 1:
        ipList = [k for k,v in addressBook.items() if v == targetUsername]
        while targetIp not in ipList:
            targetIp = input(f"{Fore.CYAN}There are multiple IP's with the same username. Choose an IP from the list: " + ", ".join(ipList)+ f"\n{Style.RESET_ALL}")

    elif sum(value == targetUsername for value in addressBook.values()) == 1:
        targetIp = list(addressBook.keys())[list(addressBook.values()).index(targetUsername)]

    # targetIp = input(f"{Fore.CYAN}IP of the receiver \n{Style.RESET_ALL}")
    # message = input(f"{Fore.CYAN}Message \n{Style.RESET_ALL}")
    send(targetIp,name=myName,ip=myIp,packetType=messageType,payload=message,logError=True)

def sender():
    global exitSignal
    while(not exitSignal):
        command = input(f"{Fore.CYAN}Enter a command or message\n{Style.RESET_ALL}")
        if command == "addressBook()":
            printAddressBook()
        elif command == "exit()":
            exitSignal = True
        # elif command == "message()":
        #     sendMessage()
        elif command == "discover()":
            sendBroadcast(discoverType,3)
        elif "; " in command:
            sendMessage(command.split("; ",1)[0],command.split("; ",1)[1])
        else:
            print(f"{Fore.RED}You did not enter a valid command \n{Style.RESET_ALL}")

def exitChat():
    global exitSignal
    exitSignal = True
    sendExitSignal()
    sendBroadcast(goodbyeType,3)

def main():
    tcpListenerThread = Thread(target=tcpListener)
    tcpListenerThread.start()
    udpListenerThread = Thread(target=udpListener)
    udpListenerThread.start()
    initializeClient()

    senderThread = Thread(target=sender)
    senderThread.start()
    senderThread.join()
    exitChat()
    tcpListenerThread.join()
    udpListenerThread.join()
    print(f"{Fore.MAGENTA}Bye! :){Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print('Interrupted')
        exitChat()

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)