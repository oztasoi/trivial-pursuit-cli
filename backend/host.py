import json
import ntplib
from threading import Thread
import subprocess 
import os
import select
import sys
import socket
import html
import time
from colorama import Fore, Style
from random import randint, shuffle
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

players = {}
scoreboard = defaultdict(int)

myIp = "" 
gameCode = 0

exitSignal = False
startSignal = False

def updateScoreboard():
    #TODO should we check if the ip in the "answers" is in the "players" dict???
    #TODO how should we distribute points? 1st 3, 2nd 2, 2rd 1? TBD
    global scoreboard
    if len(currentQuestion[currAnswers]) == 0:
        return

    res = dict(sorted(currentQuestion[currAnswers].items(), key=lambda item: item[1])) #sort according to timestamp

    resKeys = list(res.keys())
    firstIp = resKeys[0]
    lastIp = resKeys[-1]
    if firstIp == lastIp:
        scoreboard[firstIp] = scoreboard.get(firstIp, 0) + 1000
        return
    firstTimestamp = float(res[firstIp])
    lastTimestamp = float(res[lastIp])
    difference = float(lastTimestamp) - float(firstTimestamp)
    for ip in res.keys():
        if ip in players:
            points = 400 + (1.0-(float(res[ip] - firstTimestamp) / difference)) * 600
            scoreboard[ip] =  scoreboard.get(ip, 0) + points
        else:
            return

def updateAndPrintScoreboard():
    global scoreboard

    updateScoreboard()
    scoreboard = dict(sorted(scoreboard.items(), key=lambda item: item[1], reverse=True)) #sort according to scores
    top3scoreboard = printScoreboard(scoreboard)
    return top3scoreboard

def printScoreboard(scoreboard):
    print(f"{Fore.YELLOW}Scoreboard")
    top3scoreboard = {}
    for i,item in enumerate(scoreboard.items(),1):
        if item[0] in players.keys():
            username = players[item[0]]
            score = item[1]
            print(f"{Fore.YELLOW}{i}\t{Fore.GREEN}{username}\t{score}{Style.RESET_ALL}")
            if i <= 3:
                top3scoreboard[i] = {"name": username, "score": score}
    return top3scoreboard

def waitForPlayers():
    
    while(not startSignal):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', PORT)) #(TODO) is that correct?
            s.setblocking(0)
            while not startSignal:
                result = select.select([s],[],[])
                msg = result[0][0].recv(SIZE).decode("utf-8")
                if msg:
                    if msg == START_SIGNAL:
                        return
                    try:
                        message = json.loads(msg)
                    except:
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
                result = select.select([s],[],[])
                msg = result[0][0].recv(SIZE)
                if msg:
                    if msg == EXIT_SIGNAL:
                        return
                    data = msg.decode("utf-8").strip().split('\n')
                    for datum in data:
                        try:
                            message = json.loads(datum)
                        except:
                            continue
                        consumeUdp(message)
                    break

def updateCurrentAnswers(message):
    global currentQuestion
    if ( 
        message[questionNumField] == currentQuestion[currQuestionNum] 
        and message[startPeriodField] <= currentQuestion[currEndTime] 
        and message[startPeriodField] > currentQuestion[currStartTime] 
        and int(message[payloadField]) == currentQuestion[currCorrectChoice]
        and message[ipField] not in currentQuestion[currAnswers]
    ):
        currentQuestion[currAnswers][message[ipField]] = message[startPeriodField]

def consumeUdp(message):
    if myIp == message[ipField]:
        pass
    elif typeField in message:
        if message[typeField] == discoverType: #valid in server
            senderIp = message[ipField]
            if senderIp in players:
                return
            username, code = message[payloadField].split("; ")
            if senderIp != myIp and code==str(gameCode):
                players[senderIp] = username
                print(f"{Fore.GREEN}Added ({message[ipField]}) {username} to the players list{Style.RESET_ALL}")    
                send(targetIP=senderIp,ip=myIp, packetType=respondType,payload=gameCode)
        elif message[typeField] == goodbyeType:
            #TODO what should we do if goodbye packet is received
            senderIp = message[ipField]
            if senderIp in players:
                players.pop(message[ipField],None)
                print(f"{Fore.RED}Deleted {message[ipField]} from players{Style.RESET_ALL}")
        elif message[typeField] == answerType:
            senderIp = message[ipField]
            if senderIp in currentQuestion[currAnswers]:
                return
            # print(f"{Fore.RED}Answer received{Style.RESET_ALL}")
            updateCurrentAnswers(message)
        else: 
            print(f"{Fore.RED}Unknown message type\n{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No type field in message (UDP)\n{Style.RESET_ALL}")

