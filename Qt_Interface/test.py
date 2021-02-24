import cv2, numpy, atexit
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import *

app = QApplication([])
window = QWidget()
window.setLayout(QVBoxLayout())

class test(QWidget):
    # call_list = []
    call_list = pyqtSignal(numpy.ndarray)

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        atexit.register(self.cap.release)

        self.call_list.connect(test.blur)
        self.call_list.connect(test.superblur)

    def get(self):
        ret, frame = self.cap.read()

        cv2.imshow("Before", frame)

        # for f in call_list:
        #     f(frame)
        self.call_list.emit(frame)

        cv2.imshow("After", frame)
        cv2.waitKey(0)

    @staticmethod
    def blur(frame):
        height, width = frame.shape[0], frame.shape[1]
        print(width, height)

        y1 = int(height/4)
        y2 = int(3*y1)
        x1 = int(width/4)
        x2 = int(3*x1)
        frame[y1:y2, x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (23, 23))

        cv2.imshow("In Function", frame)

    @staticmethod
    def superblur(frame):
        value = 100
        height, width = frame.shape[0], frame.shape[1]
        print(width, height)

        y1 = int(height/4)
        y2 = int(3*y1)
        x1 = int(width/4)
        x2 = int(3*x1)
        frame = frame.copy()
        frame[y1:y2, x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (value, value))

        cv2.imshow("Super Function", frame)


tester = test()
window.layout().addWidget(tester)
tester.get()

window.show()
app.exec_()

