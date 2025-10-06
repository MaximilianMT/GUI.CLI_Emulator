import os
import sys
import tkinter as tk
from tkinter import scrolledtext
import xml.etree.ElementTree as ET


class ShellEmulator:
    def __init__(self, master, vfs_path=None, script_path=None):
        self.master = master
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs_name = os.path.basename(vfs_path) if vfs_path else "default_vfs"

        # Настройка окна
        self.master.title(f"Эмулятор - [{self.vfs_name}]")
        self.master.geometry("900x500")
        self.master.configure(bg="#000000")

        # Размещение через grid
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)

        # Окно вывода
        self.text = scrolledtext.ScrolledText(
            master, wrap=tk.WORD, bg="#000000", fg="#00FF00",
            insertbackground="white", font=("Menlo", 12), state="disabled"
        )
        self.text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Поле ввода
        self.entry = tk.Entry(
            master, bg="#000000", fg="#00FF00", insertbackground="white",
            font=("Menlo", 12), relief=tk.FLAT
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.entry.bind("<Return>", self.handle_command)
        self.entry.focus()

        # Инициализация
        self.log(f"Эмулятор запущен. Имя VFS: {self.vfs_name}")
        self.vfs = self.load_vfs(vfs_path)
        if script_path:
            self.run_script(script_path)

    # === Вывод текста в терминал ===
    def log(self, msg):
        self.text.configure(state="normal")
        self.text.insert(tk.END, msg + "\n")
        self.text.configure(state="disabled")
        self.text.see(tk.END)

    # === Обработка ввода пользователя ===
    def handle_command(self, _):
        line = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not line:
            return
        self.execute_line(line)

    # === Выполнение одной строки ===
    def execute_line(self, line):
        line = os.path.expandvars(line)
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]
        self.log(f"> {line}")

        if cmd == "ls":
            self.log("file1.txt  dirA  dirB")
        elif cmd == "cd":
            self.log(f"Переход в каталог: {args if args else '/'}")
        elif cmd == "exit":
            self.log("Выход из эмулятора.")
            self.master.quit()
        elif cmd == "echo":
            if args and args[0] == "$HOME":
                self.log(os.path.expandvars("$HOME"))
            else:
                self.log(" ".join(args))
        else:
            self.log(f"Ошибка: неизвестная команда '{cmd}'")

    # === Загрузка VFS ===
    def load_vfs(self, path):
        if not path:
            self.log("Создана виртуальная файловая система по умолчанию.")
            return {"root": []}
        try:
            tree = ET.parse(path)
            self.log(f"VFS '{path}' успешно загружена.")
            return tree.getroot()
        except Exception as e:
            self.log(f"Ошибка загрузки VFS: {e}")
            return {"root": []}

    # === Выполнение стартового скрипта ===
    def run_script(self, script_path):
        self.log(f"Выполнение стартового скрипта: {script_path}")
        try:
            with open(script_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Показать команду и результат
                    self.execute_line(line)
        except Exception as e:
            self.log(f"Ошибка выполнения скрипта: {e}")


# === Точка входа ===
if __name__ == "__main__":
    vfs_path = sys.argv[1] if len(sys.argv) > 1 else None
    script_path = sys.argv[2] if len(sys.argv) > 2 else None

    print("Отладочная информация:")
    print(f"  Путь к VFS: {vfs_path}")
    print(f"  Путь к стартовому скрипту: {script_path}")

    root = tk.Tk()
    app = ShellEmulator(root, vfs_path, script_path)
    root.mainloop()
