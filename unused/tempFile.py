import random
import sqlite3
import time


def checkAnswer(question, ans):
    return int(ans) == eval(question)


def getAns(question):
    while True:
        try:
            userAns = input(f"What is: '{question}' ?")
            return userAns
        except ValueError:
            print('Please input an integer!')
            continue


def generateQuestion():
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    return f'{a} + {b}'


class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.startTime = time.time()

    def main(self):
        self.turns = 0
        self.score = 0
        while self.turns < 10:
            question = generateQuestion()
            userAns = getAns(question)
            ansState = checkAnswer(question, userAns)
            if ansState:
                self.score += 1

    def connectDatabase(self):
        self.connection = sqlite3.connect("C:/Users/Kurumi/Downloads/sqlite.db")
        self.cursor = self.connection.cursor()

    def disconnectDatabase(self):
        self.connection.close()

    def recordGame(self, playerID, score, duration):
        sqlQuery = '''
        INSERT INTO Game VALUES (Null, ?, ?, ?);
        '''

        self.connectDatabase()
        self.cursor.execute(sqlQuery, (playerID, score, duration))
        self.disconnectDatabase()


myData = Database()
myData.connectDatabase()
myData.disconnectDatabase()
