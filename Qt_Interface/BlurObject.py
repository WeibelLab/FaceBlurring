import numpy

class BlurStrand:
    def __init__(self, videoObject, display_resolution, video_resolution):
        self.video = videoObject
        self.__points = []
        self.display_resolution = display_resolution
        self.video_resolution = video_resolution

    def addPoint(self, frame, position, size, display_resolution=None):
        if display_resolution is None:
            display_resolution = self.display_resolution
        self.__points.append(BlurPoint(frame, position, size, display_resolution, self.video_resolution))

    def __repr__(self) -> str:
        return "Blur from frame {} to {}".format(self.__points[0].index, self.__points[-1].index)

    def __str__(self) -> str:
        return self.__repr__()


class BlurPoint:
    def __init__(self, frame_index, position, size, display_resolution, video_resolution):
        self.index = frame_index
        self.x = position[0]
        self.y = position[1]
        self.size = size

        self.display_resolution = display_resolution
        self.video_resolution = video_resolution

    def get(self):
        '''
        the position and size of the blur in the displayed coordinate system
        '''
        return {
            "position": {
                "x": self.x,
                "y": self.y
            },
            "size": self.size
        }

    def get_in_video_resolution(self):
        '''
        the position and size of the blur in the video's coordinate system
        '''
        x = numpy.interp(self.x, [0, self.display_resolution[0]], [0, self.video_resolution[0]])
        y = numpy.interp(self.y, [0, self.display_resolution[1]], [0, self.video_resolution[1]])
        size = numpy.interp(self.size, [0,1], [0, self.video_resolution[0]])

        return {
            "position": {
                "x": x, 
                "y": y
            },
            "size": size
        }

    def blur_frame(self, frame):
        '''
        Blurs the passed frame based on this objects parameters.
        Passed frame should be a numpy array from opencv
        '''
        raise Exception("Not Implemented")

    def blur_display(self, widget):
        '''
        Blurs the portion of the widget based on this objects' parameters.
        '''
        raise Exception("Not Implemented")

    