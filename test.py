from sqlite import sqlite

Sqlite = sqlite()

words = [("딥지즑", False)]

hanbangWords = ["이리듐"]


Sqlite.addTuples(words)
#Sqlite.deleteWords(words)
# Sqlite.markHanbang(hanbangWords)