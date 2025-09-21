import sys
from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    )
from Macros import MacroClass

# An optional XML file can preload macros.
MacroFilename = None
if len(sys.argv) > 1:
    MacroFilename = sys.argv[1]

# Macro class instance
Macros = MacroClass(MacroFilename)

# Link function for learning new keys
def onNewKey(key):
    WindowMain.addKey(key)
Macros.SetKeyFunc(onNewKey)

# Link function for not learning old keys
def onUsedKey(index):
    QMessageBox.critical(WindowMain, "Already Used", "\'" + Macros.KeyName(index) +
                            "\' is already being used by \"" + Macros.Names[index] + "\".")
    WindowMain.stopAll()
Macros.SetUsedFunc(onUsedKey)

# The Add Tab button
class NewTabButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setText("Add Tab")

# The hotkey button
class KeyButton(QPushButton):
    def __init__(self, index):
        super().__init__()
        self.index = index
        # Button text is key name
        self.setText(Macros.KeyName(self.index))
        self.clicked.connect(self.Press)
        # "Checkable" indicates a toggle button
        self.setCheckable(True)

    # When the button is clicked
    def Press(self):
        if self.isChecked():
            Macros.SetMacroListening(False)
            self.setText("Press a new key")
        else:
            self.setText(Macros.KeyName(self.index))
            Macros.SetMacroListening(True)

# Tab Class
class TabWindow(QWidget):
    def __init__(self, index):
        super().__init__()
        self.index = index
        nameLabel = QLabel("Name:")
        # Line edit for name
        self.nameBox = QLineEdit(Macros.Names[index])
        keyLabel = QLabel("Key:")
        # Hotkey Button
        self.keyButton = KeyButton(index)
        macroLabel = QLabel("Macro:")
        # Text area for content
        self.macroTextBox = QPlainTextEdit(Macros.Macros[index])

        # Track text updates
        self.nameBox.textChanged.connect(self.changeName)
        self.macroTextBox.textChanged.connect(self.changeText)

        self.nameBox.installEventFilter(self)
        self.nameBox.selectionChanged.connect(self.Stop)
        self.macroTextBox.selectionChanged.connect(self.Stop)

        # Use a vertical layout
        layout = QVBoxLayout()
        # Create layout
        layout.addWidget(nameLabel)
        layout.addWidget(self.nameBox)
        layout.addWidget(keyLabel)
        layout.addWidget(self.keyButton)
        layout.addWidget(macroLabel)
        layout.addWidget(self.macroTextBox)
        self.setLayout(layout)

    # This catches clicking into
    # nameBox without causing its
    # cursor to move
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.FocusIn:
            self.Stop()
        return super().eventFilter(obj, ev)

    # Change Macro's name with text line
    def changeName(self):
        Macros.Names[self.index] = self.nameBox.text()
        WindowMain.Tabs.setTabText(self.index, self.nameBox.text())

    # Change Macro's content with text box
    def changeText(self):
        Macros.Macros[self.index] = self.macroTextBox.toPlainText()

    # Uncheck hotkey button and stop listening
    def Stop(self):
        if self.keyButton.isChecked:
            self.keyButton.setChecked(False)
            self.keyButton.setText(Macros.KeyName(self.index))
            Macros.SetMacroListening(True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Manager")

        # A main widget to hold tabs
        mainWidget = QWidget()
        layout = QVBoxLayout()
        self.addButton = NewTabButton()
        self.addButton.pressed.connect(self.tabOpen)

        # The tab host
        self.Tabs = QTabWidget()
        self.Tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.Tabs.setMovable(True)
        self.Tabs.setTabsClosable(True)

        # Create a tab for initial macros
        self.macroDetail = list()
        for i, name in enumerate(Macros.Names):
            md = TabWindow(i)
            self.macroDetail.append(md)
            self.Tabs.addTab(md, name)

        self.Tabs.tabCloseRequested.connect(self.tabClose)
        self.Tabs.currentChanged.connect(self.tabChange)
    
        # Commit layout
        layout.addWidget(self.Tabs)
        layout.addWidget(self.addButton)
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

    # Stops every hotkey button
    def stopAll(self):
        for i, tab in enumerate(self.macroDetail):
            self.macroDetail[i].Stop()

    # Tab changes
    def tabChange(self, index):
        self.stopAll()

    # New tab opened
    def tabOpen(self):
        i = Macros.AddKey('q') - 1
        md = TabWindow(i)
        self.macroDetail.append(md)
        self.Tabs.addTab(md, Macros.Names[i])

    # Add new macro
    def addKey(self, key):
        for i, tab in enumerate(self.macroDetail):
            if self.macroDetail[i].keyButton.isChecked():
                Macros.Hotkeys[i] = key
                self.macroDetail[i].Stop()

    # Prompt before closing a tab
    def tabClose(self, index):
        # Format fix for tabs with no name
        padding = ' '
        if self.Tabs.tabText(index) == '':
            padding = ''
        # Ask if the user want to close tab + end macro
        closePrompt = QMessageBox.question(self, "Close Tab",
            "Are you sure you want to close the " +
            self.Tabs.tabText(index) + padding + "tab?\n" +
            "This will end the associated macro.")
        if closePrompt == QMessageBox.StandardButton.Yes:
            # Remove the tab and it's window
            self.Tabs.removeTab(index)
            self.macroDetail.remove(self.macroDetail[index])
            # Remove the macro
            Macros.Hotkeys.pop(index)
            Macros.Names.pop(index)
            Macros.Macros.pop(index)
            # If that was the last tab, exit
            if self.Tabs.count() == 0:
                self.macroDetail[index].Stop()
                self.close()

    # Prompt before closing the window
    def closeEvent(self, event):
        self.stopAll()
        if self.Tabs.count() > 0:
            closePrompt = QMessageBox.question(self, "Close",
                "Are you sure you want to quit?\nAll macros will end if you quit.")
            if closePrompt == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

# Create QT app
app = QApplication(sys.argv)
# Set main window
WindowMain = MainWindow()
# Show window
WindowMain.show()
# Execute QT app and close with it
sys.exit(app.exec())
