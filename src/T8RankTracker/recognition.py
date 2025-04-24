import numpy as np
import cv2
import glob

# image ocr and text processing
import re
import pytesseract
from difflib import SequenceMatcher

from src.T8RankTracker.helpers import save_frame

#macro-like function to check if a string == READY or REAOY (tesseract has a hard time distinguishing the two)
def is_ready(text):
    return any((
        "READY" in text.upper(),
        "REAOY" in text.upper()
        ))

def is_TEKKENPROWESS(text):
    val = SequenceMatcher(None, "TEKKENPROWESS", text).ratio()
    return val > 0.4

def is_match(reference, input_text, threshold=0.4):
    val = SequenceMatcher(None, reference, input_text).ratio()
    return val > threshold

class FrameRecognition:
    crop_widths = [850, 980, 1090, 1100]
    kernel=np.ones((1,1),np.uint8)

    def __init__(self):
        #alphanumeric sort key from https://stackoverflow.com/a/2669120
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]

        #import rank images
        self.rank_images = [cv2.imread(file) for file in sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)]
        self.filenames = sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)
        self.rank_names = []
        for filename in self.filenames:
            name = filename.split("_")[1]
            name = name.split(".")[0]

            self.rank_names.append(name)

    def read_text(self, frame_in, xa, xb, ya, yb, threshold=175, invert=True, noisy=False, regex='[^A-Za-z0-9-]+', time_id=0, description="", save_flag=False):
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_blackwhite = cv2.threshold(frame_greyscale, threshold, 255, cv2.THRESH_BINARY)[1]
        
        if invert:
            frame_border = cv2.copyMakeBorder(frame_blackwhite, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[0,0,0])
            frame_invert = cv2.bitwise_not(frame_border)
        else:
            frame_border = cv2.copyMakeBorder(frame_blackwhite, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255,255,255])
            frame_invert = frame_border
        
        if noisy:

            frame_eroded = cv2.dilate(frame_invert, self.kernel, anchor=(0,0), iterations=2)
            frame_dinvert = cv2.bitwise_not(frame_eroded)
            frame_dilated=cv2.dilate(frame_dinvert,self.kernel,anchor=(0,0),iterations=2)
            frame_udinvert = cv2.bitwise_not(frame_dilated)

            psm13 =  pytesseract.image_to_string(frame_udinvert, config="--psm 6")
            psm13_out = re.sub(regex,'',psm13)

            if time_id > 0:
                save_frame(frame_udinvert, time_id, f"{description},{psm13_out}", save_flag)

            return psm13_out
        else:
            frame_dinvert = cv2.bitwise_not(frame_invert)
            frame_dilated=cv2.dilate(frame_dinvert,self.kernel,anchor=(0,0),iterations=2)
            frame_udinvert = cv2.bitwise_not(frame_dilated)

            psm11 =  pytesseract.image_to_string(frame_udinvert, config="--psm 11")
            psm11_out = re.sub(regex,'',psm11)

            if time_id > 0:
                save_frame(frame_udinvert, time_id, f"{description},{psm11_out}", save_flag)

            return psm11_out

    def read_rating(self, frame_in, xa=530, xb=630, ya=496, yb=522, time_id=0, description="", save_flag=False):
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_blackwhite = cv2.threshold(frame_greyscale, 175, 255, cv2.THRESH_BINARY)[1]
        frame_invert = cv2.bitwise_not(frame_blackwhite)
        frame_eroded = cv2.dilate(frame_invert, self.kernel, anchor=(0,0), iterations=2)
        frame_border = cv2.copyMakeBorder(frame_eroded, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255,255,255])

        psm11 =  pytesseract.image_to_string(frame_border, config="--psm 11")
        psm11_out = re.sub('[^0-9]+','',psm11)

        if time_id > 0:
            save_frame(frame_border, time_id, f"{description},{psm11_out}", save_flag)

        return psm11_out

    def read_fighter(self, frame_in, xa=0, xb=0, ya=0, yb=0, regex='[^A-Za-z0-9]+', time_id=0, description="", save_flag=False):
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        lower = np.array([216, 190 , 140])
        upper = np.array([255, 255, 255])
        frame_filtered = cv2.inRange(frame_resized, lower, upper)
        frame_inverted = cv2.bitwise_not(frame_filtered)
        frame_eroded = cv2.dilate(frame_inverted, self.kernel, anchor=(0,0), iterations=2)

        frame_out = frame_eroded

        psm11 = pytesseract.image_to_string(frame_out, config='--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXY')
        psm13 = pytesseract.image_to_string(frame_out, config='--psm 13 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXYZ')

        psm11_out = re.sub(regex,'',psm11)
        psm13_out = re.sub(regex,'',psm13)

        if time_id > 0:
            save_frame(frame_out, time_id, f"{description},{psm11_out},{psm13_out}", save_flag)

        return psm11_out, psm13_out
    
    def read_rank(self, frame_in, xa=0, xb=0, ya=0, yb=0, time_id=0, description="", save_flag=False):
        match_val = [None]*len(self.rank_images)

        frame_cropped = frame_in[ya:yb, xa:xb]
        for idx, rank_img in enumerate(self.rank_images):
            res = cv2.matchTemplate(frame_cropped, rank_img, cv2.TM_SQDIFF)
            match_val[idx] = cv2.minMaxLoc(res)[0]
        index_min = min(range(len(match_val)), key=match_val.__getitem__)

        rank_name = self.rank_names[index_min]

        save_frame(frame_cropped, time_id, f"{description},{rank_name}", save_flag)
        
        return rank_name
    
    def match_object(self, frame_in, xa, xb, ya, yb):
        frame = frame_in[ya:yb , xa:xb]
        template = cv2.imread("assets/empty_dot.png", cv2.IMREAD_GRAYSCALE)

        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        
        return res
    
    def count_match_dots(self, frame_in):
        player_res = self.match_object(frame_in, 1004, 1042, 510, 524)
        player_dots = 0

        opponent_res = self.match_object(frame_in, 1004, 1042, 534, 548)
        opponent_dots = 0

        thr = 0.3
        dot_locations = [2, 15, 27]
        winloss = None

        for loc in dot_locations:
            if player_res[2, loc] < thr and opponent_res[2,loc] < thr:
                return -1,-1,None
            
            if player_res[2, loc] > thr and opponent_res[2,loc] > thr:
                return player_dots, opponent_dots, winloss
            
            if player_res[2,loc] > thr:
                opponent_dots += 1
                winloss = "Loss"
            else:
                player_dots += 1
                winloss = "Win"

        return player_dots, opponent_dots, winloss