# file management
import os
import shutil
import errno
import glob

# getting yt frames and image processing
import yt_dlp as youtube_dl
import cv2

# image ocr and text processing
import pytesseract
import re

import numpy as np
from matplotlib import pyplot as plt

num = [5]
print(len(num))
#debugging
save_flag = True

def mkdir_img(path="img"):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except:
        pass

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def sec_to_ms(ms):
    return ms*1000

def save_frame(frame, id, type):
    if save_flag == True:
        filename = r"img/"+repr(id)+type+".png"
        cv2.imwrite(filename.format(),frame)

def is_ready(text):
    return any((
        text == "READY",
        text == "REAOY"
        ))

def read_frame(frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, time_id=0, description=""):
    if xb > 0 or yb > 0:
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_blackwhite = cv2.threshold(frame_greyscale, threshold, 255, cv2.THRESH_BINARY)[1]
        frame_invert = cv2.bitwise_not(frame_blackwhite)
        frame_out = frame_invert
    else:
        frame_out = frame_in
    
    if time_id > 0:
        save_frame(frame_out, time_id, description)

    text =  pytesseract.image_to_string(frame_out, config="--psm 13")
    text_out = re.sub('[^A-Za-z0-9]+','',text)
    return text_out

def match_object(frame_in, xa, xb, ya, yb):
    frame = frame_in[ya:yb , xa:xb]
    template = cv2.imread("empty_dot.png", cv2.IMREAD_GRAYSCALE)

    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    print(f"[{res[2,2]}],[{res[2,15]}],[{res[2,27]}]")
    # plt.subplot(211),plt.imshow(frame)
    # plt.subplot(212),plt.imshow(res,cmap = 'gray')
    
    return res

    # return (res > 0.8).sum()

def count_match_dots(frame_in):
    player_res = match_object(frame_in, 1004, 1042, 510, 524)
    player_dots = 0

    opponent_res = match_object(frame_in, 1004, 1042, 534, 548)
    opponent_dots = 0

    thr = 0.3
    dot_locations = [2, 15, 27]

    for loc in dot_locations:
        if player_res[2, loc] > thr and opponent_res[2,loc] > thr:
            return player_dots, opponent_dots
        
        if player_res[2,loc] > thr and opponent_res[2,loc] < thr:
            opponent_dots += 1
        elif opponent_res[2,loc] > thr and player_res[2,loc] < thr:
            player_dots += 1
        else:
            return -1,-1

    return player_dots, opponent_dots

class YoutubeCapture:
    def __init__(self, youtube_url, format_id):
        self.url = youtube_url
        self.playback_time = 0

        #youtube-dl
        ydl_opts={}
        ydl=youtube_dl.YoutubeDL(ydl_opts)
        info_dict=ydl.extract_info(self.url, download=False)
        formats = info_dict.get('formats',None)
        for f in formats:
            if f.get('format_id') == format_id:
                url = f.get('url')

        #create cv2 object
        self.cap = cv2.VideoCapture(url)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, self.playback_time)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret: #figure out better error handling
            print(f"<DEBUG@{self.get_time()}>frame error")
        return frame

    def skip_forward(self,interval):
        self.playback_time+=interval
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time)) # advance by interval

    def get_time(self):
        return round(self.playback_time,2)

#parameters
url = "https://www.youtube.com/watch?v=NKpNzW7lXk0"
setup_interval = 600 # soft
pregame_interval = 2
ingame_interval = 5
postgame_interval = 0.3
start_rating = 28480

#set video capture
yt = YoutubeCapture(url, '136')

#alphanumeric sort key from https://stackoverflow.com/a/2669120
convert = lambda text: int(text) if text.isdigit() else text
alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]

#import rank images
rank_images = [cv2.imread(file) for file in sorted(glob.glob("ranks_small/*.png"), key=alphanum_key)]
filenames = sorted(glob.glob("ranks_small/*.png"), key=alphanum_key)
match_val = [None]*len(rank_images)
rank_names = []

#match result dot
dot_template = cv2.imread('dot.png', cv2.IMREAD_GRAYSCALE)

#tekken 8 fighters list
fighter_list = ['KAZUYA',
                'JIN',
                'KING',
                'JUN',
                'PAUL',
                'LAW',
                'JACK8',
                'LARS',
                'XIAOYU',
                'NINA',
                'LEROY',
                'ASUKA',
                'LILI',
                'BRYAN',
                'HWOARANG',
                'CLAUDIO',
                'AZUCENA',
                'RAVEN',
                'LEO',
                'STEVE',
                'KUMA',
                'YOSHIMITSU',
                'SHAHEEN',
                'DRAGUNOV',
                'FENG',
                'PANDA',
                'LEE',
                'ALISA',
                'ZAFINA',
                'DEVILJIN',
                'VICTOR',
                'REINA']

