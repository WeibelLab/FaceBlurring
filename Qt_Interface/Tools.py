
from abc import abstractmethod
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QToolButton, QWidget

from BlurObject import *
from Video import Video

class Tool:
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/brush.png"
    tools = []

    def __init__(self):
        self.button = QToolButton()
        self.button.setGeometry(QRect(220, 120, 41, 41))
        icon = QIcon()
        icon.addPixmap(QPixmap(self.icon_path), QIcon.Normal, QIcon.Off)
        self.button.setIcon(icon)
        self.tools.append(self.button)
        Tool.tools.append(self)

        self.brush_size = 0.1

    @property
    def clicked(self):
        return self.button.clicked

    @abstractmethod
    def mouse_down(self, data: tuple) -> None:
        print("\tTool Down")
        pass

    @abstractmethod
    def mouse_move(self, data: tuple) -> None:
        print("\tTool Use")
        pass

    @abstractmethod
    def mouse_up(self, data: tuple) -> None:
        print("\tTool Up")
        pass

    def on_active_tool_changed(self, tool) -> None:
        if (isinstance(tool, type(self))):
            print("I ({}) was selected".format(self))
            # TODO: show tool button is selected
            self.button.setStyleSheet("border:2px solid red")
        else:
            self.button.setStyleSheet("border:None")




class BlurBrush(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/brush.png"
    def __init__(self):
        super().__init__()

    def mouse_down(self, video, location):
        video._blur_object = BlurStrand(video, video.resolution)
        video._blur_strands.append(video._blur_object)

        self.mouse_move(video, location)
    
    def mouse_move(self, video, location):
        video._blur_object.addPoint(
            video.position, # frame number
            location, # blur location
            self.brush_size
        )

    def mouse_up(self, video, location):
        self.mouse_move(video, location)
        video._blur_object.complete()
        video.newFrame.connect(video._blur_object.checkBlurFrame, type=Qt.DirectConnection)
        video._blur_object = None

class ConstantBlur(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/select.png"

    def __init__(self):
        super().__init__()

class Eraser(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/eraser.png"

    def __init__(self):
        super().__init__()