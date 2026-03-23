import os
from cli.commands import run_cli


def reset_state_for_demo():
    """
    Remove previous crawler state so the demo always starts clean.
    This avoids duplicate URL errors when indexing the same seed URL again.
    """
    state_file = "data/state.json"
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
        except Exception:
            pass


if __name__ == "__main__":
    reset_state_for_demo()
    run_cli()