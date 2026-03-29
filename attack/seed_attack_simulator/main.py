import sys
import os

# Project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

import tkinter as tk

from attack.seed_attack_simulator.sender import SenderWindow
from attack.seed_attack_simulator.receiver import ReceiverWindow
from attack.seed_attack_simulator.attacker import AttackerWindow


def main():
    # Shared state between all three windows
    shared: dict = {
        "transmitted": False,
        "seed": None,
        "password": None,
        "key": None,
        "token": None,
        "numbers": [],
        "timestamp": None,
        "on_transmit": None,  # callback set by ReceiverWindow
    }

    sender_root = tk.Tk()
    receiver_root = tk.Toplevel(sender_root)
    attacker_root = tk.Toplevel(sender_root)

    SenderWindow(sender_root, shared)
    ReceiverWindow(receiver_root, shared)
    AttackerWindow(attacker_root, shared)

    sender_root.mainloop()


if __name__ == "__main__":
    main()
