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
def sec_to_ms(ms):
    return ms*1000

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

#preprocess fighter names and read with tesseract
def read_fighter(frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, regex='[^A-Za-z0-9]+', time_id=0, description=""):
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

#preprocess image to be read by tesseract
def read_frame(frame_in, xa=0, xb=0, ya=0, yb=0, threshold=175, regex='[^A-Za-z0-9-]+', time_id=0, description=""):
    if xb > 0 or yb > 0:
        frame_cropped = frame_in[ya:yb, xa:xb]
        frame_resized = cv2.resize(frame_cropped, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        frame_greyscale = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        frame_blackwhite = cv2.threshold(frame_greyscale, threshold, 255, cv2.THRESH_BINARY)[1]
        frame_invert = cv2.bitwise_not(frame_blackwhite)
        frame_out = frame_invert
    else:
        frame_out = frame_in

    psm11 =  pytesseract.image_to_string(frame_out, config="--psm 11")

    psm11_out = re.sub(regex,'',psm11)

    if time_id > 0:
        save_frame(frame_out, time_id, f"{description},{psm11_out}")

    return psm11_out

#template matches 'empty dot' with post-game match result dots
def match_object(frame_in, xa, xb, ya, yb):
    frame = frame_in[ya:yb , xa:xb]
    template = cv2.imread("assets/empty_dot.png", cv2.IMREAD_GRAYSCALE)

    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    
    return res

#uses match_object to determine how many rounds have been won by each player and who won the most recent round
def count_match_dots(frame_in):
    player_res = match_object(frame_in, 1004, 1042, 510, 524)
    player_dots = 0

    opponent_res = match_object(frame_in, 1004, 1042, 534, 548)
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

#returns the minimum and maximum rating for a given rank
def rank_rating_range(rank_name):
    if rank_name == "Beginner":
        return 0,399
    elif rank_name == "1stDan":
        return 300, 999
    elif rank_name == "2stDan":
        return 1000, 1599
    elif rank_name == "Fighter":
        return 1600, 2599
    elif rank_name == "Strategist":
        return 2600, 3399
    elif rank_name == "Combatant":
        return 3400, 4199
    elif rank_name == "Brawler":
        return 4200, 5399
    elif rank_name == "Ranger":
        return 5400, 6399
    elif rank_name == "Cavalry":
        return 6400, 7399
    elif rank_name == "Warrior":
        return 7400, 9199
    elif rank_name == "Assailant":
        return 9200, 10799
    elif rank_name == "Dominator":
        return 10800, 12399
    elif rank_name == "Vanquisher":
        return 12400, 14699
    elif rank_name == "Destroyer":
        return 14700, 16599
    elif rank_name == "Eliminator":
        return 16600, 18499
    elif rank_name == "Garyu":
        return 18500, 23099
    elif rank_name == "Shinryu":
        return 23100, 27299
    elif rank_name == "Tenryu":
        return 27300, 31499
    elif rank_name == "MightyRuler":
        return 31500, 36499
    elif rank_name == "FlameRuler":
        return 36500, 41099
    elif rank_name == "BattleRuler":
        return 41100, 45699
    elif rank_name == "Fujin":
        return 45700, 52299
    elif rank_name == "Raijin":
        return 52300, 58499
    elif rank_name == "Kishin":
        return 58500, 64699
    elif rank_name == "Bushin":
        return 64700, 70899
    elif rank_name == "TekkenKing":
        return 70900, 79099
    elif rank_name == "TekkenEmperor":
        return 79100, 86899
    elif rank_name == "TekkenGod":
        return 87900, 97299
    elif rank_name == "TekkenGodSupreme":
        return 97300, 109699
    elif rank_name == "GodOfDestruction":
        return 109700, 200000

#class to handle youtube video stream and saving match information to log csv
class YoutubeCapture:
    def __init__(self, youtube_url, format_id, log_path=r"bin/log.csv", img_path=r"bin/img"):
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
        self.playback_time = 0
        self.cap = cv2.VideoCapture(direct_url)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time))

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
        mkdir_img()

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
        self.match_link = None

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

    #vod input
    url = "https://www.youtube.com/watch?v=NKpNzW7lXk0"

    #parameters
    setup_interval = 10
    pregame_interval = 2
    ingame_interval = 5
    postgame_interval = 0.3

    #alphanumeric sort key from https://stackoverflow.com/a/2669120
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]

    #import rank images
    rank_images = [cv2.imread(file) for file in sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)]
    filenames = sorted(glob.glob("assets/ranks/*.png"), key=alphanum_key)
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
        name = filename.split("_")[1]
        name = name.split(".")[0]

        rank_names.append(name)

    #game stats
    opponent_name = None
    opponent_rank = None
    opponent_fighter = None
    rating = None
    player_rank = None
    min_rating = None
    max_rating = None
    outcome = None

    #tekken after counter
    no_fps = 0

    #setup video capture
    yt = YoutubeCapture(url, '136')

    # Tekken 8 Rank Tracker - Finite State Machine
    #initial state
    state = "before"

    if save_flag == True:
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
                        description="_tRankedMatch")
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
                        time_id=yt.get_time(),
                        description='_fps')
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
                        description="_tSTAGE")
            #check for trigger
            if "STAGE" in trigger:
                print(f"[EVENT@{yt.get_time()}] Entering Lobby")

                #check if delayed enter into training
                kazuya_temp = read_fighter(
                                frame_in=frame, 
                                xa=1060, 
                                xb=1230, 
                                ya=520, 
                                yb=570, 
                                time_id=yt.get_time(),
                                description="_kazuya")
                #if entering training
                if "KAZUYA" in kazuya_temp:
                    print(f"[EVENT@{yt.get_time()}] Mistaken. Leaving Lobby")

                    #increment video playback time
                    yt.skip_forward(pregame_interval)
                #if entering match
                else:
                    valid_fighter = False
                    while not valid_fighter:
                        #find opponent fighter
                        for width in crop_widths:
                            fighter_temp = read_fighter(
                                            frame_in=frame, 
                                            xa=width, 
                                            xb=1250, 
                                            ya=450, 
                                            yb=500,
                                            time_id=yt.get_time(),
                                            description="_opponentfighter")
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
                                                        description="_opponentname")
                                        
                                        #find opponent rank
                                        frame_rank_player = frame[530:575, 1140:1230]
                                        for idx, rank_img in enumerate(rank_images):
                                            res = cv2.matchTemplate(frame_rank_player, rank_img, cv2.TM_SQDIFF)
                                            match_val[idx] = cv2.minMaxLoc(res)[0]
                                        index_min = min(range(len(match_val)), key=match_val.__getitem__)
                                        opponent_rank = rank_names[index_min]

                                        #find player rank
                                        frame_rank_player = frame[530:575, 390:480]
                                        for idx, rank_img in enumerate(rank_images):
                                            res = cv2.matchTemplate(frame_rank_player, rank_img, cv2.TM_SQDIFF)
                                            match_val[idx] = cv2.minMaxLoc(res)[0]
                                        index_min = min(range(len(match_val)), key=match_val.__getitem__)
                                        player_rank = rank_names[index_min]

                                        min_rating, max_rating = rank_rating_range(player_rank)

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
                                            description="_kazuya")
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
                        description="_tRating")
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
                if (min_rating - 1000) <= trigger <= (max_rating + 1000):
                    print(f"[EVENT@{yt.get_time()}] Match concluded")

                    #change state
                    state = "post game"

        if state == "post game":
            #capture new frame
            frame = yt.get_frame()
            #img log
            save_frame(frame, yt.get_time(), state)

            #search for dots, indicating no rematch possible
            player_dots, opponent_dots, outcome = count_match_dots(frame)
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
                                description="_rating")
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
                    #check for adjustment
                    adjustment_temp = read_frame(
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
                    yt.skip_forward(12)

                    #change state
                    state = "pre game"
                #check for rematch or black screen on postgame_interval
                else:
                    while True:
                        #check for ready signals, indicating a rematch or end lobby
                        player_intent = read_frame(
                                        frame_in=frame,
                                        threshold=50,
                                        xa=1220,
                                        xb=1270,
                                        ya=480,
                                        yb=500,
                                        time_id=yt.get_time(),
                                        description="_playerintent")
                        opponent_intent = read_frame(
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
                            yt.skip_forward(6)
                            
                            #change state
                            state = "pre game"

                            break
                        #check for 'ready'
                        if is_ready(player_intent) and is_ready(opponent_intent):
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