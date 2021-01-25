from urllib.parse import unquote
import json
import urllib.request
import html

'''
Create questions using Trivia API ("https://opentdb.com/api_config.php")
'''

class questionsAPI(): 
    base64encoded = "https://opentdb.com/api.php?amount=10&encode=base64"
    urlEncoded = "https://opentdb.com/api.php?amount=10&encode=url3986"
    defaultEncoded = "https://opentdb.com/api.php?amount=10"
    links = [base64encoded,urlEncoded,defaultEncoded]

    def __init__(self):

    # createURL(,amount)

    response = urllib.request.urlopen(defaultEncoded)
    encoding = response.info().get_content_charset('utf-8')
    data = json.loads(response.read().decode(encoding))

    print(data)
    print(data["results"][-1]['question'])
    print(html.unescape(data["results"][-1]['question']))

