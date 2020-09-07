from PyQt5.QtWidgets import QMainWindow, QGridLayout, QLabel, QApplication, QWidget, QPushButton, QLineEdit, QAction, QCalendarWidget
from PyQt5 import QtCore, QtGui
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime
import time
import sys
import pickle
import math


# loads pickeled objects
def load_obj(datatype):
    with open(f"{datatype}" + '.pkl', 'rb') as f:
        return pickle.load(f)

# decorator to pickle the output of a function
def pickle_output(file_name="file"):
    def decorate(func):
        def pickle_out(*arg):
            out = func(*arg)
            pick_out = open(f"{file_name}.pkl", "wb")
            pickle.dump(out, pick_out, pickle.HIGHEST_PROTOCOL)
            pick_out.close()
            return out
        return pickle_out
    return decorate


# iterates through news_outlet_data and downloads the top news story for each outlet
@pickle_output("headlines")
def get_news(news_outlet_data):
    # input
    # dict: {str(news outlet) : (str(site url), str(attribute), str(attribute class))}

    # output
    # dict: {str(news outlet) : (str(headline), str(site url))}
    # list: of news outlets
    # datetime.datetime: date and time of last update
    headlines = {}
    all_headlines = load_obj("All Headlines")
    driver = configure_driver()
    @pickle_output("All Headlines")
    def update_all_headlines():
        all_headlines[datetime.datetime.today()] = headlines
        return all_headlines
    for (news_name, (site, attr_name, class_name)) in zip(list(news_outlet_data.keys()), list(news_outlet_data.values())):
        driver.get(site)
        time.sleep(1)
        print(news_name)
        content = getattr(driver, attr_name)(class_name)
        for headline_temp in content:
            if headline_temp.text != "":
                headlines[news_name] = (headline_temp.text, get_href(headline_temp))
                break
    update_all_headlines()
    return (headlines, list(news_outlet_data.keys()), datetime.datetime.today())


# sets webdriver to headless
def configure_driver():
    # output
    # object: webdriver object
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    return driver


# retrieve links from WebElement objects
def get_href(headline, path=".//*", backtrace=1):
    # input
    # WebElement object:
    # str: path to the html objects child or its parent
    # int: number of movements up or down the path, doubles after the first recursion to go back and travel up through
    # the parents. In future will be improved with beautiful soup 4

    # output
    # str: url for headline article OR object: none
    for k in range(3*backtrace):
        try:
            if headline.get_attribute("href") != None:
                return headline.get_attribute("href")
            headline = headline.find_element_by_xpath(path)
        except:
            return get_href(headline, "./parent::*", 2)
    return None


# used to reduce code repitition
class MainWindow(QMainWindow):
    # initializes layout
    def __init__(self):
        super().__init__()
        self.window = QWidget(self)
        self.setCentralWidget(self.window)
        self.grid = QGridLayout()

    # adds layout to window, configures and then displays it
    def finish(self, title, x_dim=500, y_dim=400):
        self.window.setLayout(self.grid)
        self.setGeometry(1300, 300, x_dim, y_dim)
        self.setWindowTitle(title)
        self.show()


# a window for getting information from the user which is used to add a new news outlet
class AddNewsOutlet(MainWindow):
    # input - from user
    # str: four strings that are all outputted

    # output - to NewsGui object
    # {"Outlet Name" : str(outlet name), "Outlet Url" : str(outlet url),
    # "Left, Center or Right" : str(political leaning),
    # "Current Headline" : str(current headline)}
    def __init__(self, Main_Gui):
        super().__init__()

        # initialize gui variables
        self.Main_Gui = Main_Gui
        self.entries = {}

        # initialize gui features
        self.add_labels()
        self.add_inputs()
        self.add_buttons()
        self.finish("Add a New Outlet", x_dim=300, y_dim=100)

    def add_labels(self):
        for ind, query in enumerate(["Outlet Name", "Outlet Url", "Left, Center or Right", "Current Headline"]):
            self.grid.addWidget(QLabel(query+": "), ind, 0)

    def add_inputs(self):
        for ind, query in enumerate(["Outlet Name", "Outlet Url", "Left, Center or Right", "Current Headline"]):
            self.entries[query] = QLineEdit()
            self.grid.addWidget(self.entries[query], ind, 1)

    def add_buttons(self):
        submit = QPushButton("Submit")
        submit.clicked.connect(lambda: self.submit())
        self.grid.addWidget(submit, 4, 0)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(lambda: self.close())
        self.grid.addWidget(cancel, 4, 1)

    def submit(self):
        self.close()
        self.Main_Gui.new_out = {key: val.text() for key, val in zip(list(self.entries.keys()), list(self.entries.values()))}


