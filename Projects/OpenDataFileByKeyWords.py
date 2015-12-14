import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import subprocess
from collections import defaultdict
import re


program_tec = "tec360"
program_mat = "matlab"

class DataPath(object):

    def __init__(self, path = "data.txt"):
        self.path = path 
        self.key_path = defaultdict(list)
        self.dirty = False
        with open(self.path,'r') as f:
            onekey = ""
            newkey = True
            for line in f:
                if(line[0] != '\"'):
                    if newkey:
                        onekey = line
                    else:
                        onekey = ','.join([onekey, line])
                    newkey = False
                else:
                    onekey = ', '.join(sorted([w.strip() for w in onekey.rstrip('\n').split(',')]))
                    self.key_path[onekey].append(line.rstrip('\n'))
                    newkey = True

    def search(self, key_words):
        for key, path in self.key_path.items():
            iscontaining = True
            for word in key_words:
                if word:
                    if word[0] == '-':
                        if word[1:].lower() in [w.strip().lower() for w in key.split(',')]:
                            iscontaining = False
                            break 
                    else:
                        if word.lower() not in [w.strip().lower() for w in key.split(',')]:
                            iscontaining = False
                            break 
            if iscontaining:
                yield (key,path)

    def getKeys(self):
        return self.key_path.keys()

    def getPath(self, key):
        return self.key_path[key]

    def modifyKeys(self, old_keys, new_keys):
        pass

    def save(self):
        pass

class OpenTecDataDlg(QDialog):

    def __init__(self, name, parent=None):
        super(OpenTecDataDlg, self).__init__(parent)
        self.data = DataPath()
        self.search_key_word = []
        self.cur_keys = self.data.getKeys()
        self.name = name
        self.createWidgets(self.cur_keys)
        self.layoutWidgets()
        self.connect()
        self.setWindowTitle(name)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(1.0)

        desktop = QApplication.desktop().availableGeometry()
        self.resize(400,desktop.height())
        dw = self.width()
        dh = self.height()
        self.setGeometry(desktop.width()-dw,0, dw, dh)



    def createWidgets(self, keys_list):
        self.input_edit = QLineEdit("Type the key words seperated by \',\'")
        self.input_edit.selectAll()


        self.list_edit = QListWidget()
        if keys_list:
            for keys in keys_list:
                item = QListWidgetItem(keys)
                item.setData(Qt.UserRole,keys)
                self.list_edit.addItem(item)
        self.list_edit.setCurrentRow(0)
        self.list_edit.setMinimumHeight(400)


        self.output_edit = QListWidget()
        if keys_list:
            key = str(self.list_edit.item(0).text())
            pathes = self.data.getPath(key)
            self.output_edit.addItems(pathes)
        self.output_edit.setMaximumHeight(200)

        self.systray = QSystemTrayIcon(self)
        self.systray.setIcon(QIcon("tec.jpg"))
        self.systray.setVisible(True)

    def layoutWidgets(self):
        layout = QVBoxLayout()
        layout.addWidget(self.input_edit)
        layout.addWidget(self.list_edit)
        layout.addWidget(self.output_edit)

        self.setLayout(layout)
        self.input_edit.setFocus()

    def connect(self):
        self.input_edit.returnPressed.connect(self.updateUi)

        # Change the double click to modifu the key words
        self.list_edit.itemDoubleClicked.connect(self.plot)
        self.list_edit.itemClicked.connect(self.showPath)
        self.output_edit.itemDoubleClicked.connect(self.plotPath)

        self.systray.activated.connect(self.show)

    def updateUi(self):
        line = str(self.input_edit.text()).strip()
        if line:
            if line[0] == ':':
                self.command(line[1:])
            else:
                self.search_key_word = [w.strip().lower() for w in line.split(',')]
                self.cur_keys = [w for w, p in self.data.search(self.search_key_word)]
        else:
            self.search_key_word = []
            self.cur_keys = self.data.getKeys()

        self.list_edit.clear()
        for keys in self.cur_keys:
            item = QListWidgetItem(self.removeKeyWords(keys,self.search_key_word))
            item.setData(Qt.UserRole,keys)
            self.list_edit.addItem(item)
        # self.list_edit.addItems(self.cur_keys)

    def command(self, cmd):
        if cmd.lower() == "quit":
            self.systray.setVisible(False)
            self.close()
        if cmd.lower()[0] in "01":
            self.setWindowOpacity(float(cmd))
        if cmd.lower() == "hide":
            self.setWindowOpacity(0)
        if cmd.lower() == "update":
            self.data = DataPath()

    def show(self):
        self.setWindowOpacity(1.0)

    def plot(self, item):
        # key = str(item.text())
        key = item.data(Qt.UserRole).toString()
        pathes = self.data.getPath(key)
        for path in pathes:
            self.openFile(path)

    def plotPath(self, item):
        path = str(item.text())
        self.openFile(path)

    def showPath(self, item):
        # key = str(item.text())
        key = str(item.data(Qt.UserRole).toPyObject())
        pathes = self.data.getPath(key)
        self.output_edit.clear()
        self.output_edit.addItems(pathes)

    def openFile(self, path):
        if path[-4:-1] == "fig":
            subprocess.Popen(' '.join([program_mat,path]))
        else:
            subprocess.Popen(' '.join([program_tec,path]))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.isdrag = True 
            self.drag_position = event.globalPos()-self.pos()
            event.accept()

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() and Qt.LeftButton:
            self.move(QMouseEvent.globalPos()-self.drag_position)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.isdrag = False

    def removeKeyWords(self, string, keys):
        lst = ([w.strip() for w in string.split(',') if w.strip().lower() not in keys])
        if lst:
            return ', '.join(lst)
        else:
            return '0'

    def toHTML(self, string):
        pass


