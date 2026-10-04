import os
import socket
import sys
import csv
import base64
import getpass


class VFSNode:

    def __init__(self, name, node_type='dir', parent=None):
        self.name = name
        self.type = node_type  # 'dir' или 'file'
        self.parent = parent  # Ссылка на родителя для навигации '..'
        self.children = {}  # Словарь {имя_дочки: VFSNode} для директорий
        self.content = b''  # Байтовое содержимое для файлов


class VirtualFileSystem:

    def __init__(self):
        self.root = VFSNode('/', 'dir')
        self.cwd = self.root  # Текущая рабочая директория

    def load_from_csv(self, filepath):
        if not os.path.exists(filepath):
            print(f"Ошибка загрузки VFS: Файл '{filepath}' не найден.")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)

                if not headers or len(headers) < 2:
                    print("Ошибка загрузки VFS: Неверный формат CSV (ожидается path,type,data).")
                    return False

                for row_num, row in enumerate(reader, start=2):
                    if len(row) < 2:
                        continue

                    path = row[0].strip()
                    node_type = row[1].strip().lower()
                    data = row[2].strip() if len(row) > 2 else ""

                    if not path.startswith('/'):
                        print(f"Ошибка загрузки VFS (строка {row_num}): Путь '{path}' должен быть абсолютным.")
                        return False

                    if node_type not in ('dir', 'file'):
                        print(f"Ошибка загрузки VFS (строка {row_num}): Неверный тип узла '{node_type}'.")
                        return False

                    self._add_node(path, node_type, data, row_num)

            return True

        except csv.Error as e:
            print(f"Ошибка загрузки VFS: Ошибка синтаксиса CSV ({e}).")
            return False
        except Exception as e:
            print(f"Ошибка загрузки VFS: Непредвиденная ошибка чтения ({e}).")
            return False

    def _add_node(self, path, node_type, data, row_num):
        parts = [p for p in path.split('/') if p]
        current = self.root

        for k, part in enumerate(parts):
            is_last = (k == len(parts) - 1)

            if part not in current.children:
                if is_last:
                    new_node = VFSNode(part, node_type, parent=current)
                    if node_type == 'file':
                        try:
                            new_node.content = base64.b64decode(data) if data else b''
                        except Exception:
                            print(
                                f"Ошибка загрузки VFS (строка {row_num}): Не удалось декодировать base64 для '{path}'.")
                            return
                    current.children[part] = new_node
                else:
                    current.children[part] = VFSNode(part, 'dir', parent=current)

            current = current.children[part]

            if not is_last and current.type != 'dir':
                print(f"Ошибка загрузки VFS (строка {row_num}): Конфликт путей, '{part}' является файлом.")
                return

    def resolve_path(self, path_str):
        if not path_str:
            return self.cwd

        if path_str.startswith('/'):
            current = self.root
            parts = path_str.split('/')[1:]
        else:
            current = self.cwd
            parts = path_str.split('/')

        for part in parts:
            if not part or part == '.':
                continue
            elif part == '..':
                if current.parent:
                    current = current.parent
            else:
                if current.type == 'dir' and part in current.children:
                    current = current.children[part]
                else:
                    return None  # Путь не найден
        return current

    def ls(self, path_str=""):
        target = self.resolve_path(path_str)
        if not target:
            return f"ls: cannot access '{path_str}': No such file or directory"
        if target.type != 'dir':
            return target.name
        return list(target.children.keys())

    def cd(self, path_str):
        if not path_str:
            self.cwd = self.root
            return True

        target = self.resolve_path(path_str)
        if not target:
            print(f"cd: {path_str}: No such file or directory")
            return False
        if target.type != 'dir':
            print(f"cd: {path_str}: Not a directory")
            return False

        self.cwd = target
        return True

    def find(self, path, param, critea):
        current = self.resolve_path(path)
        result = list()
        if not current:
            print(f"find: cannot access '{path}': No such file or directory")
            return
        if critea.startswith("*") and param == "-name":
            for child in current.children:
                if current.children[child].type == "file" and child.endswith(critea[1:]):
                    result.append(f"file_name: {child} -> path: {path[1:]}")
                elif current.children[child].type == "dir":
                    new_path = path  + "/" + child
                    res = self.find(new_path, param, critea)
                    if len(res) > 0:
                        for el in res:
                            result.append(el)
        elif param == "type" and critea in ["dir", "file"]:
            for child in current.children:
                if current.children[child].type == critea:
                    if len(path[1:]) > 0:
                        result.append(f"{critea}_name: {child} -> path: {path[1:]}")
                    else:
                        result.append(f"{critea}_name: {child} -> path: {path}")
                if current.children[child].type == "dir":
                    new_path = path  + "/" + child
                    res = self.find(new_path, param, critea)
                    if len(res) > 0:
                        for el in res:
                            result.append(el)
        return result

    def pwd(self):
        current = self.cwd
        path = current.name
        while current.parent != None:
            current = current.parent
            path = current.name + "/" + path
        return path[1:]


