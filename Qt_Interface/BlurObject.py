from PyQt5.QtCore import Qt
import numpy, cv2

class BlurStrand:
    def __init__(self, videoObject, video_resolution):
        self.video = videoObject
        self.__points = []
        self.video_resolution = video_resolution
        self.start_frame = None
        self.end_frame = None
        self.video._blur_strands.append(self)

    def addPoint(self, frame, position, size):
        self.__points.append(BlurPoint(frame, position, size, self.video_resolution))

    def __repr__(self) -> str:
        return "Blur from frame {} to {}".format(self.start_frame, self.end_frame)

    def __str__(self) -> str:
        return self.__repr__()

    def complete(self, simplify=True):
        self.start_frame, self.end_frame = self.__points[0].index, self.__points[-1].index
        if simplify:
            self.simplify()
        
        self.video.newFrame.connect(self.blurFrame, type=Qt.DirectConnection)

    def simplify(self):
        # Clean up data

        # Get repeat frames and average the position
        consolidated = []
        ps = [] # store the points of a matching index
        for point_index, point in enumerate(self.__points):
            # Duplicates
            if point_index == 0:
                ps.append(point)
            elif point.index != ps[0].index or point_index == len(self.__points)-1:
                # Average
                x = sum([p.x for p in ps]) / len(ps)
                y = sum([p.y for p in ps]) / len(ps)
                size = sum([p.size for p in ps]) / len(ps)
                # Add to new list
                consolidated_point = BlurPoint(ps[0].index, (x, y), size, ps[0].resolution)
                consolidated.append(consolidated_point)

                # Fill in the blanks
                for i in range(point.index - ps[0].index -1):
                    index = consolidated_point.index + i + 1
                    consolidated.append(BlurPoint(
                        index,
                        (consolidated_point.x, consolidated_point.y),
                        consolidated_point.size,
                        consolidated_point.resolution
                    ))

                # Clear variables for next index
                ps = []
                ps.append(point)
            else:
                ps.append(point)
        

        print("Blur from", self.start_frame, "to", self.end_frame, "of", self.video.number_of_frames, "frames")
        print("p[0]", consolidated[0], "p[last]", consolidated[-1])

        self.__points = consolidated

    def checkBlurFrame(self, index) -> list:
        if (self.start_frame <= index <= self.end_frame):
            toblur = [point for point in self.__points if point.index == index]
            return toblur
        return []

    def blurFrame(self, index, frame):
        toblur = self.checkBlurFrame(index)
        for pt in toblur:
            pt.blur_frame(frame)

    def split_on(self, frame_index):
        ''' Splits the points in this blur object into 2 new blur objects.'''
        point = self.checkBlurFrame(frame_index)[0]
        pointIndex = self.__points.index(point)
        if pointIndex is 0:
            return [self]

        # Create a and b strands
        aStrand = BlurStrand(self.video, self.video_resolution)
        bStrand = BlurStrand(self.video, self.video_resolution)
        # Split points between a and b strands
        aStrand.__points = self.__points[:pointIndex]
        bStrand.__points = self.__points[pointIndex:]
        aStrand.complete(False)
        bStrand.complete(False)
        # Destroy self
        self.destroy()
        return [aStrand, bStrand]

    def destroy(self):
        self.video.newFrame.disconnect(self.blurFrame)
        self.video._blur_strands.remove(self)

    def serialize(self):
        out = {
            "video": self.video._video_path,
            "points": []
        }

        for point in self.__points:
            out["points"].append(point.serialize())

        return out

    @staticmethod
    def deserialize(data, videoWidget):
        strand = BlurStrand(videoWidget.video, videoWidget.video_resolution)
        points = []
        for point in data["points"]:
            points.append(BlurPoint.deserialize(point))

        strand.__points = points
        strand.complete(False)
        return strand





class BlurPoint:

    blur_strength = 50

    def __init__(self, frame_index, position, size, video_resolution):
        self.index = frame_index
        self.x = position[0]
        self.y = position[1]
        self.size = size

        self.resolution = video_resolution

    @property
    def stroke_size(self):
        return self.size

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

    def get_blur_region(self, frame=None):
        y_start = int(self.y - self.stroke_size/2)
        y_end = int(self.y + self.stroke_size/2)
        x_start = int(self.x - self.stroke_size/2)
        x_end = int(self.x + self.stroke_size/2)

        if (y_start == y_end or x_start == x_end):
            return None

        if frame is not None:
            # account for being out of frame
            if (y_start < 0):
                y_start = 0
            if (x_start < 0):
                x_start = 0
            if (y_end > frame.shape[0]):
                y_end = frame.shape[0]
            if (x_end > frame.shape[1]):
                x_end = frame.shape[1]

        return (x_start, y_start, x_end, y_end)


    def blur_frame(self, frame):
        '''
        Blurs the passed frame based on this objects parameters.
        Passed frame should be a numpy array from opencv
        '''
        ret = self.get_blur_region(frame)
        if ret is None:
            return

        x_start, y_start, x_end, y_end = ret
        
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

    def serialize(self):
        return {
            "frame": self.index,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "resolution": self.resolution
        }

    @staticmethod
    def deserialize(data):
        return BlurPoint(data["frame"], (data["x"], data["y"]), data["size"], data["resolution"])

    