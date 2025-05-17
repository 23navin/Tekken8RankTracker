from cv2 import imwrite
from re import sub

from os.path import isdir
from os import makedirs
import shutil
import errno

# makes a temporary directory for img or video logging/debugging
def log_dir(path="bin/vid"):
    try:
        if isdir(path):
            shutil.rmtree(path)
    except:
        pass
    
    try:
        makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and isdir(path):
            pass
        else: raise


#save a frame as a png to img bin
def save_frame(frame, id, type, save_flag=True):
    """
    Saves a given frame as an image file if the save_flag is set to True.

    Args:
        frame (numpy.ndarray): The image frame to be saved.
        id (str): A unique identifier for the image file.
        type (str): A string representing the type or category of the image.
        save_flag (bool, optional): A flag to determine whether to save the frame. Defaults to True.

    Returns:
        None
    """
    if save_flag == True:
        type = sub(' ','',type)
        filename = f"bin/img/{id}{type}.png"
        imwrite(filename.format(),frame)
        
#time (hh:mm:ss.ms) to seconds
def time_to_seconds(time_str):
    """
    Convert a time string in the format 'hh:mm:ss.ms' to seconds.
    Args:
        time_str (str): A string representing time in the format 'hh:mm:ss' or 'mm:ss'.
    Returns:
        float: The total time in seconds.
    Raises:
        ValueError: If the input string is not in the expected format.
    """
    time_parts = time_str.split(':')
    if len(time_parts) == 3:
        hours, minutes, seconds = map(float, time_parts)
    elif len(time_parts) == 2:
        hours = 0
        minutes, seconds = map(float, time_parts)
    else:
        raise ValueError("Invalid time format. Expected hh:mm:ss or mm:ss.")
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

#convert seconds to milli-seconds
def sec_to_ms(sec):
    """
    Convert seconds to milliseconds.

    Args:
        sec (float): Time in seconds.

    Returns:
        float: Time converted to milliseconds.
    """
    return sec*1000