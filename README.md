# FaceBlurring
A tool for blurring faces in videos. Intended use is for blurring PII data.

## Setup
1. Install [Python 3.x](python.org)
2. (optional) create a virtual environment
   1. `pip install virtualenv`
   2. `cd /path/to/repo/FaceBlurring/`
   3. `python -m venv myvirtualenv`
   4. Workon the virtual environment
      1. Windows: `./myvirtualenv/Scripts/Activate.bat`
      2. Unix: `source ./myvirtualenv/Scripts/activate` or sometimes it is in `./myvirtualenv/bin/activate`
3. Install Qt: `pip install PyQt5`
4. Install OpenCV: `pip install opencv-python`
5. Run the application `python ./Qt_Interface/main.py`

### Bugs?
`DirectShowPlayerService::doRender: Unresolved error code 0x80040266 (IDispatch error #102)` on Windows
1. You're missing some video drivers.
2. Go to [LAV Filter](http://forum.doom9.org/showthread.php?t=156191) and download (scroll down to 'Download' and install the binaries. Direct link to download [here](https://files.1f0.de/lavf/LAVFilters-0.74.1.exe))
3. Personally I add the H.264 driver. I don't know if you need it though
4. It should run now.