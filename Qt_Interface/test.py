import cv2, os, sys, shutil, atexit

f = "../sample_assets/SampleVideo.mp4"

# Duplicate Video


# Create temp folder
if not os.path.exists(tmpFolder):
    os.mkdir(tmpFolder) # make folder
    def removeFolder(folder):
        print("Removing folder", folder)
        os.removedirs(folder)
    atexit.register(removeFolder, folder=tmpFolder)

# Create temp file
usable_file = os.path.join(tmpFolder, "_"+filename)
shutil.copyfile(absPath, usable_file) # copy file so we can edit it
def remove(filepath):
    print("Removing file", filepath)
    os.remove(filepath)
atexit.register(remove, filepath=usable_file)

# Open temp file
cap = cv2.VideoCapture(usable_file)
atexit.register(cap.release)
ret, frame = cap.read()
cv2.imshow("asdf", frame)
cv2.waitKey(0)