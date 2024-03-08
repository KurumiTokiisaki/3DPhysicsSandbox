import sqlite3


class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connectDatabase(self):
        self.connection = sqlite3.connect("C:/Users/Kurumi/Downloads/sqlite.db")
        self.cursor = self.connection.cursor()

    def disconnectDatabase(self):
        self.connection.close()


myData = Database()
myData.connectDatabase()
myData.disconnectDatabase()
