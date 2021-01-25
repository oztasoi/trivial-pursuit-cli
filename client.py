import json
import re
from threading import Thread
import subprocess 
import os
import select
import sys
import socket
import multiprocessing
import time
from colorama import Fore, Style
from random import randint
from bidict import bidict
from collections import defaultdict
from utils import *

'''
This is the script that the users will run
'''


'''
Every username must be unique (not so sure about this)
If username is not unique, the user will be prompted to change its username
Every game will have a random number (like Kahoot) and users will join the game using the number
If a user drops out of the game, he/she will be able to rejoin using that number
'''

exitSignal = False
respondReceived = False
myIp = "" 
hostIp = ""
myName = "" 
gameCode = 0    

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

def consumeUdp(message):
    print(message)
    global hostIp
    if typeField in message:
        if message[typeField] == goodbyeType:
            senderIp = message[ipField]
            if senderIp==hostIp:
                sendSignal(EXIT_SIGNAL,myIp)
        elif message[typeField] == messageType:
            print(f"{Fore.RED}Message/Respond UDP received\n{Style.RESET_ALL}")
        elif message[typeField] == respondType: #valid in client
            #TODO check this logic
            global respondReceived
            if hostIp == "" and message[payloadField]==gameCode: #is this correct?
                hostIp = message[ipField]
                respondReceived = True
    else:
        print(f"{Fore.RED}No type field in message (UDP)\n{Style.RESET_ALL}")

def initializeClient():
    global myName
    global gameCode
    subprocess.run(["clear"])
    print(f"{Fore.MAGENTA}Welcome to Scio!{Style.RESET_ALL}")    

    myName = input(f"{Fore.MAGENTA}Enter your username:\n{Style.RESET_ALL}")
    while (myName == ""):
        print(f"{Fore.RED}Username cannot be blank\n{Style.RESET_ALL}")
        myName = input(f"{Fore.MAGENTA}Enter your username:\n{Style.RESET_ALL}")

    print(f"{Fore.MAGENTA}Hello {myName}! {Style.RESET_ALL}")  

    global myIp
    myIp = findIpList()
    
def sendMessage(targetUsername, message):
    targetIp =""
    if targetUsername not in players.values():
        print(f"{Fore.RED}Username not in address book{Style.RESET_ALL}")
        return
    elif sum(value == targetUsername for value in players.values()) > 1:
        ipList = [k for k,v in players.items() if v == targetUsername]
        while targetIp not in ipList:
            targetIp = input(f"{Fore.CYAN}There are multiple IP's with the same username. Choose an IP from the list: " + ", ".join(ipList)+ f"\n{Style.RESET_ALL}")

    elif sum(value == targetUsername for value in players.values()) == 1:
        targetIp = list(players.keys())[list(players.values()).index(targetUsername)]

    # targetIp = input(f"{Fore.CYAN}IP of the receiver \n{Style.RESET_ALL}")
    # message = input(f"{Fore.CYAN}Message \n{Style.RESET_ALL}")
    send(targetIp,name=myName,ip=myIp,packetType=messageType,payload=message,logError=True)

def sender():
    global exitSignal
    global gameCode
    while not respondReceived:
        gameCode = input(f"{Fore.CYAN}Enter the game code seen on the host screen\n{Style.RESET_ALL}")
        sendBroadcast(myIp,discoverType,3,f"{myName}; {gameCode}")
        time.sleep(2)

    while(not exitSignal):
        command = input(f"{Fore.CYAN}Enter a command or message\n{Style.RESET_ALL}")
        if command == "addressBook()":
            printAddressBook()
        elif command == "exit()":
            exitSignal = True
        # elif command == "message()":
        #     sendMessage()
        elif command == "discover()":
            sendBroadcast(myIp,discoverType,3,f"{myName}; {gameCode}")
        elif "; " in command:
            sendMessage(command.split("; ",1)[0],command.split("; ",1)[1])
        else:
            print(f"{Fore.RED}You did not enter a valid command \n{Style.RESET_ALL}")

def exitGame():
    global exitSignal 
    exitSignal = True
    sendSignal(EXIT_SIGNAL,myIp)
    sendBroadcast(myIp,goodbyeType,3)

def main():
    udpListenerThread = Thread(target=udpListener)
    udpListenerThread.start()

    initializeClient()

    senderThread = Thread(target=sender)
    senderThread.start()
    senderThread.join()
    exitGame()

    udpListenerThread.join()
    print(f"{Fore.MAGENTA}Bye! :){Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print('Interrupted')
        exitGame()

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)