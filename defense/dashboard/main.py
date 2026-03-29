import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import tkinter as tk
from defense.dashboard.app import DefenseDashboard


def main():
    root = tk.Tk()
    DefenseDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
