import os
import socket

hostname = socket.gethostname()
username = os.getlogin() 

def ls(array):
    print("LS", *array)

def cd(array):
    print("CD", *array)

def parser(s):
    if s[0] == '$':
        if s[1:] in os.environ:
            return os.environ[s[1:].split()[0]]
        else:
            print("KeyError")
            return None
    return s

while True:
    answer = input(f"{username}@{hostname}:~$")
    array = answer.split()
    perem = []
    for i in array[1:]:
        perem.append(parser(i))
    if None in perem:
        print("ArgError")
        continue

    if array[0] == "ls":
        ls(perem)

    elif array[0] == "cd":
        cd(perem)

    elif array[0] == "exit":
        if len(array) > 1:
            print("Слишком много аргументов")
        else:
            break

    else:
        print("Такой команды нет")
