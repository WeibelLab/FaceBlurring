from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QRect, pyqtSignal
from PyQt5.QtWidgets import QBoxLayout, QHBoxLayout, QToolButton, QVBoxLayout, QWidget
from Tools import *
from Video import VideoWidget

class Toolbar (QWidget):

    active_tool_changed = pyqtSignal(Tool)

    def __init__(self, parent=None, video_blurring_window=None):
        super().__init__(parent)
        self.video_blurring_window = video_blurring_window
        self.setLayout(QVBoxLayout())
        # self.setStyleSheet("border:1px solid red")


        ## Create Buttons
        # Blur brush
        self.blur_brush = BlurBrush()
        self.layout().addWidget(self.blur_brush.button)
        self.blur_brush.clicked.connect(self.toggle_blur_brush)

        # Constant Blur
        self.const_blur = ConstantBlur()
        self.layout().addWidget(self.const_blur.button)
        self.const_blur.clicked.connect(self.toggle_constant_blur)

        # Eraser
        self.eraser = Eraser()
        self.layout().addWidget(self.eraser.button)
        self.eraser.clicked.connect(self.toggle_constant_blur)


        self.active_tool = self.blur_brush

    def register_video(self, videoWidget):
        print("Registering Video", videoWidget)
        videoWidget.mouse_down.connect(lambda data: self.on_mouse_down(data[0], data[1]))
        videoWidget.mouse_move.connect(lambda data: self.on_mouse_move(data[0], data[1]))
        videoWidget.mouse_up.connect(lambda data: self.on_mouse_up(data[0], data[1]))
        videoWidget.scroll_event.connect(self.on_brush_size_changed)
        # videos = video_blurring_window.videoSpace.findChildren(VideoWidget, name="VideoWidget")

    def on_mouse_down(self, video, click_location):
        self.active_tool.mouse_down(video, click_location)
    
    def on_mouse_move(self, video, click_location):
        self.active_tool.mouse_move(video, click_location)

    def on_mouse_up(self, video, click_location):
        self.active_tool.mouse_up(video, click_location)

    def on_brush_size_changed(self, video, d_size, x, y):
        self.active_tool.brush_size += d_size*5
        if self.active_tool.brush_size <= 0:
            self.active_tool.brush_size = 0
        self.active_tool.mouse_scroll(video, d_size, x, y)

        print("Brush size set to", self.active_tool.brush_size)


    def toggle_blur_brush(self):
        print("Enable Brush")
        self.active_tool = self.blur_brush
        self.active_tool_changed.emit(self.active_tool)

    def toggle_constant_blur(self):
        print("Enable constant blur")
        self.active_tool = self.const_blur
        self.active_tool_changed.emit(self.active_tool)

    def toggle_erase(self):
        print("Enable Eraser")
        self.active_tool = self.eraser
        self.active_tool_changed.emit(self.active_tool)