for filename in filenames:
    # rank_small/16_shinryu.png
    name = filename.split("_")[2]
    name = name.split(".")[0]

    rank_names.append(name)

####
    
frame = cv2.imread("img/4227.0pre game.png")

# might need read_frame output a tuple of psm11 and psm13 for matching
# or take the time and do match templating
# fighter_temp = read_frame(
#             frame_in=frame, 
#             xa=850, 
#             xb=1230, 
#             ya=450, 
#             yb=500, 
#             time_id=1,
#             description=f"opponent fighter")

# #check if valid fighter
# for fighter in fighter_list:
#     if fighter in fighter_temp:
#         opponent_fighter = fighter
#         valid_fighter = True
#         break

# player_rounds , opponent_rounds = count_match_dots(frame)
# print(f"counted {player_rounds} v {opponent_rounds} round")

# frame_rank = frame[530:575, 1140:1230]
# for idx, rank_img in enumerate(rank_images):
#     res = cv2.matchTemplate(frame_rank, rank_img, cv2.TM_SQDIFF)
#     match_val[idx] = cv2.minMaxLoc(res)[0]
#     print(f"{rank_names[idx]} >> {match_val[idx]}")

# index_min = min(range(len(match_val)), key=match_val.__getitem__)
# opponent_rank = rank_names[index_min]

####

#clear img log
mkdir_img()

#game stats
yt_link = url.split("=")[1]
timestamp = None
opponent_name = None
opponent_rank = None
opponent_fighter = None
rating = start_rating
new_rating = None
outcome = None

# Tekken 8 Rank Tracker - Finite State Machine
state = "before"
if save_flag == True:
    print(f"\n\n<DEBUG@{yt.get_time()}>State Machine Starting")

