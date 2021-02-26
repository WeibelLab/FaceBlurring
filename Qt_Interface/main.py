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

# print(window.objectName())
# print(window.accessibleName())
# print(window.dynamicPropertyNames())
# print(window.winId())

# print(window.metaObject())
# meta = window.metaObject()
# meta.className()
# meta.classInfo(0)
# meta.property(0)
# meta.userProperty()

# classInfo = meta.classInfo()
# classInfo.name()
# classInfo.value()

# Set Stylesheet
# qss = "./darktheme.qss"
# with open(qss, 'r') as f:
#     app.setStyleSheet("\n".join(f.readlines()))

# Upper
upper = QWidget()
upperLayout = QHBoxLayout()
upper.setLayout(upperLayout)
layout.addWidget(upper)

# Bottom Timeline
timeline = QWidget()
layout.addWidget(timeline)
timeline.setMinimumHeight(100)


# Center for videos
videoSpace = QWidget()
videoLayout = QHBoxLayout()
videoSpace.setLayout(videoLayout)

# Sidebar
sidebar = Sidebar.SidebarWidget(None, videoSpace)

# Add to GUI
upperLayout.addWidget(sidebar)
upperLayout.addWidget(videoSpace)



window.show()
app.exec_()