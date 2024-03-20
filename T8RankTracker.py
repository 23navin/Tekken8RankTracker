# file management
import os
import shutil
import errno
import glob
from pathlib import Path

# getting yt frames and image processing
import yt_dlp as youtube_dl
import numpy as np
import cv2

# image ocr and text processing
import pytesseract
import re

# data logging
import csv

#creates img log
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

#convert seconds to milli-seconds
def sec_to_ms(sec):
    return sec*1000

#save a frame as a png to img bin
def save_frame(frame, id, type, save_flag=True):
    if save_flag == True:
        type = re.sub(' ','',type)
        filename = f"bin/img/{id:.1f}{type}.png"
        cv2.imwrite(filename.format(),frame)

#macro-like function to check if a string == READY or REAOY (tesseract has a hard time distinguishing the two)
def is_ready(text):
    return any((
        "READY" in text,
        "REAOY" in text
        ))

class FrameRecognition:
    crop_widths = [850, 980, 1090, 1100]

    fighter_list = [
            'KAZUYA',
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
            'REINA'
        ]

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

    def read_text(self, frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, regex='[^A-Za-z0-9-]+', time_id=0, opening=False, description=""):
        if xb > 0 or yb > 0:
            frame_cropped = frame_in[ya:yb, xa:xb]
            frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            frame_blackwhite = cv2.threshold(frame_greyscale, threshold, 255, cv2.THRESH_BINARY)[1]
            frame_border = cv2.copyMakeBorder(frame_blackwhite, 30,30,30,30,cv2.BORDER_CONSTANT)
            frame_invert = cv2.bitwise_not(frame_border)
            frame_out = frame_invert
        else:
            frame_out = frame_in

        if opening:
            kernelSize = (5, 5)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernelSize)
            frame_out = cv2.morphologyEx(frame_out, cv2.MORPH_OPEN, kernel)

        psm11 =  pytesseract.image_to_string(frame_out, config="--psm 11")
        psm11_out = re.sub(regex,'',psm11)

        if time_id > 0:
            save_frame(frame_out, time_id, f"{description},{psm11_out}")

        return psm11_out

    def read_fighter(self, frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, regex='[^A-Za-z0-9]+', time_id=0, description=""):
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        lower = np.array([216, 190 , 140])
        upper = np.array([255, 255, 255])
        frame_filtered = cv2.inRange(frame_resized, lower, upper)
        
        frame_inverted = cv2.bitwise_not(frame_filtered)

        frame_out = frame_inverted

        psm11 = pytesseract.image_to_string(frame_out, config='--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXY')
        psm13 = pytesseract.image_to_string(frame_out, config='--psm 13 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJIKLMNOPQRSTUVWXYZ')

        psm11_out = re.sub(regex,'',psm11)
        psm13_out = re.sub(regex,'',psm13)

        if time_id > 0:
            save_frame(frame_out, time_id, f"{description},{psm11_out},{psm13_out}")

        return psm11_out, psm13_out
    
    def read_rank(self, frame_in, xa=0, xb=0, ya=0, yb=0, time_id=0, description=""):
        match_val = [None]*len(self.rank_images)

        frame_cropped = frame_in[530:575, 390:480]
        for idx, rank_img in enumerate(self.rank_images):
            res = cv2.matchTemplate(frame_cropped, rank_img, cv2.TM_SQDIFF)
            match_val[idx] = cv2.minMaxLoc(res)[0]
        index_min = min(range(len(match_val)), key=match_val.__getitem__)
        return self.rank_names[index_min] 

    def rank_rating_range(self,rank_name):
        if rank_name == "Beginner":
            return 0,999
        elif rank_name == "1stDan":
            return 0, 1599
        elif rank_name == "2stDan":
            return 400, 2599
        elif rank_name == "Fighter":
            return 1000, 3399
        elif rank_name == "Strategist":
            return 1600, 4199
        elif rank_name == "Combatant":
            return 2600, 5399
        elif rank_name == "Brawler":
            return 3400, 6399
        elif rank_name == "Ranger":
            return 4200, 7399
        elif rank_name == "Cavalry":
            return 5400, 9199
        elif rank_name == "Warrior":
            return 6400, 10799
        elif rank_name == "Assailant":
            return 7400, 12399
        elif rank_name == "Dominator":
            return 9200, 14699
        elif rank_name == "Vanquisher":
            return 10800, 16599
        elif rank_name == "Destroyer":
            return 12400, 18499
        elif rank_name == "Eliminator":
            return 14700, 23099
        elif rank_name == "Garyu":
            return 16600, 27299
        elif rank_name == "Shinryu":
            return 18500, 31499
        elif rank_name == "Tenryu":
            return 23100, 36499
        elif rank_name == "MightyRuler":
            return 27300, 41099
        elif rank_name == "FlameRuler":
            return 31500, 45699
        elif rank_name == "BattleRuler":
            return 36500, 52299
        elif rank_name == "Fujin":
            return 41100, 58499
        elif rank_name == "Raijin":
            return 45700, 64699
        elif rank_name == "Kishin":
            return 52300, 70899
        elif rank_name == "Bushin":
            return 58500, 79099
        elif rank_name == "TekkenKing":
            return 64700, 86899
        elif rank_name == "TekkenEmperor":
            return 70900, 97299
        elif rank_name == "TekkenGod":
            return 79100, 109699
        elif rank_name == "TekkenGodSupreme":
            return 87900, 200000
        elif rank_name == "GodOfDestruction":
            return 97300, 200000

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

