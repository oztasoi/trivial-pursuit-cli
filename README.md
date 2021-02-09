# CMPE 487 Final Project

## <span style="color:green">Made by Alkım Ece Toprak & Ibrahim Ozgurcan Oztas</span>

Welcome to our CLI-Based "Trivial Pursuit"-"Kahoot" combined game, Scio!
Here, you can have your friends play with you and challenge your knowledge with different sets of questions, even with your customized quizzes.
It is based as a CLI application, yet it has potential to evolve into an advanced form, which would have its GUI as a web application and a mobile app, and its backend as an opensource API.

## <span style="color:green">Challenges Encountered:</span>

### <span style="color:cyan">Network Time Synchronization between all participants</span>
- We've used a network timing protocol to synchronize all participants in the game, such as the host and all remaining players.
- Since many users can use many different date&time synchronization sources, thus we've found the actual offset of each participant and adjusted everyone in the session to be on the same page, approximately.

### <span style="color:cyan">Session</span>
- We know that there may be disconnections from the game, since network may have a strict bottleneck restriction for any interval, thus reconnection of any player to the ongoing session is essential. Therefore, we've implemented our packet systems to be able to reconnect if a player disconnects from the session.
- If host fails to provide session, all players will be dropped from the session. However, if a player disconnects, then they can reconnect via the game code and resume quizzing.

### <span style="color:cyan">Relative scoring system</span>
- We've collected each answer with its actual given response time to sort the received answers in an ascending order. Therefore, we've scaled our scoring of a player if one answers with correct answer.
- Each answer packet includes timestamps, which are the time indicators of the happening event. In this case, answering is an event and we keep its actual time and send it back to the host, which leads host to evaluate scores based on the lowest and highest timestamp.

Below, you can find how to run our CLI app.

## How to Run As Host:
- Pull the repository from our GitHub Page
    - `
    git clone https://github.com/oztasozgurcan/CMPE487FinalProject.git`

- Change directory into the project, then change directory into backend
    - `
    cd CMPE487FinalProject;
    python3 -m venv venv;
    ./venv/bin/activate;
    pip3 install -r requirements.txt;
    cd backend
    `

- To run as host, simply start host.py
    - `
    python3 host.py
    `

## How to Run as Client:
- Pull the repository from our GitHub Page
    - `
    git clone https://github.com/oztasozgurcan/CMPE487FinalProject.git
    `

- Change directory into the project, then change directory into backend
    - `
    cd CMPE487FinalProject;
    python3 -m venv venv;
    ./venv/bin/activate;
    pip3 install -r requirements.txt;
    cd backend
    `
- To run as client, simply start client.py
    - `
    python3 client.py
    `

## FAQ:
- How many quiz modes does the Scio have?
    - 3 quiz modes: single, multiple, custom

- How does custom quiz mode works?
    - Add your customized quiz as a JSON file into `quizzes` directory, then you are able to see them in your host session as options in quiz mode 3, custom.
    - Example quiz.json:
        ```json
        [
            {
                "category":"Art",
                "type":"multiple",
                "difficulty":"medium",
                "question":"Which time signature is commonly known as &ldquo;Cut Time?&rdquo;",
                "correct_answer":"2\/2",
                "incorrect_answers":[
                    "4\/4",
                    "6\/8",
                    "3\/4"
                ]
            },
            {
                "category":"Art",
                "type":"multiple",
                "difficulty":"easy",
                "question":"Who painted the Sistine Chapel?",
                "correct_answer":"Michelangelo",
                "incorrect_answers":[
                    "Leonardo da Vinci",
                    "Pablo Picasso",
                    "Raphael"
                ]
            }
            ]
        ```

- Does Scio support Hamachi Networks?
    - Yes, you can create your Hamachi network and add your friends, then you can select your IP as your Hamachi IP while playing.