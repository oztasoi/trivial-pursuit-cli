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
from inputimeout import inputimeout, TimeoutOccurred

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

nextStartTime = float("inf")
nextEndTime = float("inf")
currentQuestion = 0

def udpListener():
    while(myName== "" or myIp==""):
        pass
    
    while(not exitSignal):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', PORT)) 
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
    # print("CONSUMING MESSAGE",message)
    global hostIp, nextStartTime, nextEndTime, respondReceived, currentQuestion
    if myIp == message[ipField]:
        #print(f"{Fore.RED}Hearing echo\n{Style.RESET_ALL}")
        pass
    elif typeField in message:
        if message[typeField] == goodbyeType:
            senderIp = message[ipField]
            if senderIp==hostIp:
                sendSignal(EXIT_SIGNAL,myIp)
                try:
                    sys.exit(0)
                except SystemExit:
                    os._exit(0)
        elif message[typeField] == preQueryType:
            nextStartTime = message[startPeriodField]
            nextEndTime = message[endPeriodField]
            currentQuestion = message[questionNumField]
        elif message[typeField] == answerType:
            print(f"{Fore.RED}ANSWER received, somethings wrong\n{Style.RESET_ALL}")
        elif message[typeField] == respondType: #valid in client
            #TODO check this logic
            if hostIp == "" and message[payloadField]==int(gameCode): #is this correct?
                hostIp = message[ipField]
                respondReceived = True
        elif message[typeField] == postQueryType:
            currentScoreboard = message[payloadField]
            displayScoreboard(currentScoreboard)
    else:
        print(f"{Fore.RED}No type field in message (UDP)\n{Style.RESET_ALL}")

def displayScoreboard(currentScoreboard):
    print(f"{Fore.YELLOW}Scoreboard")
    for rank, userInfo in currentScoreboard.items():
        name = userInfo["name"]
        score = userInfo["score"]
        print(f"{Fore.YELLOW}{rank}\t{Fore.GREEN}{name}\t{score}{Style.RESET_ALL}")

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
    ipRegex(myIp)
    
def sendAnswer(message):
    global exitSignal
    if hostIp == "":
        #TODO this shouldnt ideally happen but if the host sends a goodbye packet, we can unset the hostIp and exit the game
        print(f"{Fore.RED}Couldn't find host{Style.RESET_ALL}")
        exitSignal = True

    send(hostIp,ip=myIp,packetType=answerType,payload=message,logError=True,questionNum=currentQuestion)

def sender():
    global exitSignal, gameCode

    while not respondReceived:
        gameCode = input(f"{Fore.CYAN}Enter the game code seen on the host screen\n{Style.RESET_ALL}")
        sendBroadcast(myIp,discoverType,3,f"{myName}; {gameCode}")
        time.sleep(2)

    while(not exitSignal):
        subprocess.run(["clear"])

        while(nextStartTime == float("inf")): pass
        q = currentQuestion

        now = time.time() + OFFSET
        time.sleep(nextStartTime-now)    
        try: 
            inputStr = inputimeout(prompt=f"{Fore.YELLOW}Question {currentQuestion}\n{Fore.CYAN}Enter an answer in range 0-3\n{Style.RESET_ALL}",timeout=QUESTION_DURATION)
        except:
            print("You didn't answer the question")
            inputStr = "NO ANSWER"

        if inputStr == "exit()":
            exitSignal = True
        elif inputStr == "NO ANSWER":
            pass
        else:
            try:
                inputInt = int(inputStr) # if one of 0,1,2,3 is entered, send ANSWER packet
            except:
                print(f"{Fore.RED}You did not enter a valid command \n{Style.RESET_ALL}")
                return

            if inputInt in range(4):
                sendAnswer(inputStr.strip()) 
            else:
                print(f"{Fore.RED}You did not enter a valid number \n{Style.RESET_ALL}")

        now = time.time() + OFFSET
        if(now<nextEndTime):
            time.sleep(nextEndTime-now)
        
        while(q==currentQuestion): pass

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