import os
import tkinter as tk
from tkinter import scrolledtext


class ShellEmulator:
    def __init__(self, master, vfs_name="default_vfs"):
        self.master = master
        self.vfs_name = vfs_name
        self.master.title(f"Эмулятор - [{self.vfs_name}]")

        # === Терминальный стиль ===
        self.master.configure(bg="#000000")
        self.master.geometry("900x500")
        self.master.resizable(True, True)

        # Настраиваем сетку
        self.master.grid_rowconfigure(0, weight=1)  # текст растягивается
        self.master.grid_rowconfigure(1, weight=0)  # строка ввода фиксирована
        self.master.grid_columnconfigure(0, weight=1)

        # === Окно вывода ===
        self.text = scrolledtext.ScrolledText(
            master,
            wrap=tk.WORD,
            bg="#000000",
            fg="#00FF00",
            insertbackground="white",
            font=("Menlo", 12),
            state="disabled"
        )
        self.text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # === Поле ввода ===
        self.entry = tk.Entry(
            master,
            bg="#000000",
            fg="#00FF00",
            insertbackground="white",
            font=("Menlo", 12),
            relief=tk.FLAT
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.entry.bind("<Return>", self.handle_command)
        self.entry.focus()

        self.log("Эмулятор запущен. Введите команду (ls, cd, exit):")

    def log(self, msg: str):
        """Вывод текста в терминал"""
        self.text.configure(state="normal")
        self.text.insert(tk.END, msg + "\n")
        self.text.configure(state="disabled")
        self.text.see(tk.END)

    def handle_command(self, _):
        """Обработка команд"""
        line = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not line:
            return

        # Раскрытие переменных окружения ($HOME и т.п.)
        line = os.path.expandvars(line)
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]

        self.log(f"> {line}")

        # Команды-заглушки
        if cmd == "ls":
            self.log(f"Выполнена команда ls, аргументы: {args}")
        elif cmd == "cd":
            self.log(f"Выполнена команда cd, аргументы: {args}")
        elif cmd == "exit":
            self.log("Выход из эмулятора.")
            self.master.quit()
        else:
            self.log(f"Ошибка: неизвестная команда '{cmd}'")


if __name__ == "__main__":
    root = tk.Tk()
    app = ShellEmulator(root)
    root.mainloop()
