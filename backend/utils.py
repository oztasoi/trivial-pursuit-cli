import json
import re
import os
from threading import Thread
import subprocess 
import socket
import time
from colorama import Fore, Style
import ntplib

C = ntplib.NTPClient()
OFFSET = C.request('europe.pool.ntp.org').offset

PRE_QUERY_DURATION = 2
QUESTION_DURATION = 10
POST_QUERY_DURATION = 1.5

PORT = 12345
SIZE = 1024

EXIT_SIGNAL = str.encode("EXIT_SIG")
START_SIGNAL = str.encode("START_SIG")

BROADCAST_IP = "25.255.255.255"

nameField = "NAME" #can be received from respond's payload
ipField = "MY_IP"
typeField = "TYPE"
payloadField = "PAYLOAD"
startPeriodField = "START_TIME"
endPeriodField = "END_TIME"
questionNumField = "QUESTION_NUM"

discoverType = "DISCOVER"       #sent by client
topicType = "TOPIC"             #sent by client
answerType = "ANSWER"           #sent by client

respondType = "RESPOND"         #sent by host
preTopicType = "PRE_TOPIC"      #sent by host
preQueryType = "PRE_QUERY"      #sent by host
postQueryType = "POST_QUERY"    #sent by host
queryResultType= "QUERY_RESULT" #sent by host

goodbyeType = "GOODBYE"

currQuestionNum = "question number"
currStartTime = "start time"
currEndTime = "end time"
currCorrectChoice = "correct choice"
currAnswers = "answers"

currentQuestion = {
    currQuestionNum : -1,
    currStartTime: -1,
    currEndTime: -1,
    currCorrectChoice: -1,
    currAnswers: {},
}

# testing w hamachi
# hamachiIpList = ["25.47.190.102","25.47.190.104", "25.43.1.132", ""]

def quizInspector():
    '''
    Retrieves the name of files in quizzes
    '''
    qlist = sorted([ f for f in os.listdir("../quizzes")], key=str.lower)
    return qlist

def ipRegex(ip):
    global BROADCAST_IP
    local_pat = re.compile("^192.168.[0-9]{1,3}.[0-9]{1,3}$")
    hamachi_pat = re.compile("^25.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}$")
    hamachi_match = hamachi_pat.match(ip)
    local_match = local_pat.match(ip)
    if hamachi_match is not None:
        BROADCAST_IP = "25.255.255.255"
        return
    if local_match is not None:
        ipFragments = local_match.group().split(".")
        BROADCAST_IP = ".".join(ipFragments[:3]) + ".255"
        return

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

def createJsonString(ip="",packetType="",payload="",questionNum=0):
    global currentQuestion
    packet = { 
        ipField: ip,
        typeField: packetType,
        payloadField: payload,
    }
    if packetType == preQueryType:
        start = time.time() + OFFSET + PRE_QUERY_DURATION
        currentQuestion[currStartTime] = start
        packet[startPeriodField] = start

        end = start + QUESTION_DURATION
        currentQuestion[currEndTime] = end
        packet[endPeriodField] = end

        packet[questionNumField] = questionNum
    elif packetType == answerType:
        packet[startPeriodField] = time.time() + OFFSET #this is the time that the question was answered
        packet[questionNumField] = questionNum


    return json.dumps(packet)

def send(targetIP,ip="",packetType="",payload="",questionNum=0,logError = False):
    #(TODO) type = bytes
    packet = str.encode(createJsonString(ip=ip, packetType=packetType, payload=payload, questionNum=questionNum))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:  
        for i in range(3):
            s.sendto(packet,(targetIP,PORT))

    if logError == True:
        print(f"{Fore.GREEN}Sending answer:{Style.RESET_ALL} {payload}") 

def sendSignal(signal,ip):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s: 
        #(TODO) BURADA SIKINTI VAR BENCE
        s.sendto(signal,(ip,PORT))   

def sendBroadcast(senderIp,broadcastType,count=1,payload="",questionNum=0):
    msg = str.encode(createJsonString(ip=senderIp, packetType=broadcastType, questionNum=questionNum,payload=payload))
    for _ in range(count):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('',0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

            s.sendto(msg,(BROADCAST_IP,PORT))
            #s.sendto(msg,('<broadcast>',PORT)) #(TODO) değiştir

            #broadcastIp = senderIp.rsplit(".",1)[0]+".255"
            #s.sendto(msg,(broadcastIp,PORT)) #(TODO) değiştir