#class to handle youtube video stream and saving match information to log csv
class YoutubeCapture:
    def __init__(self, youtube_url, format_id, playback_start=0, playback_end=0, log_path=r"bin/log.csv", img_path=r"bin/img"):
        #save paths
        self.url = youtube_url
        self.log_path = log_path
        self.img_path = "/bin/"+img_path

        #init variables
        self.cap = None
        self.opponent_name = None
        self.opponent_fighter = None
        self.opponent_rank = None
        self.match_count = 0
        self.match_link = None

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
        self.playback_time = playback_start
        self.cap = cv2.VideoCapture(direct_url)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time))
        
        #get video length
        if playback_end == 0:
            self.video_length = info_dict.get('duration')
        else:
            self.video_length = playback_end
        
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
                    'Player_Fighter',
                    'Player_Rank',
                    'Opponent_Name',
                    'Opponent_Fighter',
                    'Opponent_Rank',
                    'Match_Count',
                    'Match_Outcome',
                    'Postmatch_Rating',
                    'Youtube_Link'
                ])
                
        #create new img/ diretory
        mkdir_img()

    def get_frame(self, type, save_flag):
        ret, frame = self.cap.read()
        if not ret: #figure out better error handling
            print(f"[DEBUG@{self.get_time()}] frame error")

        save_frame(frame, self.playback_time, type, save_flag)
        return frame

    def skip_forward(self,interval):
        self.playback_time+=interval
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time)) # advance by interval

    def get_time(self):
        return round(self.playback_time,2)
    
    def get_url(self):
        return f"https://youtu.be/{self.video_id}?t={int(self.playback_time)}"
    
    def new_lobby(self, player_fighter, player_rank, opponent_name, opponent_fighter, opponent_rank):
        self.player_fighter = player_fighter
        self.player_rank = player_rank
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
        self.player_fighter = None
        self.player_rank = None
        self.opponent_name = None
        self.opponent_fighter = None
        self.opponent_rank = None
        self.match_count = None
        self.match_outcome = None
        self.postmatch_rating = None
        self.match_link = None

    def save_result(self):
        with open(self.log_path, "a") as csvfile:
                log = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                log.writerow([
                    self.upload_date,
                    int(self.playback_time),
                    self.player_fighter,
                    self.player_rank,
                    self.opponent_name,
                    self.opponent_fighter,
                    self.opponent_rank,
                    self.match_count,
                    self.match_outcome,
                    self.postmatch_rating,
                    self.match_link])

