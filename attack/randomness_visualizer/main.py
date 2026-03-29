import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import tkinter as tk
from attack.randomness_visualizer.app import RandomnessVisualizer


def main():
    root = tk.Tk()
    RandomnessVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
