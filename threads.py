import logging
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
from parser import parse_cea_output

class ParserThread(QThread):
    """Background thread"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            df = parse_cea_output(self.filepath, self.progress.emit)
            self.finished.emit(df)
        except Exception as e:
            logging.exception("Error parsing CEA output")
            self.error.emit(str(e))