command_history = []
hostname = socket.gethostname()
try:
    username = os.getlogin()
except:
    username = getpass.getuser()

# Инициализация VFS
vfs = VirtualFileSystem()
if len(sys.argv) > 1:
    vfs.load_from_csv(sys.argv[1])

def parser(s):
    if not s:
        return s
    if s[0] == '$':
        var_name = s[1:].split()[0]
        if var_name in os.environ:
            return os.environ[var_name]
        else:
            print("KeyError")
            return None
    return s


def check_errors(answer):
    array = answer.split()
    perem = []
    for el in array[1:]:
        perem.append(parser(el))
    return None in perem

def add_history(command, result):
    command_history.append(f"{command}: {result}")

def conf_dump():
    if len(sys.argv) > 1:
        print(f"VFS = {sys.argv[1]}\n")
        add_history("conf_dump: ", " ".join(sys.argv))
    elif len(sys.argv) > 2:
        add_history("conf_dump: ", " ".join(sys.argv))
        print(f"start_script = {sys.argv[2]}\n")
    else:
        add_history("conf_dump: ", " ".join(sys.argv))


def ls(array):
    path = array[0] if array else ""
    result = vfs.ls(path)
    if isinstance(result, str) and result.startswith("ls:"):
        add_history("ls", result)
        print(result)
    else:
        add_history("ls", " ".join(result))
        print(" ".join(result))


def cd(array):
    add_history(f"cd {array}", "")
    path = array[0] if array else ""
    vfs.cd(path)


def work(answer):
    answer = answer.strip()
    if not answer:
        return

    array = answer.split()
    perem = []
    for ele in array[1:]:
        perem.append(parser(ele))

    if None in perem:
        print("ArgError")
        return

    command = array[0]
    if command == "ls":
        if len(perem) > 1:
            print("ArgError")
        else:
            ls(perem)
    elif command == "cd":
        if len(perem) > 1:
            print("ArgError")
        else:
            cd(perem)
    elif command == "conf-dump":
        if len(array) > 1:
            print("ArgError")
        else:
            conf_dump()
    elif command == "history":
        if len(perem) > 1:
            print("ArgError")
        else:
            for i in command_history:
                print(i)
    elif command == "find":
        if len(perem) != 3:
            print("ArgError")
        else:
            add_history("find", "\n      ".join(vfs.find(perem[0], perem[1], perem[2])))
            for i in vfs.find(perem[0], perem[1], perem[2]):
                print(i)
    elif command == "pwd":
        if len(perem) > 0:
            print("ArgError")
        else:
            add_history("pwd", vfs.pwd())
            print(vfs.pwd())
    else:
        print("Такой команды нет")


flag = True

if len(sys.argv) > 2:
    if os.path.exists(sys.argv[2]):
        with open(sys.argv[2], 'r') as file:
            for line in file:
                i = line.strip()
                if not i:
                    continue

                print(i)
                cmd = i.split()[0]

                if cmd == "exit":
                    if len(i.split()) > 1:
                        print("Слишком много аргументов")
                    else:
                        flag = False
                        break

                if check_errors(i):
                    break

                if cmd == "#":
                    continue

                work(i)
    else:
        print("Такого файла не существует\n")

while flag:
    answer_ = input(f"{username}@{hostname}:~$ ")

    if answer_.split()[0] == "exit":
        if len(answer_.split()) > 1:
            print("Слишком много аргументов")
        else:
            flag = False
            break
    else:
        work(answer_)