class HistoricalNews(MainWindow):
    def __init__(self):
        super().__init__()

        self.history = load_obj("All Headlines")

        self.add_calendar()
        self.test()
        # self.add_labels()
        self.finish("History")

    def add_calendar(self):
        self.calendar = QCalendarWidget(self)

        self.grid.addWidget(self.calendar, 0, 0)
        self.calendar.clicked[QtCore.QDate].connect(self.date_search)


    def test(self):
        format = QtGui.QTextCharFormat()
        format.setFont(QtGui.QFont('Times', 15))
        [self.calendar.setDateTextFormat(QtCore.QDate(date.year, date.month, date.day), format)
         for date in list(self.history.keys())]

    def date_search(self, date):
        selected_date = datetime.datetime.strptime(date.toString(), "%a. %b. %d %Y")
        # if str(date.date) in [str(news_date.date()) for news_date in list(self.history.keys())]:

        for news_date, news_info in list(self.history.items()):
            if str(news_date.date()) == str(selected_date.date()):
                NewsGUI((news_info, list(news_info.keys()), news_date))
                # selected_date = (news_date, news_info)
                # break
            print(date)

    def add_labels(self):
        for ind, query in enumerate(list(self.history.keys())):
            self.grid.addWidget(QLabel(f"{query}"), ind, 0)

    def selection(self):
        pass


# main project gui window
class NewsGUI(MainWindow):

    def __init__(self, current_news=load_obj("headlines")):
        super().__init__()

        # initialize gui variables
        self.headlines, self.news_outlets, self.datetime = current_news  # replace news_out with list(headlines.keys())
        self.labels = {(row, col): QLabel() for col in range(3) for row in range(math.ceil(len(self.news_outlets)/3))}

        # initialize gui features
        self.add_buttons(self.add_labels())
        self.add_menus()
        self.finish(f"News for {self.datetime.date()}")

    # adds news headlines to gui
    def add_labels(self):
        for col, bias in enumerate(["<b style=\"color:blue\">LEFT</b>","<b style=\"color:black\">CENTER</b>",
                                                                        "<b style=\"color:red\">RIGHT</b>"]):
            (label := QLabel(bias), label.setAlignment(QtCore.Qt.AlignCenter), self.grid.addWidget(label, 0, col))
        for ind, (coord, label) in enumerate(zip(list(self.labels.keys()), list(self.labels.values()))):
            (headline_text, link), outlet = (self.headlines[self.news_outlets[ind]], self.news_outlets[ind])
            label.setText(
                f"<a href=\"{link}\" style=color:black; style=text-decoration:none> "
                f"<a>{outlet}: {headline_text}</font> </a>")
            (label.setOpenExternalLinks(True), label.setWordWrap(True),
            label.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignCenter),
            self.grid.addWidget(label, coord[0] + 1, coord[1]))
        (label := QLabel(f"Last Updated: {self.datetime}"), label.setWordWrap(True), label.setAlignment(QtCore.Qt.AlignRight))
        self.grid.addWidget(label, coord[0] + 4, 2)
        return coord[0] + 1

    def add_buttons(self, row_temp):
        button = QPushButton("Refresh")
        button.clicked.connect(lambda: self.refresh_news())
        self.grid.addWidget(button, row_temp+3, 0)

    def add_menus(self):
        menubar = self.menuBar()
        filemenu = menubar.addMenu("File")

        # history = QAction("View History", self)
        # history.triggered.connect(lambda: self.history())
        # filemenu.addAction(history)

        new = QAction("New Outlet", self)
        new.triggered.connect(lambda: self.new_outlet())
        filemenu.addAction(new)

    def history(self):
        self.close()
        HistoricalNews()

    def new_outlet(self):
        add_new = AddNewsOutlet(self)
        add_new.show()

    # fetch updated headlines
    def refresh_news(self):
        get_news(load_obj("news_outlet_data"))
        self.add_labels()


def main():
    app = QApplication(sys.argv)
    # a = HistoricalNews()
    a = NewsGUI()
    sys.exit(app.exec_())


main()