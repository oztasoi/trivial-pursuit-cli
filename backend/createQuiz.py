from urllib.parse import unquote
import json
import urllib.request
import html
from colorama import Fore, Style

'''
Create questions using Trivia API ("https://opentdb.com/api_config.php")
'''

categoryList = []

difficulties = {
    1: "mixed",
    2: "easy",
    3: "medium",
    4: "hard"
}    

def getQuestions():
    defaultEncoded = "https://opentdb.com/api.php?amount=10"

    # createURL(,amount)

    response = urllib.request.urlopen(defaultEncoded)
    encoding = response.info().get_content_charset('utf-8')
    data = json.loads(response.read().decode(encoding))

    print(data)
    print(data["results"][-1]['question'])
    print(html.unescape(data["results"][-1]['question']))

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

    print(f"{Fore.MAGENTA}Number of questions available is {countList[key]}{Style.RESET_ALL}")
    return countList[key]

def printCategoryList():
    pass
