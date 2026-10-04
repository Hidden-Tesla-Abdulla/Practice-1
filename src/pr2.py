import os
import socket
import sys
import csv
import base64


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


hostname = socket.gethostname()
username = os.getlogin()

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


def conf_dump():
    if len(sys.argv) > 1:
        print(f"VFS = {sys.argv[1]}\n")
    if len(sys.argv) > 2:
        print(f"start_script = {sys.argv[2]}\n")


def repchik(array):
    path = array[0] if array else ""
    result = vfs.ls(path)
    if isinstance(result, str) and result.startswith("ls:"):
        print(result)
    else:
        print(" ".join(result))

def ls(array):
    print("LS", *array)

def cd(array):
    print("CD", *array)


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
        ls(perem)
    elif command == "cd":
        cd(perem)
    elif command == "rep":
        repchik(perem)
    elif command == "conf-dump":
        if len(array) > 1:
            print("Слишком много аргументов")
        else:
            conf_dump()
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
