from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableView,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QStyle,
    QDialog,
    QSpinBox,
)
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis
from PyQt6 import QtCore
from db import Income as IncomeTable
import datetime
from peewee import fn
from calendar import monthrange
import ctypes
from helpers.const import Vietnamese


headers = [
    'ID',
    Vietnamese.CONTENT.value,
    Vietnamese.DATE.value,
    Vietnamese.AMOUNT_OF_MONEY.value,
]


class Form(QDialog):

    def __init__(self, parent=None, month=1, year=datetime.date.today().year, edit=False, id=None):
        self.month = month
        self.year = year
        self.updated = False
        self.id = id

        super(Form, self).__init__(parent)
        form_layout = QFormLayout()

        name_label = QLabel(Vietnamese.CONTENT.value)
        self.name_input = QLineEdit()

        form_layout.addRow(name_label, self.name_input)

        amount_label = QLabel(Vietnamese.AMOUNT_OF_MONEY.value)
        validator = QIntValidator(0, 2147483647)
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(validator)

        form_layout.addRow(amount_label, self.amount_input)

        date_label = QLabel(Vietnamese.DATE.value)
        self.date_input = QSpinBox()
        self.date_input.setMinimum(1)
        self.date_input.setMaximum(monthrange(self.year, self.month)[1])

        today = datetime.date.today()
        if today.month == month:
            self.date_input.setValue(today.day)

        form_layout.addRow(date_label, self.date_input)

        submit_button = QPushButton(Vietnamese.SAVE.value)
    
        cancel_button = QPushButton(Vietnamese.CANCEL.value)
        cancel_button.clicked.connect(self.close)

        form_layout.addRow(submit_button, cancel_button)

        self.setLayout(form_layout)

        if not edit:
            submit_button.clicked.connect(self.insert)
            self.setWindowTitle(Vietnamese.ADD_INCOME.value)
        else:
            submit_button.clicked.connect(self.update)
            self.setWindowTitle(Vietnamese.EDIT_INCOME.value)

    def validated(self):
        conditions = [
            self.name_input.text().strip() != '',
            self.amount_input.text().strip() != '',
            self.amount_input.text().isdigit(),
        ]

        return not False in conditions

    
    def insert(self):
        if self.validated():
            data = IncomeTable()
            data.name = self.name_input.text()
            data.amount_of_money = int(self.amount_input.text())
            data.date = datetime.date(self.year, self.month, int(self.date_input.value()))
            data.save()

            self.updated = True
            self.close()

    def update(self):
        if self.validated():
            q = (
                IncomeTable.update({
                    IncomeTable.name: self.name_input.text(),
                    IncomeTable.amount_of_money: int(self.amount_input.text()),
                    IncomeTable.date: datetime.date(self.year, self.month, int(self.date_input.value()))
                }).where(
                    IncomeTable.id == self.id
                )
            )
            q.execute()
            self.updated = True
            self.close()
            

