
from Video import VideoWidget
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QWidget

class SidebarWidget(QWidget): #QDock

    def __init__(self, parent, videoSpace):
        QWidget.__init__(self, parent)
        self.metaObject().className()
        self.setLayout(QHBoxLayout())

        print(help(self))
        self.setAttribute("className", "SidebarWidget") # FIXME: works?
        
        self.__videoSpace = videoSpace

        self.loadButton = QPushButton()
        self.loadButton.setText("Load File")
        self.loadButton.clicked.connect(self.loadVideo)
        self.layout().addWidget(self.loadButton)

        self.setMinimumSize(300, 800)


    def loadVideo(self):
        video = VideoWidget.loadVideo()
        if (video is not None):
            self.__videoSpace.layout().addWidget(video)
        
