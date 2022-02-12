from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
)
from PyQt6.QtGui import QFont, QBrush, QColor
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet
from peewee import fn
from PyQt6 import QtCore
from db import Income as IncomeTable, Expense as ExpenseTable
import ctypes
import datetime
from helpers.const import Vietnamese

from .income import IncomeScreen
from .expense import ExpenseScreen


class Home(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def initUI(self):
        user32 = ctypes.windll.user32

        desktop_width = user32.GetSystemMetrics(0)
        desktop_height = user32.GetSystemMetrics(1)

        width = int(desktop_width * 0.23)
        height = int(desktop_height * 0.34)

        self.resize(width, height)

        hbox1 = QHBoxLayout()
        hbox1.addStretch()

        vbox1 = QVBoxLayout()
        vbox1.addSpacing(30)

        label = QLabel(Vietnamese.REVENUE_AND_EXPENDITURE_SOFTWARE.value.title())
        font = QFont('Times', 20)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        vbox1.addWidget(label)

        self.chartView = QChartView()
        vbox1.addWidget(self.chartView)

        self.month_input = QDateEdit()
        self.month_input.setCurrentSection(
            QDateEdit.Section.MonthSection 
        )
        self.month_input.setDateTime(
            QtCore.QDateTime.currentDateTime()
        )
        self.month_input.setDisplayFormat("MM/yyyy")
        self.month_input.dateChanged.connect(self.loadData)
        vbox1.addWidget(self.month_input)

        hbox2 = QHBoxLayout()

        income_button = QPushButton(Vietnamese.INCOME.value)
        income_button.clicked.connect(self.incomeButtonClicked)

        expense_button = QPushButton(Vietnamese.EXPENSE.value)
        expense_button.clicked.connect(self.expenseButtonClicked)

        hbox2.addWidget(income_button)
        hbox2.addWidget(expense_button)
        
        vbox1.addLayout(hbox2)
        vbox1.addSpacing(30)

        hbox1.addLayout(vbox1)

        hbox1.addStretch()
        self.setLayout(hbox1)
        self.setWindowTitle(Vietnamese.REVENUE_AND_EXPENDITURE_SOFTWARE.value)
        self.show()

    def loadData(self):
        date = self.month_input.date().toPyDate()

        from_date = date.replace(day=1)
        to_date = datetime.date(date.year + int(date.month/12), date.month % 12 + 1, 1) - datetime.timedelta(days=1)

        imcome_total = IncomeTable.select(fn.SUM(IncomeTable.amount_of_money)).where(
            IncomeTable.date >= from_date,
            IncomeTable.date <= to_date,
        ).scalar()

        imcome_total = imcome_total if imcome_total is not None else 0

        expense_total = ExpenseTable.select(fn.SUM(ExpenseTable.amount_of_money)).where(
            ExpenseTable.date >= from_date,
            ExpenseTable.date <= to_date,
        ).scalar()

        expense_total = expense_total if expense_total is not None else 0

        series = QBarSeries()
        set0 = QBarSet(Vietnamese.INCOME.value)
        set0.setBrush(QBrush(QColor(0, 0, 255)))
        set1 = QBarSet(Vietnamese.EXPENSE.value)
        set1.setBrush(QBrush(QColor(255, 0, 0)))

        set0 << imcome_total
        set1 << expense_total

        series.append(set0)
        series.append(set1)

        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.chartView.setChart(chart)

    def incomeButtonClicked(self):
        date = self.month_input.date().toPyDate()

        self.screen = IncomeScreen(date.month, date.year)

        self.close()

    def expenseButtonClicked(self):
        date = self.month_input.date().toPyDate()

        self.screen = ExpenseScreen(date.month, date.year)

        self.close()