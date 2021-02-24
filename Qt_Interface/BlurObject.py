import numpy, cv2

class BlurStrand:
    def __init__(self, videoObject, display_resolution, video_resolution):
        self.video = videoObject
        self.__points = []
        self.display_resolution = display_resolution
        self.video_resolution = video_resolution
        self.start_frame = None
        self.end_frame = None

    def addPoint(self, frame, position, size, display_resolution=None):
        if display_resolution is None:
            display_resolution = self.display_resolution
        self.__points.append(BlurPoint(frame, position, size, display_resolution, self.video_resolution))

    def __repr__(self) -> str:
        return "Blur from frame {} to {}".format(self.start_frame, self.end_frame)

    def __str__(self) -> str:
        return self.__repr__()

    def complete(self):
        self.start_frame, self.end_frame = self.__points[0].index, self.__points[-1].index

    def checkBlurFrame(self, index, frame):
        if (self.start_frame <= index <= self.end_frame):

            strand_index = index - self.start_frame
            point = self.__points[strand_index]
            print("Blur frame", index, "at", point)
            point.blur_frame(frame)



class BlurPoint:

    blur_strength = 50

    def __init__(self, frame_index, position, size, display_resolution, video_resolution):
        self.index = frame_index
        self.x = position[0]
        self.y = position[1]
        self.size = size

        self.display_resolution = display_resolution
        self.video_resolution = video_resolution

    @property
    def stroke_size_for_display(self):
        return self.size * self.display_resolution[0]

    @property
    def stroke_size_for_video(self):
        return self.size * self.video_resolution[0]

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

        return {
            "position": {
                "x": x, 
                "y": y
            },
            "size": self.stroke_size_for_video
        }

    def blur_frame(self, frame):
        '''
        Blurs the passed frame based on this objects parameters.
        Passed frame should be a numpy array from opencv
        '''
        
            
        # Blur
        maskShape = (frame.shape[0], frame.shape[1], 1)
        # mask = numpy.full(maskShape, 0, dtype=numpy.uint8)

        y_start = int(self.y)
        y_end = int(self.y + self.stroke_size_for_video)
        x_start = int(self.x)
        x_end = int(self.x + self.stroke_size_for_video)
        
        frame[y_start:y_end, x_start:x_end] = cv2.blur(
            frame[y_start:y_end, x_start:x_end],
            (self.blur_strength, self.blur_strength))

    def blur_display(self, widget):
        '''
        Blurs the portion of the widget based on this objects' parameters.
        '''
        raise Exception("Not Implemented")

    def __repr__(self):
        return "{} size blur at ({}, {}) on frame {}".format(self.size, self.x, self.y, self.index)
    def __str__(self):
        return self.__repr__()

    