# file management
import os
import shutil
import errno
import glob
from pathlib import Path

# getting yt frames and image processing
import yt_dlp as youtube_dl
import cv2

# image ocr and text processing
import pytesseract
import re

# data logging
import csv

def mkdir_img(path="bin/img"):
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

def save_frame(frame, id, type, save_flag=True):
    if save_flag == True:
        type = re.sub(' ','',type)
        filename = r"bin/img/"+repr(id)+type+".png"
        cv2.imwrite(filename.format(),frame)

def is_ready(text):
    return any((
        text == "READY",
        text == "REAOY"
        ))

def read_frame(frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, regex='[^A-Za-z0-9]+', extensive=False, time_id=0, description=""):
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

    if extensive:
        psm11 =  pytesseract.image_to_string(frame_out, config='--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXY')
        psm13 =  pytesseract.image_to_string(frame_out, config='--psm 13 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXYZ')

        psm11_out = re.sub(regex,'',psm11)
        psm13_out = re.sub(regex,'',psm13)

        return psm11_out, psm13_out

    else:
        psm11 =  pytesseract.image_to_string(frame_out, config="--psm 11")

        psm11_out = re.sub(regex,'',psm11)

        return psm11_out

def match_object(frame_in, xa, xb, ya, yb):
    frame = frame_in[ya:yb , xa:xb]
    template = cv2.imread("assets/empty_dot.png", cv2.IMREAD_GRAYSCALE)

    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)

    # print(f"[{res[2,2]}],[{res[2,15]}],[{res[2,27]}]")
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
    def __init__(self, youtube_url, format_id, log_path=r"bin/log.csv", img_path=r"/bin/img"):
        #save paths
        self.url = youtube_url
        self.log_path = log_path
        self.img_path = "/bin/"+img_path

        #extract metadata with youtube-dl
        ydl_opts={}
        ydl=youtube_dl.YoutubeDL(ydl_opts)
        info_dict=ydl.extract_info(self.url, download=False)
        
        #get url for format
        formats = info_dict.get('formats',None)
        for f in formats:
            if f.get('format_id') == format_id:
                direct_url = f.get('url')
                pass

        #create cv2 object using url
        self.playback_time = 0
        self.cap = cv2.VideoCapture(direct_url)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, self.playback_time)

        #get video length
        self.video_length = info_dict.get('duration')
        
        #get video display_id for url reconstruction
        self.video_id = info_dict.get('display_id')

        #get video upload date
        self.upload_date = info_dict.get('upload_date')

        #find log file, or create if not present
        if not Path("bin/log.csv").exists():
            Path("bin").mkdir(parents=True, exist_ok=True)
            with open("bin/log.csv","x") as file:
                pen = csv.writer(file)
                pen.writerow([
                                'VOD_Date',
                                'VOD_Timestamp',
                                'Opponent_Name',
                                'Opponent_Fighter',
                                'Opponent_Rank',
                                'Match_Count',
                                'Match_Outcome',
                                'Postmatch_Rating',
                                'Youtube_Link'])
                
        #create new img/ diretory
        Path("bin/img").mkdir(parents=True, exist_ok=True)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret: #figure out better error handling
            print(f"[DEBUG@{self.get_time()}] frame error")
        return frame

    def skip_forward(self,interval):
        self.playback_time+=interval
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time)) # advance by interval

    def get_time(self):
        return round(self.playback_time,2)
    
    def get_url(self):
        return f"https://youtu.be/{self.video_id}?t={int(self.playback_time)}"
    
    def new_lobby(self, opponent_name, opponent_fighter, opponent_rank):
        self.opponent_name = opponent_name
        self.opponent_fighter = opponent_fighter
        self.opponent_rank = opponent_rank
        self.match_count = 0
        self.match_link = self.get_url()

    def rematch(self):
        self.match_link = self.get_url()

    def match_result(self, match_outcome, postmatch_rating):
        self.match_count += 1
        self.match_outcome = match_outcome
        self.postmatch_rating = postmatch_rating

    def end_lobby(self):
        self.opponent_name = None
        self.opponent_fighter = None
        self.opponent_rank = None
        self.match_count = None
        self.match_outcome = None
        self.postmatch_rating = None

    def save_result(self):
        with open(self.log_path, "a") as csvfile:
                log = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                log.writerow([
                                self.upload_date,
                                int(self.playback_time),
                                self.opponent_name,
                                self.opponent_fighter,
                                self.opponent_rank,
                                self.match_count,
                                self.match_outcome,
                                self.postmatch_rating,
                                self.match_link])

