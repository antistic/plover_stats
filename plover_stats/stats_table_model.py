from typing import Any, Callable, List, NamedTuple
from PyQt5 import QtCore

from .utils import format_number


Column = NamedTuple(
    "Column",
    [
        ("name", str),
        ("value", Callable[[Any], Any]),
        ("sort_key", Callable[[Any], Any]),
    ],
)


COLUMNS: List[Column] = [
    Column(
        name="Date",
        value=lambda item: item[0],
        sort_key=lambda item: item[0],
    ),
    Column(
        name="Stroke Count",
        value=lambda item: format_number(item[1]["strokes"]),
        sort_key=lambda item: item[1]["strokes"],
    ),
    Column(
        name="Translation Count",
        value=lambda item: format_number(item[1]["translations"]),
        sort_key=lambda item: item[1]["translations"],
    ),
]


class StatsTableModel(QtCore.QAbstractTableModel):
    # pylint: disable=no-self-use
    def __init__(self, parent: QtCore.QObject = None) -> None:
        super().__init__(parent)
        self.items: List[Any] = []

    def set_items_(self, items: List[Any]) -> None:
        self.items = items
        self.sort(0, QtCore.Qt.DescendingOrder)

    def refresh_(self, item_index: int) -> None:
        self.dataChanged.emit(
            self.index(item_index, 0),
            self.index(item_index, self.columnCount()),
        )

    def rowCount(  # pylint: disable=invalid-name
        self, _index: QtCore.QModelIndex = None
    ) -> int:
        return len(self.items)

    def columnCount(  # pylint: disable=invalid-name
        self, _index: QtCore.QModelIndex = None
    ) -> int:
        return len(COLUMNS)

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:  # type: ignore
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        item = self.items[index.row()]

        return COLUMNS[index.column()].value(item)

    def headerData(  # type: ignore  # pylint: disable=invalid-name
        self, column: int, orientation: QtCore.Qt.Orientation, role: int
    ) -> Any:
        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return QtCore.QVariant()

        return COLUMNS[column].name

    def sort(
        self, column: int, order: QtCore.Qt.SortOrder = QtCore.Qt.AscendingOrder
    ) -> None:
        reverse = order == QtCore.Qt.AscendingOrder  # it's not intuitive I know
        self.items.sort(key=COLUMNS[column].sort_key, reverse=reverse)
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount(), self.columnCount()),
        )
