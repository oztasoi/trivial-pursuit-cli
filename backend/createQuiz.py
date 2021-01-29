import json
import urllib
import urllib.parse
import urllib.request
import html
import random
from colorama import Fore, Style

'''
Create questions using Trivia API ("https://opentdb.com/api_config.php")
'''

categoryList = []
questions = []

difficulties = {
    1: "mixed",
    2: "easy",
    3: "medium",
    4: "hard"
}    

def createUrl(categoryId,difficultyNum,numOfQ):
    url = "https://opentdb.com/api.php?"
    post_params = {
        'type' : 'multiple',
        'amount' : str(numOfQ),
        'category': str(categoryId)
    }
    if difficultyNum != 1:
        post_params['difficulty']=difficulties[difficultyNum]
    post_args = urllib.parse.urlencode(post_params)
    
    response = urllib.request.urlopen(url+post_args) #couldn't pass the parameters as 'data' here
    encoding = response.info().get_content_charset('utf-8')
    return json.loads(response.read().decode(encoding))

def getQuestions(categoryId,difficultyNum,numOfQ):
    global questions
    data = createUrl(categoryId,difficultyNum,numOfQ)

    if data["response_code"]!=0:
        raise ValueError(f"{Fore.RED}API call returned a response code of {data['response_code']}{Style.RESET_ALL}")

    questions=data["results"]
    print(f"{Fore.MAGENTA}Successfully retrieved the questions{Style.RESET_ALL}")
    # print(questions)

def listCategories():
    global categoryList
    response = urllib.request.urlopen("https://opentdb.com/api_category.php")
    encoding = response.info().get_content_charset('utf-8')
    categoryList = json.loads(response.read().decode(encoding))["trivia_categories"]
    
    print(f"{Fore.MAGENTA}\t id \t category name{Style.RESET_ALL}")
    for c in categoryList:
        print(f"{Fore.YELLOW}\t {c['id']}{Style.RESET_ALL}\t {c['name']}")
    
    return [x["id"] for x in categoryList]

def listDifficulties():
    print(f"{Fore.MAGENTA}\t number \t difficulty{Style.RESET_ALL}")
    for k,v in difficulties.items():
        print(f"{Fore.YELLOW}\t {k}{Style.RESET_ALL}\t {v}")


def listAvailableAmount(categoryId, difficulty):
    response = urllib.request.urlopen("https://opentdb.com/api_count.php?category="+str(categoryId))
    encoding = response.info().get_content_charset('utf-8')
    countList = json.loads(response.read().decode(encoding))["category_question_count"]
    
    key = "total_question_count"
    if difficulty != 1:
        key = "total_"+difficulties[difficulty]+"_question_count"

    print(f"{Fore.MAGENTA}Number of questions available: {Fore.MAGENTA}{countList[key]}{Style.RESET_ALL}")
    return countList[key]

def chooseCategory():
    print(f"{Fore.MAGENTA}Please choose and enter a category id from the following list:{Style.RESET_ALL}")    

    idList = listCategories()

    chosenCategory = int(input(f"{Fore.MAGENTA}Please enter an id: {Style.RESET_ALL}"))
    while chosenCategory not in idList:
        print(chosenCategory)
        chosenCategory = int(input(f"{Fore.MAGENTA}Chosen id is not valid, please enter a valid id: {Style.RESET_ALL}"))
    return chosenCategory

def chooseDifficulty():
    print(f"{Fore.MAGENTA}Please choose and enter a difficulty number from the following list:{Style.RESET_ALL}")

    listDifficulties()

    chosenDifficulty = int(input(f"{Fore.MAGENTA}Please enter a difficulty number: {Style.RESET_ALL}"))
    while chosenDifficulty not in difficulties:
        chosenDifficulty = int(input(f"{Fore.MAGENTA}Chosen number is not valid, please enter a valid difficulty number: {Style.RESET_ALL}"))
    return chosenDifficulty

def chooseNumOfQuestions(categoryId,difficultyNum):
    maxNum =listAvailableAmount(categoryId,difficultyNum)

    chosenNum = int(input(f"{Fore.MAGENTA}Please enter how many questions you want to be asked: {Style.RESET_ALL}"))
    while chosenNum not in range(1,maxNum):
        chosenNum = int(input(f"{Fore.MAGENTA}Chosen number is not valid, please enter how many questions you want to be asked: {Style.RESET_ALL}"))
    return chosenNum

def printCategoryList():
    pass


# getQuestions(22,2,10)