
from abc import abstractmethod
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QCursor, QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QToolButton, QWidget
import cv2, numpy

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
        # Set brush size
        self.brush_size += value*5
        if self.brush_size <= 0:
            self.brush_size = 0

        # Set cursor size
        s = int(self.brush_size/2)
        cursor_np = numpy.zeros((s, s, 4), numpy.uint8)
        cv2.rectangle(cursor_np, (0, 0), (s, s), (255, 255, 255, 255), 2)
        cursor_img = QImage(cursor_np, cursor_np.shape[1], cursor_np.shape[0], cursor_np.shape[1] * 4, QImage.Format_RGBA8888)
        cursor_pix = QPixmap(cursor_img)
        cursor = QCursor(cursor_pix, -1, -1)
        video.setCursor(cursor)

    def on_active_tool_changed(self, tool) -> None:
        if (isinstance(tool, type(self))):
            print("I ({}) was selected".format(self))
            # TODO: show tool button is selected
            self.button.setStyleSheet("border:2px solid red")
        else:
            self.button.setStyleSheet("border:None")

    def mouse_over(self, video): 
        s = int(self.brush_size/2)
        cursor_np = numpy.zeros((s, s, 4), numpy.uint8)
        cv2.rectangle(cursor_np, (0, 0), (s, s), (255, 255, 255, 255), 2)
        cursor_img = QImage(cursor_np, cursor_np.shape[1], cursor_np.shape[0], cursor_np.shape[1] * 4, QImage.Format_RGBA8888)
        cursor_pix = QPixmap(cursor_img)
        cursor = QCursor(cursor_pix, -1, -1)
        video.setCursor(cursor)

    def mouse_leave(self, video):
        video.setCursor(QCursor())




class BlurBrush(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/brush.png"
    def __init__(self):
        super().__init__()

    def mouse_down(self, video, location):
        video._blur_object = BlurStrand(video, video.resolution)
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
        
        # Blur all frames
        print("Blurring from frame 0 to frame", int(video.number_of_frames))
        for i in range(int(video.number_of_frames)):
            video._blur_object.addPoint(
                i,
                location,
                self.brush_size
            )

        video._blur_object.complete(simplify=False)
        video._blur_object = None
        video.reblit()

class Eraser(Tool):
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/erase.png"

    def __init__(self):
        super().__init__()

    def mouse_down(self, video, location):
        pass

    def mouse_move(self, video, location):
        pass

    def mouse_up(self, video, location):
        # Check to see if cursor intersects with any blur points
        for strand in video._blur_strands:
            for point in strand.checkBlurFrame(video.position):
                # Get BlurPoint region
                ret = point.get_blur_region(video.frame)
                if ret is None: continue
                x_start, y_start, x_end, y_end = ret

                # Check if click is within a blur
                if (x_start < location[0] < x_end) and (y_start < location[1] < y_end):
                    strand.destroy()

                video.setPosition(video.position)

    def mouse_over(self, video): 
        video.setCursor(Qt.CursorShape.CrossCursor)
    def mouse_scroll(self, video, value, x, y) -> None:
        pass

class SplitStrand(Tool):
    '''
    Takes a blur stand and cuts it into two at the given frame.
    This allows the user to erase a portion of a blur strand
    '''
    icon_path = "C:/Users/tlsha/GitHub/FaceBlurring/assets/scissors.png"

    def __init__(self):
        super().__init__()

    def mouse_down(self, video, location):
        print(location)
        pass

    def mouse_move(self, video, location):
        pass

    def mouse_up(self, video, location):
        # Check to see if cursor intersects with any blur points
        for strand in video._blur_strands:
            for point in strand.checkBlurFrame(video.position):
                # Get BlurPoint region
                ret = point.get_blur_region(video.frame)
                if ret is None: continue
                x_start, y_start, x_end, y_end = ret

                # Check if click is within a blur
                if (x_start < location[0] < x_end) and (y_start < location[1] < y_end):
                    newStrands = strand.split_on(video.position)

                    return # only split one at a time

    
    def mouse_over(self, video): 
        video.setCursor(Qt.CursorShape.CrossCursor)
    def mouse_scroll(self, video, value, x, y) -> None:
        pass   
