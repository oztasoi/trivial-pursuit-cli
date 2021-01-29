import json
import re
from threading import Thread
import subprocess 
import os
import select
import sys
import socket
import multiprocessing
import html
import time
from colorama import Fore, Style
from random import randint
from bidict import bidict
from collections import defaultdict 
from utils import *
import createQuiz 

'''
Every username must be unique
If username is not unique, the user will be prompted to change its username
Every game will have a random number (like Kahoot) and users will join the game using the number
If a user drops out of the game, he/she will be able to rejoin using that number
'''
currQuestionNum = "question number"
currStartTime = "start time"
currEndTime = "end time"
currCorrectChoice = "correct choice"
currAnswers = "answers"

currentQuestion = {
    currQuestionNum : -1,
    currStartTime: -1,
    currEndTime: -1,
    currCorrectChoice: -1
    currAnswers : {}
}

players = bidict()
scoreboard = defaultdict(lambda: 0)

myIp = "" 
gameCode = 0

exitSignal = False
startSignal = False

def printAddressBook():
    print(f"{Fore.CYAN}Address book:")
    for ip, username in players.items():
        print(f"{username} ({ip})")
    print(f"{Style.RESET_ALL}")    

def waitForPlayers():
    
    while(not startSignal):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', PORT)) #(TODO) is that correct?
            s.setblocking(0)
            while not startSignal:
                # print("Waiting for UDP")
                result = select.select([s],[],[])
                msg = result[0][0].recv(SIZE).decode("utf-8")
                if msg:
                    # print(msg)
                    if msg == START_SIGNAL:
                        # print( "Start signal received udp")
                        return

                    # print("Data received udp: ",data)
                    try:
                        message = json.loads(msg)
                    except:
                        # print(f"{Fore.RED}Wrong JSON format received:{Style.RESET_ALL} {datum}, bu kadar udp")
                        continue
                    consumeUdp(message)
                    break

def udpListener():
    while(myIp==""):
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
    if typeField in message:
        if message[typeField] == discoverType: #valid in server
            # addToAddressBook(message[ipField],message[nameField])
            senderIp = message[ipField]
            username, code = message[payloadField].split("; ")
            if senderIp != myIp and code==gameCode:
                players[senderIp] = username
                print(f"{Fore.GREEN}Added ({message[ipField]}) {username} to the players list{Style.RESET_ALL}")    
                send(targetIP=senderIp,ip=myIp, packetType=respondType,payload=gameCode)
        elif message[typeField] == goodbyeType:
            #TODO what should we do if goodbye packet is received
            players.pop(message[ipField],None)
        elif message[typeField] == answerType:
            print(f"{Fore.RED}Answer received\n{Style.RESET_ALL}")
            if message[questionNumField]==currentQuestion[currQuestionNum] and message[startPeriodField] <= currentQuestion[currEndTime] and message[startPeriodField] > currentQuestion[currStartTime]:
                currentQuestion[currAnswers][message[ipField]] = message[startPeriodField]

        else: 
            print(f"{Fore.RED}Unknown message type\n{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No type field in message (UDP)\n{Style.RESET_ALL}")

def configureGame():
    '''
    Here, the host will configure the quiz
    list the categories using the api
    user chooses category index
    user chooses number of questions
    user chooses difficulty
    '''
    categoryId = createQuiz.chooseCategory()
    difficultyNum = createQuiz.chooseDifficulty()
    numOfQ = createQuiz.chooseNumOfQuestions(categoryId,difficultyNum)

    createQuiz.getQuestions(categoryId,difficultyNum,numOfQ)

def initializeHost():
    global gameCode
    subprocess.run(["clear"])
    print(f"{Fore.MAGENTA}Welcome to Scio!")    

    print(f"Hello host! {Style.RESET_ALL}")  

    global myIp
    myIp = findIpList()

    configureGame()
    
    gameCode = randint(100000, 999999)
    print(f"{Fore.MAGENTA}Join the game using the game code: {Style.RESET_ALL} {gameCode} ")  

    waitForPlayersThread = Thread(target=waitForPlayers)
    waitForPlayersThread.start()

    cmd = ""
    while(not cmd=="start"):
        cmd = input(f"{Fore.MAGENTA}Type \"start\" when players are ready {Style.RESET_ALL}")  
    startGame()

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

def play():
    subprocess.run(["clear"]) 
    print(f"{Fore.CYAN}Starting the game{Style.RESET_ALL}")
    for i,question in enumerate(createQuiz.questions,1):
        currentQuestion[currQuestionNum]=i
        currentQuestion[currAnswers]={}
        if exitSignal: #TODO this is meaningless, solve this issue!
            return
        
        print(f"{Fore.CYAN}Get ready for question {i}...{Style.RESET_ALL}")
        #broadcast PRE_QUERY packet
        sendBroadcast(myIp,preQueryType,3,questionNum=i)
        #PRE_QUERY period
        time.sleep(PRE_QUERY_DURATION)
        subprocess.run(["clear"])
        print(time.time())

        #QUESTION period
        print(f"{Fore.CYAN}Question {i}\n{html.unescape(question['question'])}")
        choices = question['incorrect_answers']
        correctChoice = randint(0,3)
        currentQuestion[currCorrectChoice]=correctChoice
        choices.insert(correctChoice,question['correct_answer'])
        for j,choice in enumerate(choices):
            print(f"{Fore.YELLOW}{j} {Fore.CYAN}{html.unescape(choice)}{Style.RESET_ALL}")

        time.sleep(QUESTION_DURATION)
        subprocess.run(["clear"])
        print(time.time())

        print(f"{Fore.CYAN}Time's up...{Style.RESET_ALL}")
        #broadcast POST_QUERY packet
        time.sleep(POST_QUERY_DURATION)
        subprocess.run(["clear"])
        print(time.time())



        


def startGame():
    global startSignal
    startSignal = True
    sendSignal(START_SIGNAL,myIp)

def exitGame():
    global exitSignal 
    exitSignal = True
    sendSignal(EXIT_SIGNAL,myIp)
    sendBroadcast(myIp,goodbyeType,3)

def main():
    initializeHost()

    udpListenerThread = Thread(target=udpListener)
    udpListenerThread.start()

    # playThread = Thread(target=play)
    # playThread.start()
    # playThread.join()
    play()
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