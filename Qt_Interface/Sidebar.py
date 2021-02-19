

from PyQt5.QtWidgets import QBoxLayout, QPushButton, QWidget


class SidebarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layoutBox = QBoxLayout()
        self.setLayout(self.layoutBox)

        self.loadButton = QPushButton()
        self.loadButton.setText("Load File")
        self.loadButton.clicked.connect(self.loadVideo)
        self.layoutBox.addWidget(self.loadButton)
