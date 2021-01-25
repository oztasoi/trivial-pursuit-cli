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

PORT = 12345
SIZE = 1024

EXIT_SIGNAL = str.encode("EXIT_SIG")
START_SIGNAL = str.encode("START_SIG")

nameField = "NAME" #can be received from respond's payload
ipField = "MY_IP"
typeField = "TYPE"
payloadField = "PAYLOAD"
startPeriodField = "START_TIME"
endPeriodField = "END_TIME"

discoverType = "DISCOVER"
goodbyeType = "GOODBYE"
respondType = "RESPOND"
messageType = "MESSAGE"

# testing w hamachi
# hamachiIpList = ["25.47.190.102","25.47.190.104", "25.43.1.132", ""]

def searchForIp(string):
    regexp ='(?<=inet )192.\d+.\d+.\d+'
    return re.findall(regexp,string)

def searchForHamachiIp(string):
    regexp ='(?<=inet )25.\d+.\d+.\d+'
    # regexp ='(?<=inet )\d+.\d+.\d+.\d+'
    return re.findall(regexp,string)

def findIpList():
    ip = ""
    ifconfig = subprocess.run("ifconfig",stdout=subprocess.PIPE,text=True,stderr=subprocess.PIPE )
    
    l1 = searchForIp(ifconfig.stdout)
    l2 = searchForHamachiIp(ifconfig.stdout)
    finalList = l1 + l2
    if len(finalList) == 1:
        ip = finalList[0]
        print(f"{Fore.MAGENTA}Your IP address is", ip, f"{Style.RESET_ALL}")
    elif len(finalList) > 1:
        chosen = False
        while not chosen:
            chosenIp = input(f"{Fore.MAGENTA}Choose an IP from the list: " + ", ".join(finalList)+ f"\n{Style.RESET_ALL}")
            if chosenIp not in finalList:
                print(f"{Fore.MAGENTA}Chosen IP is not in the list{Style.RESET_ALL}")
            else:
                ip = chosenIp
                print(f"{Fore.MAGENTA}Your IP address is", ip, f"{Style.RESET_ALL}")
                chosen=True
    else:
        print(f"{Fore.MAGENTA}Your IP address is", ip, f"{Style.RESET_ALL}")
    return ip

def createJsonString(ip="",packetType="",payload=""):
    return json.dumps({ 
        ipField: ip,
        typeField: packetType,
        payloadField: payload,
    }) + "\n"

def send(targetIP,ip="",packetType="",payload="",logError = False):
    #(TODO) type = bytes
    packet = str.encode(createJsonString(ip=ip, packetType=packetType, payload=payload))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:  
        # print(f"Sending {packet} to {targetIP}")

        for i in range(3):
            s.sendto(packet,(targetIP,PORT))

    if logError == True:        
        print(f"{Fore.GREEN}Message to {targetIP} :{Style.RESET_ALL} {payload}") 

def sendSignal(signal,ip):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: 
        #(TODO) BURADA SIKINTI VAR BENCE 
        # s.bind(('',PORT))
        # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        s.sendto(signal,(ip,PORT))   

def sendBroadcast(senderIp,broadcastType,count=1,payload=""):
    print(f"{Fore.MAGENTA}Sending {broadcastType}{Style.RESET_ALL}")

    for _ in range(count):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('',0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
            msg = str.encode(createJsonString(ip=senderIp, packetType=broadcastType, payload=payload))

            # s.sendto(msg,('25.255.255.255',PORT))
            broadcastIp = senderIp.rsplit(".",1)[0]+".255"
            # s.sendto(msg,('<broadcast>',PORT)) #(TODO) değiştir
            s.sendto(msg,(broadcastIp,PORT)) #(TODO) değiştir
            # print("sending discover", msg)