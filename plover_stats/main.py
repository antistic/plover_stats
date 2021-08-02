from plover.gui_qt.tool import Tool
from plover.engine import StenoEngine
from PyQt5 import QtCore, QtWidgets

from .stats_ui import Ui_Stats
from .stats_table_model import COLUMNS, StatsTableModel
from .utils import format_number

from .stats import get_stats


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal(tuple)
    progress = QtCore.pyqtSignal(int)

    def run(self) -> None:
        result = get_stats(update=self.progress.emit)
        self.finished.emit(result)


class Stats(Tool, Ui_Stats):
    TITLE = "Stats"
    ICON = ":/plover_stats/stats.svg"
    ROLE = "stats"

    def __init__(self, engine: StenoEngine) -> None:
        super().__init__(engine)
        self.setupUi(self)
        self.pages.setCurrentIndex(0)
        self.load_data()
        self.show()

    def load_data(self) -> None:
        self.thread = QtCore.QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.show_data)

        def on_progress(x):
            self.progress_bar.setMaximum(x)
            self.progress_bar.setValue(x)

        self.worker.progress.connect(on_progress)

        self.thread.start()

    def show_data(self, data) -> None:
        self.pages.setCurrentIndex(1)

        overview_stats, stats_by_day = data

        # populate overview screen
        stroke_count, translation_count, unique_days = overview_stats
        self.strokes_count.setText(format_number(stroke_count))
        self.translation_count.setText(format_number(translation_count))
        self.days.setText(format_number(unique_days))

        # set up table
        model = StatsTableModel()
        model.set_items_(list(stats_by_day.items()))
        self.day_table.setModel(model)
        self.day_table.resizeRowsToContents()
        self.day_table.resizeColumnsToContents()

        header = self.day_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        # header.sectionClicked.connect(self.day_table.resizeRowsToContents)
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.show_header_menu)

    def show_header_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu()
        header = self.day_table.horizontalHeader()
        for i, column in enumerate(COLUMNS):
            if column.name == "Date":
                continue
            action = menu.addAction(column.name)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(i))

            def on_toggle(checked: bool, i: int = i) -> None:
                if checked:
                    header.showSection(i)
                else:
                    header.hideSection(i)

            action.toggled.connect(on_toggle)

        menu.exec_(self.day_table.mapToGlobal(position))
