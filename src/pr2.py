import os
import socket
import sys

hostname = socket.gethostname()
username = os.getlogin() 

def check_errors(answer):
    array = answer.split()
    perem = []
    for i in array[1:]:
        perem.append(parser(i))
    if None in perem:
        return True
    return False


def conf_dump():
    if len(sys.argv) > 1:
        print(f"VFS = {sys.argv[1]}\n")
    if len(sys.argv) > 2:
        print(f"start_script = {sys.argv[2]}\n")

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

def work(answer):
    array = answer.split()
    perem = []
    for  i in array[1:]:
        perem.append(parser(i))
    if None in perem:
        print("ArgError")

    if array[0] == "ls":
        ls(perem)

    elif array[0] == "cd":
        cd(perem)

    elif array[0] == "conf-dump":
        if len(array) > 1:
            print("Слишком много аргументов")
        else:
            conf_dump()
    else:
        print("Такой команды нет")

flag = True

if len(sys.argv) > 2:
    if os.path.exists(sys.argv[2]):
        file = open(sys.argv[2])
        for i in file:
            print(i)
            if i.split()[0] == "exit":
                if len(i.split()) > 1:
                    print("Слишком много аргументов")
                else:
                    flag = False
                    break
            if check_errors(i):
                break
            if i.split()[0] == "#":
                continue
            work(i)
    else:
        print("Такого файла не существует\n")

while flag:
    answer_ = input(f"{username}@{hostname}:~$")
    if answer_.split()[0] == "exit":
        if len(answer_.split()) > 1:
            print("Слишком много аргументов")
        else:
            flag = False
            break
    work(answer_)
