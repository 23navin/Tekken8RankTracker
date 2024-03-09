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

def read_frame(frame_in, xa=0, xb=0, ya=0, yb=0, threshold=200, time_id=0, description=""):
    if xb > 0 or yb > 0:
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_blackwhite = cv2.threshold(frame_greyscale, threshold, 255, cv2.THRESH_BINARY)[1]
        frame_out = frame_blackwhite
    else:
        frame_out = frame_in
    
    if time_id > 0:
        save_frame(frame_out, time_id, description)

    text =  pytesseract.image_to_string(frame_out, config="--psm 11")
    text_out = re.sub('[^A-Za-z0-9]+','',text)
    return text_out

def cv2_read(VideoCapture, state):
    #read next frame
    ret, frame = VideoCapture.read()
    if not ret: #figure out better error handling
        if save_flag == True:
            print(f"<DEBUG>frame error [{state}]")
    return frame

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
            print(f"<DEBUG>frame error @ [{self.playback_time}:.2] seconds")
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
# frame=cv2.imread("img/4611.100000000022training.png")

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
    print("\n\n<DEBUG>State Machine Starting")
    
while True:
    if state == "before":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), "pregrame")

        #read text from cropped frame
        trigger = read_frame(
                        frame_in=frame, 
                        xa=600, 
                        xb=690, 
                        ya=570, 
                        yb=590, 
                        time_id=yt.get_time(),
                        description="pregrame_crop")

        #check for trigger
        if "RankedMatch" in trigger:
            print(f"<GAME EVENT>Tekken Launched at {yt.get_time()} seconds")

            #change state
            state = "pre game"
        else:
            #increment video playback time
            yt.skip_forward(setup_interval)
    
    if state == "pre game":
        #capture new frame
        frame = yt.get_frame()
        
        #img log
        save_frame(frame, yt.get_time(), "training")

        #read text from cropped frame
        trigger = read_frame(
                        frame_in=frame, 
                        xa=600, 
                        xb=670, 
                        ya=530, 
                        yb=560, 
                        time_id=yt.get_time(),
                        description="training_crop")

        #check for trigger
        if "STAGE" in trigger:
            while True:
                #find opponent fighter
                fighter_temp = read_frame(
                            frame_in=frame, 
                            xa=770, 
                            xb=1250, 
                            ya=450, 
                            yb=500, 
                            time_id=yt.get_time(),
                            description="character")
                
                #check if valid fighter
                if fighter_temp in fighter_list:
                    opponent_fighter = fighter_temp
                    break
                else:
                    #read frames until fighter is legible
                    #advance video playback
                    yt.skip_forward(0.5)

                    #capture new frame
                    frame = yt.get_frame()
                    
                    #img log
                    save_frame(frame, yt.get_time(), "training")

            #find opponent name
            opponent_name = read_frame(
                frame_in=frame,
                xa=830,
                xb=1130,
                ya=540,
                yb=570,
                time_id=1,
                description="pregame_name")
            
            #find opponent rank
            frame_rank = frame[530:575, 1140:1230]
            for idx, rank_img in enumerate(rank_images):
                res = cv2.matchTemplate(frame_rank, rank_img, cv2.TM_SQDIFF)
                match_val[idx] = cv2.minMaxLoc(res)[0]

            index_min = min(range(len(match_val)), key=match_val.__getitem__)
            opponent_rank = rank_names[index_min]

            print(f"<GAME EVENT>Starting match against {opponent_name} ({opponent_fighter} - {opponent_rank}) at {yt.get_time()} seconds")

            #advance video playback by minimum match length
            yt.skip_forward(60)

            #change state
            state = "in game"
        else:
            #increment video playback time
            yt.skip_forward(pregame_interval)

    if state == "in game":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), "ingame")

        #search for number, indicating post game
        trigger = read_frame(
                        frame_in=frame,
                        xa=530,
                        xb=630,
                        ya=490,
                        yb=530,
                        time_id=yt.get_time(),
                        description="ingame_trigger"
        )
        #if number is present, change state
        try:
            trigger = int(re.sub(r'\D','',trigger))
        except ValueError:
            #increment video playback time
            yt.skip_forward(ingame_interval)
        else:
            if (rating - 1000) <= trigger <= (rating + 1000):
                print(f"<GAME EVENT>Match concluded at {yt.get_time()} seconds")

                #change state
                state = "post game"

    if state == "post game":
        #capture new frame
        frame = yt.get_frame()

        #img log
        save_frame(frame, yt.get_time(), "postgame")

        #search for black screen, indicating ...
        frame_trigger = frame[250:300, 500:800]
        frame_trigger_grey = cv2.cvtColor(frame_trigger, cv2.COLOR_BGR2GRAY)
        if cv2.countNonZero(frame_trigger_grey) == 0:
            #determine match outcome
            if(new_rating < rating):
                outcome = "Loss"
            else:
                outcome = "Win"

            #set rating
            rating = new_rating
            new_rating = None
            print(f"<GAME EVENT>Match Result: {outcome} - Rating: {rating}")
            print(f"<GAME EVENT>Leaving lobby with {opponent_name} at {yt.get_time()}")

            #advance video playback by minimum pre game length
            yt.skip_forward(6)
            
            #change state
            state = "pre game"
        else:
            #update rating
            rating_temp = read_frame(
                            frame_in=frame,
                            xa=530,
                            xb=630,
                            ya=490,
                            yb=530,
                            time_id=yt.get_time(),
                            description="postgame_rating"
            )
            #if number is present, change state
            try:
                rating_temp = int(re.sub(r'\D','',rating_temp))
            except ValueError:
                pass
            else:
                new_rating = rating_temp

            #search for ready signals, indicating a rematch
            ready1 = read_frame(
                        frame_in=frame,
                        threshold=50,
                        xa=1220,
                        xb=1270,
                        ya=480,
                        yb=500,
                        time_id=yt.get_time(),
                        description="postgame_ready1"
            )

            ready2 = read_frame(
                        frame_in=frame,
                        threshold=50,
                        xa=1210,
                        xb=1260,
                        ya=550,
                        yb=580,
                        time_id=yt.get_time(),
                        description="postgame_ready2"
            )

            #check if both players want to rematch
            if (("READY" in ready1) or ("REAOY" in ready1)) and (("READY" in ready2) or ("REAOY" in ready2)):
                #determine match outcome
                if(new_rating < rating):
                    outcome = "Loss"
                else:
                    outcome = "Win"

                #set rating
                rating = new_rating
                new_rating = None

                print(f"<GAME EVENT>Match Result: {outcome} - Rating: {rating}")
                print(f"<GAME EVENT>Starting rematch against {opponent_name} ({opponent_fighter} - {opponent_rank}) at {yt.get_time()} seconds")
                
                #advance video playback by minimum match length
                yt.skip_forward(60)
                
                #change state
                state = "in game"
            else:
                #increment video playback time
                yt.skip_forward(postgame_interval)