class Tekken8RankTracker:
    def __init__(self, vod_url, format='136', start_time=0, end_time=0, frame_log=True):
        #set debug output
        self.log_flag = True
        self.imglog_flag = frame_log

        #vod input
        self.url = vod_url

        #interval parameters
        self.setup_interval = 10
        self.pregame_interval = 2
        self.ingame_interval = 3
        self.postgame_interval = 0.3

        #minimum length parameters
        self.min_pregame_length = 12
        self.min_match_length = 90

        #minimum amount of intervals for tekken to be closed before ending vod
        self.min_no_fps = 150
        self.tekken_end = end_time

        #setup video capture
        self.yt_capture = YoutubeCapture(
            youtube_url=vod_url,
            format_id=format,
            playback_start=start_time,
            playback_end=end_time
        )

    def set_parameters(self,setup_int=10,pregame_int=2,ingame_int=5,postgame_int=0.3,min_pregame=12,min_match=90, min_notekken=300):
        #interval parameters
        self.setup_interval = setup_int
        self.pregame_interval = pregame_int
        self.ingame_interval = ingame_int
        self.postgame_interval = postgame_int

        #minimum length parameters
        self.min_pregame_length = min_pregame
        self.min_match_length = min_match

        #minimum amount of time for tekken to be closed before ending vod
        self.min_no_fps = min_notekken / self.pregame_interval

    def run_fsm(self, initial_state="before"):
        #alphanumeric sort key from https://stackoverflow.com/a/2669120
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]

        #import rank images
        rank_images = [cv2.imread(file) for file in sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)]
        filenames = sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)
        match_val = [None]*len(rank_images)
        rank_names = []
        for filename in filenames:
            name = filename.split("_")[1]
            name = name.split(".")[0]

            rank_names.append(name)
            
        #opponent fighter crop widths for ocr
        crop_widths = [850, 980, 1090, 1100]

        #tekken 8 fighters list
        fighter_list = [
            'KAZUYA',
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
            'REINA'
        ]

        #tekken after counter
        no_fps = 0
        
        #create capture object
        yt = self.yt_capture

        #create ocr objec
        fr = FrameRecognition()

        #set initial state
        state = initial_state

        if self.log_flag == True:
            print(f"\n\n[DEBUG@{yt.get_time()}] State Machine Starting")

        #finite state machine
        while True:
            #check if vod is over
            if yt.playback_time >= yt.video_length:
                #if so, exit fsm
                yt.playback_time == yt.video_length
                print(f"[DEBUG@{yt.get_time()}] VOD finished")
                state == "after"

            if state == "before":
                #capture new frame
                frame = yt.get_frame(state, self.imglog_flag)

                #read text from cropped frame
                trigger = fr.read_text(
                    frame_in=frame, 
                    xa=600, 
                    xb=690, 
                    ya=570, 
                    yb=590, 
                    time_id=yt.get_time(),
                    description="_tRankedMatch"
                )
                #check for trigger
                if "RankedMatch" in trigger:
                    print(f"[EVENT@{yt.get_time()}] Tekken Launched")

                    #change state
                    state = "pre game"
                #if no trigger, increment
                else:
                    #increment video playback time
                    yt.skip_forward(self.setup_interval)
            
            if state == "pre game":
                #capture new frame
                frame = yt.get_frame(state, self.imglog_flag)

                #check if fps counter is present
                fps_temp = fr.read_text(
                    frame_in=frame,
                    xa=0,
                    xb=60,
                    ya=0,
                    yb=25,
                    time_id=yt.get_time(),
                    description='_fps'
                )
                #if fps counter is not present
                if self.tekken_end == 0:
                    if not "fps" in fps_temp:
                        #increment counter
                        no_fps += 1
                        #if no fps counter for 5 minutes, assume that tekken has been closed
                        if no_fps > self.min_no_fps:
                            print(f"[EVENT@{yt.get_time()}] Tekken Closed")

                            state = "after"
                    #reset tracker
                    else:
                        no_fps = 0

                #read text from cropped frame
                trigger = fr.read_text(
                    frame_in=frame, 
                    xa=600, 
                    xb=670, 
                    ya=530, 
                    yb=560, 
                    threshold=190,
                    time_id=yt.get_time(),
                    description="_tSTAGE"
                )
                #check for trigger
                if "STAGE" in trigger:
                    print(f"[EVENT@{yt.get_time()}] Entering Lobby")

                    #check if delayed enter into training
                    kazuya_temp = fr.read_fighter(
                                    frame_in=frame, 
                                    xa=1060, 
                                    xb=1230, 
                                    ya=520, 
                                    yb=570, 
                                    time_id=yt.get_time(),
                                    description="_kazuya"
                    )
                    #if entering training
                    if "KAZUYA" in kazuya_temp:
                        print(f"[EVENT@{yt.get_time()}] Mistaken. Leaving Lobby")

                        #increment video playback time
                        yt.skip_forward(self.pregame_interval)
                    #if entering match
                    else:
                        valid_fighter = False
                        while not valid_fighter:
                            #find opponent fighter
                            for width in crop_widths:
                                fighter_temp = fr.read_fighter(
                                                frame_in=frame, 
                                                xa=width, 
                                                xb=1250, 
                                                ya=450, 
                                                yb=500,
                                                time_id=yt.get_time(),
                                                description="_opponentfighter"
                                )
                                #check if valid fighter
                                for fighter in fighter_list:
                                    for string in fighter_temp:
                                        if fighter in string:
                                            opponent_fighter = fighter
                                            valid_fighter = True

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
                                kazuya_temp = fr.read_text(
                                                frame_in=frame, 
                                                xa=1060, 
                                                xb=1230, 
                                                ya=520, 
                                                yb=570, 
                                                time_id=yt.get_time(),
                                                description="_kazuya"
                                )
                                #if entering training
                                if "KAZUYA" in kazuya_temp:
                                    print(f"[EVENT@{yt.get_time()}] Mistaken. Leaving Lobby")

                                    #increment video playback time
                                    yt.skip_forward(self.pregame_interval)

                                    #exit loop since not entering lobby
                                    break
                                #increment manually since in while loop
                                else:
                                    #read frames until fighter is legible
                                    #advance video playback
                                    yt.skip_forward(0.5)

                                    #capture new frame
                                    frame = yt.get_frame(state, self.imglog_flag)
                        #if opponent fighter was identified
                        if valid_fighter:
                            #find player fighter
                            for width in crop_widths:
                                fighter_temp = fr.read_fighter(
                                                frame_in=frame, 
                                                xa=50, 
                                                xb=450, 
                                                ya=450, 
                                                yb=500,
                                                time_id=yt.get_time(),
                                                description="_playerfighter"
                                )
                                #check if valid fighter
                                for fighter in fighter_list:
                                    for string in fighter_temp:
                                        if fighter in string:
                                            player_fighter = fighter

                                            break
                                    else:
                                        continue
                                    break
                                else:
                                    continue
                                break

                            #find player rank
                            frame_rank_player = frame[530:575, 390:480]
                            for idx, rank_img in enumerate(rank_images):
                                res = cv2.matchTemplate(frame_rank_player, rank_img, cv2.TM_SQDIFF)
                                match_val[idx] = cv2.minMaxLoc(res)[0]
                            index_min = min(range(len(match_val)), key=match_val.__getitem__)
                            player_rank = rank_names[index_min]

                            #find opponent name
                            opponent_name = fr.read_text(
                                            frame_in=frame,
                                            xa=833,
                                            xb=980,
                                            ya=547,
                                            yb=563,
                                            threshold=170,
                                            time_id=yt.get_time(),
                                            description="_opponentname"
                            )
                            
                            #find opponent rank
                            frame_rank_player = frame[530:575, 1140:1230]
                            for idx, rank_img in enumerate(rank_images):
                                res = cv2.matchTemplate(frame_rank_player, rank_img, cv2.TM_SQDIFF)
                                match_val[idx] = cv2.minMaxLoc(res)[0]
                            index_min = min(range(len(match_val)), key=match_val.__getitem__)
                            opponent_rank = rank_names[index_min]

                            #get rating range for ingame->postgame trigger
                            min_rating, max_rating = fr.rank_rating_range(player_rank)

                            yt.new_lobby(player_fighter, player_rank, opponent_name,opponent_fighter,opponent_rank)
                            print(f"[EVENT@{yt.get_time()}] Starting match Player ({player_fighter} - {player_rank}) vs. {opponent_name} ({opponent_fighter} - {opponent_rank})")

                            #advance video playback by minimum match length
                            yt.skip_forward(self.min_match_length)

                            #change state
                            state = "in game"
                #if no trigger, increment
                else:
                    #increment video playback time
                    yt.skip_forward(self.pregame_interval)

            if state == "in game":
                #capture new frame
                frame = yt.get_frame(state, self.imglog_flag)

                #search for number, indicating post game
                trigger = fr.read_text(
                            frame_in=frame,
                            xa=530,
                            xb=630,
                            ya=493,
                            yb=523,
                            opening=True,
                            time_id=yt.get_time(),
                            description="_tRating"
                )
                #check if number (rating) is present
                try:
                    trigger = int(re.sub(r'\D','',trigger))
                #if number is not present, increment
                except ValueError:
                    #increment video playback time
                    yt.skip_forward(self.ingame_interval)
                #if number is present, change state
                else:
                    #only change if valid number (filter out numbers picked up unintentionally)
                    if (min_rating - 1000) <= trigger <= (max_rating + 1000):
                        print(f"[EVENT@{yt.get_time()}] Match concluded")

                    #change state
                    state = "post game"

            if state == "post game":
                #capture new frame
                frame = yt.get_frame(state, self.imglog_flag)

                #search for dots, indicating no rematch possible
                player_dots, opponent_dots, outcome = fr.count_match_dots(frame)
                #if dots are not legible
                if player_dots == -1 or opponent_dots == -1:
                    #skip forward and try to read again
                    yt.skip_forward(1)
                else:
                    #read new rating value
                    rating_temp = fr.read_text(
                                    frame_in=frame,
                                    xa=530,
                                    xb=630,
                                    ya=490,
                                    yb=525,
                                    time_id=yt.get_time(),
                                    description="_rating")
                    #try to read a number from rating_temp
                    try:
                        rating_temp = int(re.sub(r'\D','',rating_temp))
                    #if number is not present
                    except ValueError:
                        #skip forward and try to read again
                        yt.skip_forward(0.1)
                        continue
                    #if number is present, update rating
                    else:
                        #check for adjustment
                        adjustment_temp = fr.read_text(
                                            frame_in=frame,
                                            xa=630,
                                            xb=680,
                                            ya=492,
                                            yb=510,
                                            threshold=100,
                                            time_id=yt.get_time(),
                                            description="_radj")
                        #if negative adjustment
                        if '-' in adjustment_temp:
                            #see if there is a number
                            try:
                                adjustment = int(re.sub(r'\D','',adjustment_temp))
                            #if not, ignore adjustment
                            except ValueError:
                                pass
                            #if there is a number, apply the adjustment
                            else:
                                rating_temp -= adjustment
                        #if positive adustment (or no adjustment)
                        else:
                            #see if there is a number
                            try:
                                adjustment = int(re.sub(r'\D','',adjustment_temp))
                            #if not, ignore adjustment
                            except ValueError:
                                pass
                            #if there is a number, apply the adjustment
                            else:
    
                        #set rating
                                rating_temp += adjustment
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
                        yt.skip_forward(self.min_pregame_length)

                        #change state
                        state = "pre game"
                    #check for rematch or black screen on postgame_interval
                    else:
                        while True:
                            #check for ready signals, indicating a rematch or end lobby
                            player_intent = fr.read_text(
                                            frame_in=frame,
                                            threshold=50,
                                            xa=1220,
                                            xb=1270,
                                            ya=480,
                                            yb=500,
                                            time_id=yt.get_time(),
                                            description="_playerintent")
                            opponent_intent = fr.read_text(
                                                frame_in=frame,
                                                threshold=50,
                                                xa=1210,
                                                xb=1260,
                                                ya=550,
                                                yb=580,
                                                time_id=yt.get_time(),
                                                description="_opponentintent")
                            #check for 'cancel'
                            if "CANCEL" in player_intent or "CANCEL" in opponent_intent:
                                yt.end_lobby()
                                print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                                #advance video playback by minimum pre game length
                                yt.skip_forward(self.min_pregame_length)
                                
                                #change state
                                state = "pre game"

                                break
                            #check for 'ready'
                            if is_ready(player_intent) and is_ready(opponent_intent):
                                yt.rematch()
                                print(f"[EVENT@{yt.get_time()}] Starting rematch against {opponent_name} ({opponent_fighter} - {opponent_rank})")
                                
                                #check for disconnect after accepting rematch
                                yt.skip_forward(self.min_pregame_length)

                                #check for ranked match 5x every 2 seconds
                                for r in range(3):
                                    frame_check = yt.get_frame(state, self.imglog_flag)
                                    check = fr.read_text(
                                        frame_in=frame_check, 
                                        xa=600, 
                                        xb=690, 
                                        ya=570, 
                                        yb=590, 
                                        time_id=yt.get_time(),
                                        description="_cRankedMatch"
                                    )
                                    #check for trigger
                                    if "RankedMatch" in check:
                                        #if ranked match, go to pregame
                                        print(f"[EVENT@{yt.get_time()}] Connection error. Leaving lobby with {opponent_name}")

                                        #change state
                                        state = "pre game"
                                        break
                                    #if no trigger, increment
                                    else:
                                        #increment video playback time
                                        yt.skip_forward(self.pregame_interval)
                                #else go to ingame
                                else:
                                    #advance video playback by minimum match length
                                    yt.skip_forward(self.min_match_length - 3 * self.pregame_interval)
                                    
                                    #change state
                                    state = "in game"

                                #escape infinite while loop
                                break
                            
                            #check for leaving match
                            frame_black_cropped = frame[250:300, 500:800]
                            frame_black_grey = cv2.cvtColor(frame_black_cropped, cv2.COLOR_BGR2GRAY)
                            if cv2.countNonZero(frame_black_grey) == 0:
                                yt.end_lobby()
                                print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                                #advance video playback by minimum pre game length
                                yt.skip_forward(self.min_pregame_length - 6)
                                
                                #change state
                                state = "pre game"

                                break
                            
                            #if neither, increment manually since in while loop
                            #advance video playback
                            yt.skip_forward(0.5)

                            #capture new frame
                            frame = yt.get_frame(state, self.imglog_flag)
            
            if state == "after":
                break

#demo
if __name__ == "__main__":
    #initialize object
    tracker = Tekken8RankTracker(
        #must provide a url to a youtube vod, that has a 720p option (format '136')
        vod_url='https://www.youtube.com/watch?v=NKpNzW7lXk0',
        #when (in seconds) to start scraping (must be at least a couple seconds before starting matchmaking)
        start_time=3600,
        #when (in seconds)to stop scraping (must be after leaving a lobby)
        end_time=15420,
        #set frame_log to False if you do not need to debug
        frame_log=True
    )
    #start scraping
    tracker.run_fsm()