if __name__ == "__main__":
    #enable debug output
    save_flag = True

    #parameters
    url = "https://www.youtube.com/watch?v=NKpNzW7lXk0"
    setup_interval = 600 # soft
    pregame_interval = 2
    ingame_interval = 5
    postgame_interval = 0.3
    start_rating = 28480

    #alphanumeric sort key from https://stackoverflow.com/a/2669120
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]

    #import rank images
    rank_images = [cv2.imread(file) for file in sorted(glob.glob("assets/ranks_small/*.png"), key=alphanum_key)]
    filenames = sorted(glob.glob("assets/ranks_small/*.png"), key=alphanum_key)
    match_val = [None]*len(rank_images)
    rank_names = []

    #match result dot
    dot_template = cv2.imread('assets/dot.png', cv2.IMREAD_GRAYSCALE)

    #opponent fighter crop widths for ocr
    crop_widths = [850, 980, 1100]

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

    #game stats
    yt_link = url.split("=")[1]
    timestamp = None
    opponent_name = None
    opponent_rank = None
    opponent_fighter = None
    rating = start_rating
    outcome = None

    # Tekken 8 Rank Tracker - Finite State Machine
    #initial state
    state = "before"

    #tekken after counter
    no_fps = 0

    #set video capture
    yt = YoutubeCapture(url, '136')

    if save_flag == True:
        print(f"\n\n[DEBUG@{yt.get_time()}] State Machine Starting")

    #finite state machine
    while True:
        if yt.playback_time >= yt.video_length:
            print(f"[DEBUG@{yt.get_time()}] VOD finished")
            state == "after"

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
                print(f"[EVENT@{yt.get_time()}] Tekken Launched")

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

            #check if fps counter is present
            fps_temp = read_frame(
                            frame_in=frame,
                            xa=0,
                            xb=60,
                            ya=0,
                            yb=25,
                            time_id=1,
                            description='fps')
            #if fps counter is not present
            if not "fps" in fps_temp:
                #increment counter
                no_fps += 1
                #if no fps counter for 5 minutes, assume that tekken has been closed
                if no_fps > 150:
                    print(f"[EVENT@{yt.get_time()}] Tekken Closed")

                    state = "after"
            #reset tracker
            else:
                no_fps = 0

            #read text from cropped frame
            trigger = read_frame(
                            frame_in=frame, 
                            xa=600, 
                            xb=670, 
                            ya=530, 
                            yb=560, 
                            threshold=190,
                            time_id=yt.get_time(),
                            description=f"{state}_tSTAGE")
            #check for trigger
            if "STAGE" in trigger:
                print(f"[EVENT@{yt.get_time()}] Entering Lobby")

                #check if delayed enter into training
                kazuya_temp = read_frame(
                                frame_in=frame, 
                                xa=1060, 
                                xb=1230, 
                                ya=520, 
                                yb=570, 
                                time_id=yt.get_time(),
                                description=f"{state}_kazuya")
                #if entering training
                if "KAZUYA" in kazuya_temp:
                    #increment video playback time
                    yt.skip_forward(pregame_interval)
                #if entering match
                else:
                    valid_fighter = False
                    while not valid_fighter:
                        #find opponent fighter
                        for width in crop_widths:
                            fighter_temp = read_frame(
                                        frame_in=frame, 
                                        xa=width, 
                                        xb=1250, 
                                        ya=450, 
                                        yb=500,
                                        extensive=True,
                                        time_id=yt.get_time(),
                                        description=f"{state}_opponent fighter")
                            #check if valid fighter
                            for fighter in fighter_list:
                                for string in fighter_temp:
                                    if fighter in string:
                                        opponent_fighter = fighter
                                        valid_fighter = True

                                        #find opponent name
                                        opponent_name = read_frame(
                                            frame_in=frame,
                                            xa=830,
                                            xb=1130,
                                            ya=540,
                                            yb=570,
                                            time_id=yt.get_time(),
                                            description=f"{state}_opponent name")
                                        
                                        #find opponent rank
                                        frame_rank = frame[530:575, 1140:1230]
                                        for idx, rank_img in enumerate(rank_images):
                                            res = cv2.matchTemplate(frame_rank, rank_img, cv2.TM_SQDIFF)
                                            match_val[idx] = cv2.minMaxLoc(res)[0]
                                        index_min = min(range(len(match_val)), key=match_val.__getitem__)
                                        opponent_rank = rank_names[index_min]

                                        yt.new_lobby(opponent_name,opponent_fighter,opponent_rank)
                                        print(f"[EVENT@{yt.get_time()}] Starting match against {opponent_name} ({opponent_fighter} - {opponent_rank})")

                                        #advance video playback by minimum match length
                                        yt.skip_forward(60)

                                        #change state
                                        state = "in game"

                                        break
                                else:
                                    continue
                                break
                            else:
                                continue
                            break
                        #if invalid fighter, check for training and increment
                        else:
                            #check if delayed enter into training ('kazuya' text can be missed by ocr during an animation)
                            kazuya_temp = read_frame(
                                            frame_in=frame, 
                                            xa=1060, 
                                            xb=1230, 
                                            ya=520, 
                                            yb=570, 
                                            time_id=yt.get_time(),
                                            description=f"{state}_kazuya")
                            #if entering training
                            if "KAZUYA" in kazuya_temp:
                                print(f"[EVENT@{yt.get_time()}] Mistaken. Leaving Lobby")

                                #increment video playback time
                                yt.skip_forward(pregame_interval)

                                #exit loop since not entering lobby
                                break
                            #increment manually since in while loop
                            else:
                                #read frames until fighter is legible
                                #advance video playback
                                yt.skip_forward(0.5)

                                #capture new frame
                                frame = yt.get_frame()
                                #img log
                                save_frame(frame, yt.get_time(), state)                     
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
                            yb=525,
                            time_id=yt.get_time(),
                            description=f"{state}_tRating")
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
                    print(f"[EVENT@{yt.get_time()}] Match concluded")

                    #change state
                    state = "post game"

        if state == "post game":
            #capture new frame
            frame = yt.get_frame()
            #img log
            save_frame(frame, yt.get_time(), state)

            #search for dots, indicating no rematch possible
            player_dots, opponent_dots = count_match_dots(frame)
            # print(f"({yt.get_time()}): {player_dots}/3 and {opponent_dots}/3")
            if player_dots == -1 or opponent_dots == -1:
                #maybe .5 seconds for interval
                yt.skip_forward(3) #consider increasing to 2-5 seconds from 0.5 seconds
            else:
                #read new rating value
                rating_temp = read_frame(
                                frame_in=frame,
                                xa=530,
                                xb=630,
                                ya=490,
                                yb=525,
                                time_id=yt.get_time(),
                                description=f"{state}_rating")
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
                    #determine match outcome
                    if(rating_temp < rating):
                        outcome = "Loss"
                    else:
                        outcome = "Win"
                    #set rating
                    rating = rating_temp

                    yt.match_result(outcome, rating)
                    yt.save_result()
                    print(f"[EVENT@{yt.get_time()}] Match Result: {outcome} - Rating: {rating}")
                #check if final match
                if player_dots == 2 or opponent_dots == 2:
                    #set outcome
                    if player_dots == 2:
                        outcome = "Win"
                    else:
                        outcome = "Loss"

                    yt.end_lobby()
                    print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                    #clear opponent variables
                    opponent_fighter = None
                    opponent_name = None
                    opponent_rank = None

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
                                    description=f"{state}_player ready")
                        opponent_ready = read_frame(
                                    frame_in=frame,
                                    threshold=50,
                                    xa=1210,
                                    xb=1260,
                                    ya=550,
                                    yb=580,
                                    time_id=yt.get_time(),
                                    description=f"{state}_opponent ready")
                        if is_ready(player_ready) and is_ready(opponent_ready):
                            yt.rematch()
                            print(f"[EVENT@{yt.get_time()}] Starting rematch against {opponent_name} ({opponent_fighter} - {opponent_rank})")
                                
                            #advance video playback by minimum match length
                            yt.skip_forward(90) #consider increasing from 60
                            
                            #change state
                            state = "in game"

                            break
                        
                        #check for leaving match
                        frame_black_cropped = frame[250:300, 500:800]
                        frame_black_grey = cv2.cvtColor(frame_black_cropped, cv2.COLOR_BGR2GRAY)
                        if cv2.countNonZero(frame_black_grey) == 0:
                            yt.end_lobby()
                            print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

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