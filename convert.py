from sqlite import sqlite

Sqlite = sqlite()
with open("kkutu_ko_not_ack_10000.txt") as fs:
    words = []
    for word in fs:
        words.append((word.replace('\n', ''), False))
    Sqlite.addWords(words)