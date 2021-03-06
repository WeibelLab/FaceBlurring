import numpy, cv2

class BlurStrand:
    def __init__(self, videoObject, video_resolution):
        self.video = videoObject
        self.__points = []
        self.video_resolution = video_resolution
        self.start_frame = None
        self.end_frame = None

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

    def checkBlurFrame(self, index, frame):
        if (self.start_frame <= index <= self.end_frame):
            toblur = [point for point in self.__points if point.index == index]

            for pt in toblur:
                pt.blur_frame(frame)



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

    def blur_frame(self, frame):
        '''
        Blurs the passed frame based on this objects parameters.
        Passed frame should be a numpy array from opencv
        '''
        y_start = int(self.y - self.stroke_size/2)
        y_end = int(self.y + self.stroke_size/2)
        x_start = int(self.x - self.stroke_size/2)
        x_end = int(self.x + self.stroke_size/2)

        if (y_start == y_end or x_start == x_end):
            return
        
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

    