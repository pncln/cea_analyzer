from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd

class PandasModel(QAbstractTableModel):
    """A Qt model to display a pandas DataFrame."""
    def __init__(self, df: pd.DataFrame = pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.copy()

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._df.columns[section]
            else:
                return section
        return None

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._df.iat[index.row(), index.column()])
        return None
