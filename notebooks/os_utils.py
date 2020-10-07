"""Utility to get around type checking of windows specific methods."""
# type: ignore
import os

IS_WIN = os.name == "nt"

if IS_WIN:

    def startfile(path):
        """Open a file using default app, or explorer.exe for directory paths."""
        os.startfile(path)  # nosec: B606


else:

    def startfile(path):
        """Do nothing, we aren't on windows."""
        pass
