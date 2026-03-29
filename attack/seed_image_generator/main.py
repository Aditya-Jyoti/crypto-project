import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import tkinter as tk
from attack.seed_image_generator.generator import GeneratorWindow
from attack.seed_image_generator.attacker import AttackerWindow


def main():
    shared = {
        "seed": None,
        "fingerprint": None,
        "generated": False,
        "on_generate": None,
    }

    root = tk.Tk()
    GeneratorWindow(root, shared)

    atk_root = tk.Toplevel(root)
    AttackerWindow(atk_root, shared)

    root.mainloop()


if __name__ == "__main__":
    main()
