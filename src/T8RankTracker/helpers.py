from cv2 import imwrite
from re import sub

#save a frame as a png to img bin
def save_frame(frame, id, type, save_flag=True):
    if save_flag == True:
        type = sub(' ','',type)
        filename = f"bin/img/{id}{type}.png"
        imwrite(filename.format(),frame)