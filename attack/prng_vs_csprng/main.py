import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import tkinter as tk
from attack.prng_vs_csprng.generator import GeneratorWindow
from attack.prng_vs_csprng.predictor import PredictorWindow


def main():
    shared = {
        "mode": "prng",
        "seed": 42,
        "outputs": [],
        "latest": None,
        "threshold": 10,  # outputs needed before prediction is allowed
        "pending_prediction": None,
        "on_emit": None,
        "on_reset": None,
    }

    root = tk.Tk()
    GeneratorWindow(root, shared)

    pred_root = tk.Toplevel(root)
    PredictorWindow(pred_root, shared)

    root.mainloop()


if __name__ == "__main__":
    main()
