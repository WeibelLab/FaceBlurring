
from abc import abstractmethod
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QToolButton, QWidget
import cv2

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

        self.brush_size = 150

    @property
    def clicked(self):
        return self.button.clicked

    @abstractmethod
    def mouse_down(self, video, location) -> None:
        pass

    @abstractmethod
    def mouse_move(self, video, location) -> None:
        pass

    @abstractmethod
    def mouse_up(self, video, location) -> None:
        pass

    def mouse_scroll(self, video, value, x, y) -> None:
        # Show new size
        x1, y1 = int(x-self.brush_size/2), int(y-self.brush_size/2)
        x2, y2 = int(x+self.brush_size/2), int(y+self.brush_size/2)
        cv2.rectangle(video.frame, (x1, y1), (x2, y2), (0,0,0), 2)
        video.rerender()
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
        print(video)

    def mouse_up(self, video, location):
        self.mouse_move(video, location)
        video._blur_object.complete()
        video.newFrame.connect(video._blur_object.checkBlurFrame, type=Qt.DirectConnection)
        video._blur_object = None
        video.reblit()

class ConstantBlur(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/select.png"

    def __init__(self):
        super().__init__()

    def mouse_down(self, video, location):
        pass
    
    def mouse_move(self, video, location):
        pass

    def mouse_up(self, video, location):

        video._blur_object = BlurStrand(video, video.resolution)
        video._blur_strands.append(video._blur_object)
        
        # Blur all frames
        print("Blurring from frame 0 to frame", int(video.number_of_frames))
        for i in range(int(video.number_of_frames)):
            video._blur_object.addPoint(
                i,
                location,
                self.brush_size
            )

        video._blur_object.complete(simplify=False)
        video.newFrame.connect(video._blur_object.checkBlurFrame, type=Qt.DirectConnection)
        video._blur_object = None
        video.reblit()

class Eraser(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/eraser.png"

    def __init__(self):
        super().__init__()

class SplitStrand(Tool):
    '''
    Takes a blur stand and cuts it into two at the given frame.
    This allows the user to erase a portion of a blur strand
    '''
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/scissors.png"

    def __init__(self):
        super().__init__()