class IncomeScreen(QWidget):

    def __init__(self, month, year):
        super().__init__()
        self.month = month
        self.year = year
        self.initUI()
        self.loadData()
        self.loadDataSummary()

    def initUI(self):
        user32 = ctypes.windll.user32

        desktop_width = user32.GetSystemMetrics(0)
        desktop_height = user32.GetSystemMetrics(1)

        width = int(desktop_width)
        height = int(desktop_height)

        self.resize(width, height)

        self.showMaximized()

        vbox1 = QVBoxLayout()

        label = QLabel(f'{Vietnamese.MONTH.value} {self.month}, {Vietnamese.YEAR.value} {self.year}')
        font = QFont('Times', 15)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        vbox1.addWidget(label)
        vbox1.addSpacing(15)

        hbox1 = QHBoxLayout()
        back_button = QPushButton()
        back_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        )
        back_button.clicked.connect(self.backButtonClicked)

        hbox1.addWidget(back_button)

        hbox1.addStretch()

        add_button = QPushButton(Vietnamese.ADD.value)
        add_button.clicked.connect(self.addButtonClicked)

        hbox1.addWidget(add_button)
        vbox1.addLayout(hbox1)
        vbox1.addSpacing(15)

        self.table = self.createTableView()

        vbox1.addWidget(self.table)

        hbox2 = QHBoxLayout()
        
        self.summaryTable = self.createTableSummary()
        
        hbox2.addWidget(self.summaryTable)
        hbox2.addStretch()

        self.chartView = QChartView()
        self.chartView.setMaximumHeight(desktop_height * 0.278)
        hbox2.addWidget(self.chartView)

        vbox1.addLayout(hbox2)

        self.setLayout(vbox1)
        self.setWindowTitle(Vietnamese.INCOME_SECTION.value)
        self.show()

    def createTableView(self):
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setRowCount(10)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.cellDoubleClicked.connect(self.cellClicked)
        return table

    
    def createTableSummary(self):
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setRowCount(1)
        table.setColumnCount(3)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(70)
        return table


    def loadData(self):
        from_date = datetime.date(self.year, self.month, 1)
        to_date = datetime.date(self.year + int(self.month/12), self.month % 12 + 1, 1) - datetime.timedelta(days=1)

        data = IncomeTable.select().where(
            IncomeTable.date >= from_date,
            IncomeTable.date <= to_date
        ).order_by(IncomeTable.date)

        self.table.clearContents()
        row_count = data.count() if data.count() > 0 else 10
        self.table.setRowCount(row_count + 1)

        center_item = QTableWidgetItem()
        center_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        total = 0

        for index, record in enumerate(data):
            data = [
                str(record.id),
                str(record.name),
                record.date.strftime('%d/%m/%Y'),
                "{:,} VNĐ".format(record.amount_of_money),
            ]

            total += record.amount_of_money

            column = 0
            for value in data:
                item = center_item.clone()
                item.setText(value)

                self.table.setItem(index, column, item)
                column += 1

        total_data = [
            '',
            Vietnamese.TOTAL.value.upper(),
            '',
            "{:,} VNĐ".format(total),
        ]

        column = 0
        for value in total_data:
            item = center_item.clone()

            font = QFont()
            font.setBold(True)

            item.setFont(font)
            item.setText(value)

            self.table.setItem(row_count, column, item)
            column += 1


    def loadDataSummary(self):
        from_date = datetime.date(self.year, self.month, 1)
        to_date = datetime.date(self.year + int(self.month/12), self.month % 12 + 1, 1) - datetime.timedelta(days=1)

        headers = []
        data = []

        for _ in range(3):
            headers.insert(0, f'{to_date.month}/{to_date.year}')

            amount = IncomeTable.select(fn.SUM(IncomeTable.amount_of_money)).where(
                IncomeTable.date >= from_date,
                IncomeTable.date <= to_date,
            ).scalar()

            amount = amount if amount is not None else 0

            data.insert(0, amount)

            to_date = from_date - datetime.timedelta(days=1)
            from_date = to_date.replace(day=1)

        self.summaryTable.setHorizontalHeaderLabels(headers)

        center_item = QTableWidgetItem()
        center_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        for index, value in enumerate(data):
            item = center_item.clone()
            item.setText("{:,} VNĐ".format(value))
            self.summaryTable.setItem(0, index, item)
        
        series = QBarSeries()
        set0 = QBarSet(headers[0])
        set1 = QBarSet(headers[1])
        set2 = QBarSet(headers[2])

        set0 << data[0]
        set1 << data[1]
        set2 << data[2]

        series.append(set0)
        series.append(set1)
        series.append(set2)

        axisY = QValueAxis()
        axisY.setRange(0, max(data) + 500000)
        axisY.setLabelFormat("%d")

        chart = QChart()
        chart.addAxis(axisY, QtCore.Qt.AlignmentFlag.AlignLeft)
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chartView.setChart(chart)

    def backButtonClicked(self):
        from .home import Home
        self.screen = Home()
        self.close()


    def addButtonClicked(self):
        self.form = Form(month=self.month, year=self.year)
        self.form.exec()
        
        if self.form.updated:
            self.loadData()
            self.loadDataSummary()


    def cellClicked(self, row):
        item = self.table.item(row, 0)

        try:
            id = int(item.text())
        except:
            return

        item = IncomeTable.get(IncomeTable.id == id)

        self.form = Form(month=self.month, year=self.year, edit=True, id=id)
        self.form.name_input.setText(item.name)
        self.form.amount_input.setText(str(item.amount_of_money))
        self.form.date_input.setValue(item.date.day)

        self.form.exec()

        if self.form.updated:
            self.loadData()
            self.loadDataSummary()