#finite state machine
while True:
    if state == "before":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), state)

        #read text from cropped frame
        trigger = read_frame(
                        frame_in=frame, 
                        xa=600, 
                        xb=690, 
                        ya=570, 
                        yb=590, 
                        time_id=yt.get_time(),
                        description=f"{state}_tRankedMatch")

        #check for trigger
        if "RankedMatch" in trigger:
            print(f"<EVENT@{yt.get_time()}>Tekken Launched")

            #change state
            state = "pre game"
        #if no trigger, increment
        else:
            #increment video playback time
            yt.skip_forward(setup_interval)
    
    if state == "pre game":
        #capture new frame
        frame = yt.get_frame()
        
        #img log
        save_frame(frame, yt.get_time(), state)

        #read text from cropped frame
        trigger = read_frame(
                        frame_in=frame, 
                        xa=600, 
                        xb=670, 
                        ya=530, 
                        yb=560, 
                        time_id=yt.get_time(),
                        description=f"{state}_tSTAGE")

        #check for trigger
        if "STAGE" in trigger:
            print(f"<EVENT@{yt.get_time()}>Entering Lobby")

            #check if delayed enter into training
            kazuya_temp = read_frame(
                            frame_in=frame, 
                            xa=1060, 
                            xb=1230, 
                            ya=520, 
                            yb=570, 
                            time_id=yt.get_time(),
                            description=f"{state}_kazuya")
            
            if not "KAZUYA" in kazuya_temp:
                valid_fighter = False
                while not valid_fighter:
                    #find opponent fighter
                    fighter_temp = read_frame(
                                frame_in=frame, 
                                xa=770, 
                                xb=1250, 
                                ya=450, 
                                yb=500, 
                                time_id=yt.get_time(),
                                description=f"{state}_opponent fighter")
                    
                    #check if valid fighter
                    for fighter in fighter_list:
                        if fighter in fighter_temp:
                            opponent_fighter = fighter
                            valid_fighter = True
                            break
                    #if invalid fighter, increment manually since in while loop
                    else:
                        #read frames until fighter is legible
                        #advance video playback
                        yt.skip_forward(0.5)

                        #capture new frame
                        frame = yt.get_frame()
                        
                        #img log
                        save_frame(frame, yt.get_time(), state)
                    
                #find opponent name
                opponent_name = read_frame(
                    frame_in=frame,
                    xa=830,
                    xb=1130,
                    ya=540,
                    yb=570,
                    time_id=1,
                    description=f"{state}_opponent name")
                
                #find opponent rank
                frame_rank = frame[530:575, 1140:1230]
                for idx, rank_img in enumerate(rank_images):
                    res = cv2.matchTemplate(frame_rank, rank_img, cv2.TM_SQDIFF)
                    match_val[idx] = cv2.minMaxLoc(res)[0]

                index_min = min(range(len(match_val)), key=match_val.__getitem__)
                opponent_rank = rank_names[index_min]

                print(f"<EVENT@{yt.get_time()}>Starting match against {opponent_name} ({opponent_fighter} - {opponent_rank})")

                #advance video playback by minimum match length
                yt.skip_forward(60)

                #change state
                state = "in game"
        #if no trigger, increment
        else:
            #increment video playback time
            yt.skip_forward(pregame_interval)

    if state == "in game":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), state)

        #search for number, indicating post game
        trigger = read_frame(
                        frame_in=frame,
                        xa=530,
                        xb=630,
                        ya=490,
                        yb=530,
                        time_id=yt.get_time(),
                        description=f"{state}_tRating"
        )
        #check if number (rating) is present
        try:
            trigger = int(re.sub(r'\D','',trigger))
        #if number is not present, increment
        except ValueError:
            #increment video playback time
            yt.skip_forward(ingame_interval)
        #if number is present, change state
        else:
            #only change if valid number (filter out numbers picked up unintentionally)
            if (rating - 1000) <= trigger <= (rating + 1000):
                print(f"<EVENT@{yt.get_time()}>Match concluded")

                #advance by min
                #no skip is 7seconds
                # yt.skip_forward(5)
                #change state
                state = "post game"

    if state == "post game":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), state)

        #search for dots, indicating no rematch possible
        player_dots, opponent_dots = count_match_dots(frame)
        print(f"({yt.get_time()}): {player_dots}/3 and {opponent_dots}/3")

        if player_dots == -1 or opponent_dots == -1:
            #maybe .5 seconds for interval
            yt.skip_forward(0.5)
        else:
            #read new rating value
            rating_temp = read_frame(
                            frame_in=frame,
                            xa=530,
                            xb=630,
                            ya=490,
                            yb=530,
                            time_id=yt.get_time(),
                            description=f"{state}_rating"
            )

            #try to read a number from rating_temp
            try:
                rating_temp = int(re.sub(r'\D','',rating_temp))
            #if number is not present, increment
            except ValueError:
                #maybe .5 seconds for interval
                yt.skip_forward(0.5)
                continue

            #if number is present, update rating
            else:
                rating = rating_temp
            
            #check if final match
            if player_dots == 2 or opponent_dots == 2:
                #set outcome
                if player_dots == 2:
                    outcome = "Win"
                else:
                    outcome = "Loss"

                #clear opponent variables
                opponent_fighter = None
                opponent_name = None
                opponent_rank = None

                print(f"<EVENT@{yt.get_time()}>Match Result: {outcome} - Rating: {rating}")
                print(f"<EVENT@{yt.get_time()}>Leaving lobby with {opponent_name}")

                #advance video playback by minimum pre-game length
                yt.skip_forward(12)

                #change state
                state = "pre game"
            #check for rematch or black screen on postgame_interval
            else:
                while True:
                    #check for ready signals, indicating a rematch
                    player_ready = read_frame(
                                frame_in=frame,
                                threshold=50,
                                xa=1220,
                                xb=1270,
                                ya=480,
                                yb=500,
                                time_id=yt.get_time(),
                                description=f"{state}_player ready"
                    )

                    opponent_ready = read_frame(
                                frame_in=frame,
                                threshold=50,
                                xa=1210,
                                xb=1260,
                                ya=550,
                                yb=580,
                                time_id=yt.get_time(),
                                description=f"{state}_opponent ready"
                    )
                    
                    if is_ready(player_ready) and is_ready(opponent_ready):
                        print(f"<EVENT@{yt.get_time()}>Starting rematch against {opponent_name} ({opponent_fighter} - {opponent_rank})")
                            
                        #advance video playback by minimum match length
                        yt.skip_forward(60)
                        
                        #change state
                        state = "in game"
                        break
                    
                    #check for leaving match
                    frame_black_cropped = frame[250:300, 500:800]
                    frame_black_grey = cv2.cvtColor(frame_black_cropped, cv2.COLOR_BGR2GRAY)

                    if cv2.countNonZero(frame_black_grey) == 0:
                        print(f"<EVENT@{yt.get_time()}>Leaving lobby with {opponent_name}")

                        #advance video playback by minimum pre game length
                        yt.skip_forward(6)
                        
                        #change state
                        state = "pre game"
                        break
                    
                    #if neither, increment manually since in while loop
                    #advance video playback
                    yt.skip_forward(0.5)

                    #capture new frame
                    frame = yt.get_frame()
                    
                    #img log
                    save_frame(frame, yt.get_time(), state)