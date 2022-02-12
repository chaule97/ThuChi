from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLabel,
    QStyle,
    QTableWidget,
    QAbstractItemView,
    QTableWidgetItem,
    QTableView,
    QHeaderView,
    QDialog,
    QLineEdit,
    QComboBox,
    QSpinBox,
)
from PyQt6.QtGui import QFont, QIntValidator, QBrush, QColor
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6 import QtCore
import ctypes
import datetime
from db import Expense as ExpenseTable
from peewee import fn
from helpers.const import Vietnamese
from calendar import monthrange

headers = [
    'ID',
    Vietnamese.CONTENT.value,
    Vietnamese.DATE.value,
    Vietnamese.MUST_HAVE.value,
    Vietnamese.NICE_TO_HAVE.value,
    Vietnamese.WASTED.value,
]

summaryHeaders = [
    '',
    Vietnamese.LAST_MONTH.value,
    Vietnamese.THIS_MONTH.value,
    '',
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

        expense_type_label = QLabel(Vietnamese.EXPENSE_TYPE.value)
        self.expense_type_input = QComboBox()
        self.expense_type_input.addItem(Vietnamese.MUST_HAVE.value, ExpenseTable.MUST_HAVE)
        self.expense_type_input.addItem(Vietnamese.NICE_TO_HAVE.value, ExpenseTable.NICE_TO_HAVE)
        self.expense_type_input.addItem(Vietnamese.WASTED.value, ExpenseTable.WASTED)

        form_layout.addRow(expense_type_label, self.expense_type_input)

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
            self.setWindowTitle(Vietnamese.ADD_EXPENSE.value)
        else:
            submit_button.clicked.connect(self.update)
            self.setWindowTitle(Vietnamese.EDIT_EXPENSE.value)

    def validated(self):
        conditions = [
            self.name_input.text().strip() != '',
            self.amount_input.text().strip() != '',
            self.amount_input.text().isdigit(),
        ]

        return not False in conditions

    def insert(self):
        if self.validated():
            data = ExpenseTable()
            data.name = self.name_input.text()
            data.amount_of_money = int(self.amount_input.text())
            data.type = self.expense_type_input.currentData()
            data.date = datetime.date(self.year, self.month, int(self.date_input.value()))
            data.save()

            self.updated = True
            self.close()

    def update(self):
        if self.validated():
            q = (
                ExpenseTable.update({
                    ExpenseTable.name: self.name_input.text(),
                    ExpenseTable.amount_of_money: int(self.amount_input.text()),
                    ExpenseTable.type: self.expense_type_input.currentData(),
                    ExpenseTable.date: datetime.date(self.year, self.month, int(self.date_input.value()))
                }).where(
                    ExpenseTable.id == self.id
                )
            )
            q.execute()
            self.updated = True
            self.close()

class ExpenseScreen(QWidget):

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
        
        vbox2 = QVBoxLayout()
        
        vbox2.addStretch()
        self.summaryTable = self.createTableSummary()
        vbox2.addWidget(self.summaryTable)
        vbox2.addSpacing(20)

        font = QFont()
        font.setPixelSize(16)

        self.minimum_standard_of_living_label = QLabel()
        self.minimum_standard_of_living_label.setFont(font)
        vbox2.addWidget(self.minimum_standard_of_living_label)
        self.standard_of_living_label = QLabel()
        self.standard_of_living_label.setFont(font)
        vbox2.addWidget(self.standard_of_living_label)
        self.expense_in_month_label = QLabel()
        self.expense_in_month_label.setFont(font)
        vbox2.addWidget(self.expense_in_month_label)
        vbox2.addStretch()

        hbox2.addLayout(vbox2)

        hbox2.addStretch()

        self.chartView = QChartView()
        self.chartView.setMaximumHeight(desktop_height * 0.278)
        hbox2.addWidget(self.chartView)


        vbox1.addLayout(hbox2)

        self.setLayout(vbox1)
        self.setWindowTitle(Vietnamese.EXPENSE_SECTION.value)
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
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        table.cellDoubleClicked.connect(self.cellClicked)
        return table

    def createTableSummary(self):
        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setRowCount(3)
        table.setColumnCount(len(summaryHeaders))
        table.setHorizontalHeaderLabels(summaryHeaders)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(150)
        return table

    def loadData(self):
        from_date = datetime.date(self.year, self.month, 1)
        to_date = datetime.date(self.year + int(self.month/12), self.month % 12 + 1, 1) - datetime.timedelta(days=1)

        data = ExpenseTable.select().where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date
        ).order_by(ExpenseTable.date)

        self.table.clearContents()
        row_count = data.count() if data.count() > 0 else 10
        self.table.setRowCount(row_count + 1)

        center_item = QTableWidgetItem()
        center_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        must_have_total = 0
        nice_to_have_total = 0
        wasted_total = 0

        for index, record in enumerate(data):
            data = [
                str(record.id),
                str(record.name),
                record.date.strftime('%d/%m/%Y'),
            ]

            money = "{:,} VNĐ".format(record.amount_of_money)

            if record.type == ExpenseTable.MUST_HAVE:
                data.extend([
                    money,
                    '',
                    '',
                ])
                must_have_total += record.amount_of_money
            elif record.type == ExpenseTable.NICE_TO_HAVE:
                data.extend([
                    '',
                    money,
                    '',
                ])
                nice_to_have_total += record.amount_of_money
            else:
                data.extend([
                    '',
                    '',
                    money,
                ])
                wasted_total += record.amount_of_money

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
            "{:,} VNĐ".format(must_have_total),
            "{:,} VNĐ".format(nice_to_have_total),
            "{:,} VNĐ".format(wasted_total),
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

        must_have_total_this_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.MUST_HAVE
        ).scalar()

        must_have_total_this_month = must_have_total_this_month if must_have_total_this_month is not None else 0

        nice_to_have_total_this_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.NICE_TO_HAVE
        ).scalar()

        nice_to_have_total_this_month = nice_to_have_total_this_month if nice_to_have_total_this_month is not None else 0

        wasted_total_this_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.WASTED
        ).scalar()

        wasted_total_this_month = wasted_total_this_month if wasted_total_this_month is not None else 0

        to_date = from_date - datetime.timedelta(days=1)
        from_date = to_date.replace(day=1)

        must_have_total_last_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.MUST_HAVE
        ).scalar()

        must_have_total_last_month = must_have_total_last_month if must_have_total_last_month is not None else 0

        nice_to_have_total_last_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.NICE_TO_HAVE
        ).scalar()

        nice_to_have_total_last_month = nice_to_have_total_last_month if nice_to_have_total_last_month is not None else 0

        wasted_total_last_month = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
            ExpenseTable.type == ExpenseTable.WASTED
        ).scalar()

        wasted_total_last_month = wasted_total_last_month if wasted_total_last_month is not None else 0

        must_have_difference = must_have_total_this_month - must_have_total_last_month
        nice_to_have_difference = nice_to_have_total_this_month - nice_to_have_total_last_month
        wasted_difference = wasted_total_this_month - wasted_total_last_month

        # Show difference 2 months
        data = [
            [
                Vietnamese.MUST_HAVE.value,
                "{:,} VNĐ".format(must_have_total_last_month),
                "{:,} VNĐ".format(must_have_total_this_month),
                must_have_difference
            ],
            [
                Vietnamese.NICE_TO_HAVE.value,
                "{:,} VNĐ".format(nice_to_have_total_last_month),
                "{:,} VNĐ".format(nice_to_have_total_this_month),
                nice_to_have_difference
            ],
            [
                Vietnamese.WASTED.value,
                "{:,} VNĐ".format(wasted_total_last_month),
                "{:,} VNĐ".format(wasted_total_this_month),
                wasted_difference
            ],
        ]

        center_item = QTableWidgetItem()
        center_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        for index, record in enumerate(data):
            column = 0

            for value in record:
                item = center_item.clone()

                if column == 3:
                    if value > 0:
                        item.setForeground(QBrush(QColor(255, 0, 0)))
                        value = "+ {:,} VNĐ".format(value)
                    elif value < 0:
                        item.setForeground(QBrush(QColor(0, 0, 255)))
                        value = "- {:,} VNĐ".format(abs(value))
                    else:
                        value = "0 VNĐ"

                item.setText(value)

                self.summaryTable.setItem(index, column, item)
                column += 1

        # Show standard living
        self.minimum_standard_of_living_label.setText(f'{Vietnamese.MINIUM_STANDARD_LIVING.value}: { "{:,}".format(must_have_total_this_month) } VNĐ')
        self.standard_of_living_label.setText(f'{Vietnamese.STANDARD_LIVING.value}: { "{:,}".format(must_have_total_this_month + nice_to_have_total_this_month) } VNĐ')
        self.expense_in_month_label.setText(f'{Vietnamese.EXPENSE_IN_MONTH.value}: { "{:,}".format(must_have_total_this_month + nice_to_have_total_this_month + wasted_total_this_month) } VNĐ')

        # Show Chart
        this_month = must_have_total_this_month + nice_to_have_total_this_month + wasted_total_this_month
        
        if this_month > 0:
            must_have_total_this_month_percent = must_have_total_this_month / this_month * 100
            nice_to_have_total_this_month_percent = nice_to_have_total_this_month / this_month * 100
            wasted_total_this_month_percent = 100 - must_have_total_this_month_percent - nice_to_have_total_this_month_percent

            series = QPieSeries()

            series.append(Vietnamese.MUST_HAVE.value, must_have_total_this_month_percent)
            series.append(Vietnamese.NICE_TO_HAVE.value, nice_to_have_total_this_month_percent)
            series.append(Vietnamese.WASTED.value, wasted_total_this_month_percent)
            series.slices()[0].setBrush(QBrush(QColor(0, 0, 255)))
            series.slices()[1].setBrush(QBrush(QColor(255, 165, 0)))
            series.slices()[2].setBrush(QBrush(QColor(255, 0, 0)))
            series.setLabelsVisible()

            chart = QChart()
            chart.legend().setVisible(False)
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

        item = ExpenseTable.get(ExpenseTable.id == id)

        self.form = Form(month=self.month, year=self.year, edit=True, id=id)
        self.form.name_input.setText(item.name)
        self.form.amount_input.setText(str(item.amount_of_money))
        
        if item.type == ExpenseTable.MUST_HAVE:
            self.form.expense_type_input.setCurrentText(Vietnamese.MUST_HAVE.value)
        elif item.type == ExpenseTable.NICE_TO_HAVE:
            self.form.expense_type_input.setCurrentText(Vietnamese.NICE_TO_HAVE.value)
        else:
            self.form.expense_type_input.setCurrentText(Vietnamese.WASTED.value)

        self.form.date_input.setValue(item.date.day)

        self.form.exec()

        if self.form.updated:
            self.loadData()
            self.loadDataSummary()