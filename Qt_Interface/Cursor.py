from PyQt5.QtGui import QCursor, QPixmap
import os

class Cursor(QCursor):

    folder = "./assets/Cursor"
    shape = "square"

    def __init__(self):
        pixmap = QPixmap(os.path.join(Cursor.folder, Cursor.shape+"_64.png"))
        super().__init__(pixmap, hotX=-1, hotY=-1)

    def set_size(self, size=64):
        new_cursor = self.scaled(size, size)
        Cursor.window.setCursor(QCursor(new_cursor, hotX=-1, hotY=-1))