def configureGame():
    '''
    Here, the host will configure the quiz mode:
    One category or multiple categories
    '''

    quizStyleSet = set([1, 2, 3])

    print(f"{Fore.MAGENTA}Listing all quiz-modes: {Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t number \t quiz-mode{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}\t 1{Style.RESET_ALL} \t\t single")
    print(f"{Fore.YELLOW}\t 2{Style.RESET_ALL} \t\t multiple")
    print(f"{Fore.YELLOW}\t 3{Style.RESET_ALL} \t\t custom")

    quizStyle = int(input(f"{Fore.MAGENTA}Enter the quiz mode, single category or multiple categories: {Style.RESET_ALL}"))
    while quizStyle not in quizStyleSet:
        quizStyle = int(input(f"{Fore.MAGENTA}Invalid mode, re-enter quiz mode, either 1, 2 or 3: {Style.RESET_ALL}"))

    if quizStyle == 1:
        configureSingleCategoryGame()
    elif quizStyle == 2:
        configureMultipleCategoryGame()
    else:
        configureACustomGame()

def configureSingleCategoryGame():
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

def configureMultipleCategoryGame():
    '''
    Here, the host will configure the quiz
    list the categories using the api
    user chooses multiple categories
    user chooses number of questions
    user chooses difficulty
    returned questions are shuffled
    '''

    categoryIds = createQuiz.chooseMultipleCategory()
    quizQuestions = list()
    for categoryId in categoryIds:
        print(f"{Fore.MAGENTA}For category ID {categoryId}: {Style.RESET_ALL}")
        difficultyNum = createQuiz.chooseDifficulty()
        numOfQ = createQuiz.chooseNumOfQuestions(categoryId,difficultyNum)
        currentQuestions = createQuiz.getQuestions(categoryId,difficultyNum,numOfQ)
        quizQuestions += currentQuestions

    shuffle(quizQuestions)
    createQuiz.questions = quizQuestions

def configureACustomGame():
    '''
    Here, the host will upload a quiz from
    ./quizzes directory and selects it.
    '''

    selectedQuiz = createQuiz.chooseCustomQuiz()
    if not selectedQuiz:
        print(f"{Fore.MAGENTA}There's no custom made quizzes in your `quizzes` folder.\nCheck your folder{Style.RESET_ALL}")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    fin = open(f"../quizzes/{selectedQuiz}", "r")
    uploadedQuiz = json.load(fin)
    createQuiz.questions = uploadedQuiz

def initializeHost():
    global gameCode
    subprocess.run(["clear"])
    print(f"{Fore.MAGENTA}Welcome to Scio!")    
    print(f"Hello host! {Style.RESET_ALL}")  

    global myIp
    myIp = findIpList()
    ipRegex(myIp)

    configureGame()
    
    gameCode = randint(100000, 999999)
    print(f"{Fore.MAGENTA}Join the game using the game code: {Style.RESET_ALL} {gameCode} ")  

    waitForPlayersThread = Thread(target=waitForPlayers)
    waitForPlayersThread.start()

    cmd = ""
    while(not cmd=="start"):
        cmd = input(f"{Fore.MAGENTA}Type \"start\" when players are ready\n{Style.RESET_ALL}")
    
    startGame()
    waitForPlayersThread.join()

def play():
    subprocess.run(["clear"])
    print(f"{Fore.CYAN}Starting the game{Style.RESET_ALL}")
    for i,question in enumerate(createQuiz.questions,1):

        currentQuestion[currQuestionNum]=i
        currentQuestion[currAnswers]={}
        if exitSignal: #TODO this is meaningless, solve this issue!
            return

        subprocess.run(["clear"])
        print(f"{Fore.MAGENTA}Game Code: {gameCode}\n{Style.RESET_ALL}")

        print(f"{Fore.CYAN}Get ready for question {i}...{Style.RESET_ALL}")
        #broadcast PRE_QUERY packet
        sendBroadcast(myIp,preQueryType,3,questionNum=i)
        #PRE_QUERY period
        time.sleep(PRE_QUERY_DURATION)
        subprocess.run(["clear"])
        print(f"{Fore.MAGENTA}Game Code: {gameCode}\n{Style.RESET_ALL}")

        #QUESTION period
        print(f"{Fore.CYAN}Question {i} out of {len(createQuiz.questions)}\n{html.unescape(question['question'])}")
        choices = question['incorrect_answers']
        correctChoice = randint(0,3)
        currentQuestion[currCorrectChoice]=correctChoice #TODO
        choices.insert(correctChoice,question['correct_answer'])
        for j,choice in enumerate(choices):
            print(f"{Fore.YELLOW}{j} {Fore.CYAN}{html.unescape(choice)}{Style.RESET_ALL}")

        time.sleep(QUESTION_DURATION)
        subprocess.run(["clear"])
        print(f"{Fore.MAGENTA}Game Code: {gameCode}\n{Style.RESET_ALL}")


        print(f"{Fore.CYAN}Time's up...{Style.RESET_ALL}")
        
        #broadcast POST_QUERY packet
        print(f"{Fore.CYAN}Correct answer was {html.unescape(question['correct_answer'])}{Style.RESET_ALL}")
        
        top3scoreboard = updateAndPrintScoreboard()
        sendBroadcast(myIp,postQueryType,3,questionNum=i, payload=top3scoreboard)
        time.sleep(POST_QUERY_DURATION)

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
