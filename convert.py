from sqlite import sqlite

Sqlite = sqlite()
with open("kor_list.txt", encoding='utf-8') as fs:
    words = []
    for word in fs:
        words.append((word.replace('\n', ''), False))
    Sqlite.addWords(words)