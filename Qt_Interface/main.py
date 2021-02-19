from PyQt5.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
import Video, Sidebar

def loadVideo():
    vid = Video.VideoWidget.loadVideo(None, None)
    videoLayout.addWidget(vid)

# Create Window with widget
app = QApplication([])
window = QWidget()
layout = QVBoxLayout()
window.setLayout(layout)

# Upper
upper = QWidget()
upperLayout = QHBoxLayout()
upper.setLayout(upperLayout)
layout.addWidget(upper)

# Bottom Timeline
timeline = QWidget()
layout.addWidget(timeline)

# Sidebar
sidebar = Sidebar.SidebarWidget()
upperLayout.addWidget(sidebar)

# Center for videos
videoSpace = QWidget()
videoLayout = QHBoxLayout()
videoSpace.setLayout(videoLayout)
upperLayout.addWidget(videoSpace)



window.show()
app.exec_()