class KeyWordsDelegate(QItemDelegate):
    pass

class OpenTecDataDlgDelg(QDialog):

    def __init__(self, name, parent=None):
        super(OpenTecDataDlgDelg, self).__init__(parent)
        self.data = DataPath()
        self.search_key_word = []
        self.cur_keys = self.data.getKeys()
        self.name = name
        self.createWidgets(self.cur_keys)
        self.layoutWidgets()
        self.connect()
        self.setWindowTitle(name)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(1.0)

        desktop = QApplication.desktop().availableGeometry()
        self.resize(400,desktop.height())
        dw = self.width()
        dh = self.height()
        self.setGeometry(desktop.width()-dw,0, dw, dh)



    def createWidgets(self, keys_list):
        self.input_edit = QLineEdit("Type the key words seperated by \',\'")
        self.input_edit.selectAll()


        self.list_edit = QListWidget()
        if keys_list:
            for keys in keys_list:
                item = QListWidgetItem(keys)
                item.setData(Qt.UserRole,keys)
                self.list_edit.addItem(item)
        self.list_edit.setCurrentRow(0)
        self.list_edit.setMinimumHeight(400)


        self.output_edit = QListWidget()
        if keys_list:
            key = str(self.list_edit.item(0).text())
            pathes = self.data.getPath(key)
            self.output_edit.addItems(pathes)
        self.output_edit.setMaximumHeight(200)

        self.systray = QSystemTrayIcon(self)
        self.systray.setIcon(QIcon("tec.jpg"))
        self.systray.setVisible(True)

    def layoutWidgets(self):
        layout = QVBoxLayout()
        layout.addWidget(self.input_edit)
        layout.addWidget(self.list_edit)
        layout.addWidget(self.output_edit)

        self.setLayout(layout)
        self.input_edit.setFocus()

    def connect(self):
        self.input_edit.returnPressed.connect(self.updateUi)

        # Change the double click to modifu the key words
        self.list_edit.itemDoubleClicked.connect(self.plot)
        self.list_edit.itemClicked.connect(self.showPath)
        self.output_edit.itemDoubleClicked.connect(self.plotPath)

        self.systray.activated.connect(self.show)

    def updateUi(self):
        line = str(self.input_edit.text()).strip()
        if line:
            if line[0] == ':':
                self.command(line[1:])
            else:
                self.search_key_word = [w.strip().lower() for w in line.split(',')]
                self.cur_keys = [w for w, p in self.data.search(self.search_key_word)]
        else:
            self.search_key_word = []
            self.cur_keys = self.data.getKeys()

        self.list_edit.clear()
        for keys in self.cur_keys:
            item = QListWidgetItem(self.removeKeyWords(keys,self.search_key_word))
            item.setData(Qt.UserRole,keys)
            self.list_edit.addItem(item)
        # self.list_edit.addItems(self.cur_keys)

    def command(self, cmd):
        if cmd.lower() == "quit":
            self.systray.setVisible(False)
            self.close()
        if cmd.lower()[0] in "01":
            self.setWindowOpacity(float(cmd))
        if cmd.lower() == "hide":
            self.setWindowOpacity(0)
        if cmd.lower() == "update":
            self.data = DataPath()

    def show(self):
        self.setWindowOpacity(1.0)

    def plot(self, item):
        # key = str(item.text())
        key = item.data(Qt.UserRole).toString()
        pathes = self.data.getPath(key)
        for path in pathes:
            self.openFile(path)

    def plotPath(self, item):
        path = str(item.text())
        self.openFile(path)

    def showPath(self, item):
        # key = str(item.text())
        key = str(item.data(Qt.UserRole).toPyObject())
        pathes = self.data.getPath(key)
        self.output_edit.clear()
        self.output_edit.addItems(pathes)

    def openFile(self, path):
        if path[-4:-1] == "fig":
            subprocess.Popen(' '.join([program_mat,path]))
        else:
            subprocess.Popen(' '.join([program_tec,path]))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.isdrag = True 
            self.drag_position = event.globalPos()-self.pos()
            event.accept()

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() and Qt.LeftButton:
            self.move(QMouseEvent.globalPos()-self.drag_position)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.isdrag = False

    def removeKeyWords(self, string, keys):
        lst = ([w.strip() for w in string.split(',') if w.strip().lower() not in keys])
        if lst:
            return ', '.join(lst)
        else:
            return '0'

    def toHTML(self, string):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = OpenTecDataDlg("Data Plot")
    sys.exit(form.exec_())

