# CMPE 487 Final Project

Welcome to our CLI-Based "Trivial Pursuit"-"Kahoot" combined game, Scio!
Here, you can have your friends play with you and challenge your knowledge with different set of questions, even with your customized quizzes.
It is based as a CLI application, yet it has potential to evolve into an advanced form, which would have its GUI as a web application and a mobile app, and its backend as an opensource API.

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
- \+ How many quiz modes does the Scio have?
- -> 3 quiz modes: single, multiple, custom

- \+ How does custom quiz mode works?
- -> Add your customized quiz as a JSON file into `quizzes` directory, then you are able to see them in your host session as options in quiz mode 3, custom.
- Example quiz.json:
    - `[
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
]`

- \+ Does Scio support Hamachi Networks?
- -> Yes, you can create your Hamachi network and add your friends, then you can select your IP as your Hamachi IP while playing.