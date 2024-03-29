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
    kernel=np.ones((1,1),np.uint8)

    fighter_list = [
        'KAZUYA',
        'JIN',
        'KING',
        'JUN',
        'PAUL',
        'LAW',
        'JACK', #JACK-8 is hard for tesseract to read
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
        'DEVILJIN', #spaces are removed in tesseract post-processing
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

#class to handle youtube video stream and saving match information to log csv
class YoutubeCapture:
    OUTCOME_WIN = "Win"
    OUTCOME_LOSS = "Loss"
    RATING_UNKNOWN = "Unknown"

    def __init__(self, youtube_url, format_id, playback_start=0, playback_end=0, vod_date=0, log_path=r"bin/log.csv", img_path=r"bin/img"):
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
        if vod_date == 0:
            self.upload_date = info_dict.get('upload_date')
        else:
            self.upload_date = vod_date

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
        return f"https://youtu.be/{self.video_id}?t={int(self.playback_time)}s"
    
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
                    self.get_time(),
                    self.player_fighter,
                    self.player_rank,
                    self.opponent_name,
                    self.opponent_fighter,
                    self.opponent_rank,
                    self.match_count,
                    self.match_outcome,
                    self.postmatch_rating,
                    self.match_link])
        
        self.match_outcome = None
        self.postmatch_rating = None

class Tekken8RankTracker:
    #game states
    STATE_BEFORE = "before"
    STATE_PREGAME = "pregame"
    STATE_INGAME = "ingame"
    STATE_INGAMEUNSURE = "ingamecheck"
    STATE_POSTGAMERESULT = "gameresult"
    STATE_POSTGAMEINTENT = "postgame"
    STATE_AFTER = "after"

    def __init__(self, vod_url, format='136', start_time=0, end_time=0, vod_date=0):
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
        self.tekken_start = start_time
        self.tekken_end = end_time

        #number of rage-quit checks for a rematch
        self.igcheck = 3

        #setup video capture
        self.yt_capture = YoutubeCapture(
            youtube_url=vod_url,
            format_id=format,
            playback_start=start_time,
            playback_end=end_time,
            vod_date=vod_date
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

    def run_fsm(self, initial_state=STATE_BEFORE, frame_log=False):
        #set debug output
        log_flag = True
        imglog_flag = frame_log
        
        #tekken after counter
        no_fps = 0
        
        #create capture object
        yt = self.yt_capture

        #create ocr objec
        fr = FrameRecognition()

        #set initial state
        state = initial_state

        if log_flag == True:
            print(f"\n\n[DEBUG@{yt.get_time()}] State Machine Starting")

        #finite state machine
        while True:
            if state == self.STATE_BEFORE:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length

                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue

                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                #read text from cropped frame
                tRankedMatch = fr.read_text(
                    frame_in=frame, 
                    xa=600, 
                    xb=690, 
                    ya=570, 
                    yb=590, 
                    save_flag=imglog_flag,
                    time_id=yt.get_time(),
                    description="_tRankedMatch"
                )
                #check for trigger
                if "RankedMatch" in tRankedMatch:
                    print(f"[EVENT@{yt.get_time()}] Tekken Launched")

                    #change state
                    state = self.STATE_PREGAME
                #if no trigger, increment
                else:
                    #increment video playback time
                    yt.skip_forward(self.setup_interval)
            
            if state == self.STATE_PREGAME:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length
                    
                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue

                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                if self.tekken_end == 0 and self.tekken_start == 0:
                    #check if fps counter is present
                    fps_temp = fr.read_text(
                        frame_in=frame,
                        xa=0,
                        xb=60,
                        ya=0,
                        yb=25,
                        save_flag=imglog_flag,
                        time_id=yt.get_time(),
                        description='_fps'
                    )
                    #if fps counter is not present
                    if not "fps" in fps_temp:
                        #increment counter
                        no_fps += 1
                        #if no fps counter for 5 minutes, assume that tekken has been closed
                        if no_fps > self.min_no_fps:
                            print(f"[EVENT@{yt.get_time()}] Tekken Closed")

                            state = self.STATE_AFTER
                    #reset tracker
                    else:
                        no_fps = 0

                #read text from cropped frame
                tSTAGE = fr.read_text(
                    frame_in=frame, 
                    xa=600, 
                    xb=670, 
                    ya=530, 
                    yb=560, 
                    threshold=190,
                    save_flag=imglog_flag,
                    time_id=yt.get_time(),
                    description="_tSTAGE"
                )
                #check for trigger
                if "STAGE" in tSTAGE.upper():
                    print(f"[EVENT@{yt.get_time()}] Entering Lobby")

                    #check if delayed enter into training
                    kazuya_temp = fr.read_fighter(
                                    frame_in=frame, 
                                    xa=1060, 
                                    xb=1230, 
                                    ya=520, 
                                    yb=570, 
                                    save_flag=imglog_flag,
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
                            for width in fr.crop_widths:
                                fighter_temp = fr.read_fighter(
                                                frame_in=frame, 
                                                xa=width, 
                                                xb=1250, 
                                                ya=450, 
                                                yb=500,
                                                save_flag=imglog_flag,
                                                time_id=yt.get_time(),
                                                description="_opponentfighter"
                                )
                                #check if valid fighter
                                for fighter in fr.fighter_list:
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
                                                save_flag=imglog_flag,
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
                                    frame = yt.get_frame(state, imglog_flag)
                        #if opponent fighter was identified
                        if valid_fighter:
                            #add non-alphanumerics back to name if applicable
                            if opponent_fighter == "JACK":
                                opponent_fighter = "JACK-8"
                            if opponent_fighter == "DEVILJIN":
                                opponent_fighter = "DEVIL JIN"

                            #find player fighter
                            for width in fr.crop_widths:
                                fighter_temp = fr.read_fighter(
                                                frame_in=frame, 
                                                xa=50, 
                                                xb=450, 
                                                ya=450, 
                                                yb=500,
                                                save_flag=imglog_flag,
                                                time_id=yt.get_time(),
                                                description="_playerfighter"
                                )
                                #check if valid fighter
                                for fighter in fr.fighter_list:
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
                            
                            #add non-alphanumerics back to name if applicable
                            if player_fighter == "JACK":
                                player_fighter = "JACK-8"
                            if player_fighter == "DEVILJIN":
                                player_fighter = "DEVIL JIN"

                            #find player rank
                            player_rank = fr.read_rank(
                                frame_in=frame,
                                xa=390,
                                xb=480,
                                ya=530,
                                yb=575,
                                save_flag=imglog_flag,
                                time_id=yt.get_time(),
                                description="_playerrank"
                            )

                            #find opponent name
                            opponent_name = fr.read_text(
                                            frame_in=frame,
                                            xa=833,
                                            xb=980,
                                            ya=547,
                                            yb=563,
                                            threshold=170,
                                            save_flag=imglog_flag,
                                            time_id=yt.get_time(),
                                            description="_opponentname"
                            )
                            
                            #find opponent rank
                            opponent_rank = fr.read_rank(
                                frame_in=frame,
                                xa=1140,
                                xb=1230,
                                ya=530,
                                yb=575,
                                save_flag=imglog_flag,
                                time_id=yt.get_time(),
                                description="_opprank"
                            )

                            yt.new_lobby(player_fighter, player_rank, opponent_name,opponent_fighter,opponent_rank)
                            print(f"[EVENT@{yt.get_time()}] Starting match Player ({player_fighter} - {player_rank}) vs. {opponent_name} ({opponent_fighter} - {opponent_rank})")

                            #advance video playback by minimum match length
                            yt.skip_forward(self.min_match_length)

                            #change state
                            state = self.STATE_INGAME
                #if no trigger, increment
                else:
                    #increment video playback time
                    yt.skip_forward(self.pregame_interval)

            if state == self.STATE_INGAME:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length

                    #assume player lost
                    outcome = yt.OUTCOME_LOSS
                    rating = yt.RATING_UNKNOWN

                    #save incomplete match
                    print(f"[EVENT@{yt.get_time()}] Match Result: {outcome} - Rating: {rating}")
                    yt.match_result(outcome,rating)
                    yt.save_result()

                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue

                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                #search for trigger
                tYou = fr.read_text(
                        frame_in=frame,
                        xa=521,
                        ya=528,
                        xb=540,
                        yb=540,
                        invert=False,
                        save_flag=imglog_flag,
                        time_id=yt.get_time(),
                        description="_tYOU"
                )
                #if found, change state
                if "You" in tYou:
                    print(f"[EVENT@{yt.get_time()}] Match concluded")

                    state = self.STATE_POSTGAMERESULT
                #else increment
                else:
                    yt.skip_forward(self.ingame_interval)

            if state == self.STATE_POSTGAMERESULT:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length

                    #save incomplete data
                    yt.save_result()

                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue
                
                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                #search for dots, indicating no rematch possible
                player_dots, opponent_dots, outcome = fr.count_match_dots(frame)
                #if dots are not legible
                if player_dots == -1 or opponent_dots == -1 or outcome == None:
                    #skip forward and try to read again
                    yt.skip_forward(1)
                else:
                    #read new rating value
                    rating_temp = fr.read_text(
                                    frame_in=frame,
                                    xa=530,
                                    xb=630,
                                    ya=496,
                                    yb=522,
                                    noisy=True,
                                    save_flag=imglog_flag,
                                    time_id=yt.get_time(),
                                    description="_rating"
                    )
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
                                            save_flag=imglog_flag,
                                            time_id=yt.get_time(),
                                            description="_radj"
                        )
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
                            outcome = yt.OUTCOME_WIN
                        else:
                            outcome = yt.OUTCOME_LOSS

                        yt.end_lobby()
                        print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                        #clear opponent variables

                        opponent_fighter = None
                        opponent_name = None
                        opponent_rank = None

                        #advance video playback by minimum pre-game length
                        yt.skip_forward(self.min_pregame_length)

                        #change state
                        state = self.STATE_PREGAME
                    #if intent unknown, change state
                    else:
                        state = self.STATE_POSTGAMEINTENT        
            
            if state == self.STATE_POSTGAMEINTENT:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length

                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue
                
                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                #check for ready signals, indicating a rematch or end lobby
                player_intent = fr.read_text(
                                frame_in=frame,
                                threshold=50,
                                xa=1220,
                                xb=1270,
                                ya=480,
                                yb=500,
                                save_flag=imglog_flag,
                                time_id=yt.get_time(),
                                description="_playerintent"
                )
                opponent_intent = fr.read_text(
                                    frame_in=frame,
                                    threshold=50,
                                    xa=1210,
                                    xb=1260,
                                    ya=550,
                                    yb=580,
                                    save_flag=imglog_flag,
                                    time_id=yt.get_time(),
                                    description="_opponentintent"
                )
                #check for 'cancel'
                if "CANCEL" in player_intent or "CANCEL" in opponent_intent:
                    yt.end_lobby()
                    print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                    #advance video playback by minimum pre game length
                    yt.skip_forward(self.min_pregame_length)
                    
                    #change state
                    state = self.STATE_PREGAME
                    continue
                #check for 'ready'
                if is_ready(player_intent) and is_ready(opponent_intent):
                    yt.rematch()
                    print(f"[EVENT@{yt.get_time()}] Starting rematch against {opponent_name} ({opponent_fighter} - {opponent_rank})")
                    
                    #advance video playback by minimum pre game length
                    yt.skip_forward(self.min_pregame_length)

                    #change state
                    state = self.STATE_INGAMEUNSURE
                
                #check for leaving match
                frame_black_cropped = frame[250:300, 500:800]
                frame_black_grey = cv2.cvtColor(frame_black_cropped, cv2.COLOR_BGR2GRAY)
                if cv2.countNonZero(frame_black_grey) == 0:
                    yt.end_lobby()
                    print(f"[EVENT@{yt.get_time()}] Leaving lobby with {opponent_name}")

                    #advance video playback by minimum pre game length
                    yt.skip_forward(self.min_pregame_length - 6)
                    
                    #change state
                    state = self.STATE_PREGAME
                    continue
                
                #if neither, increment manually since in while loop
                #advance video playback
                yt.skip_forward(0.5)

                #capture new frame
                frame = yt.get_frame(state, imglog_flag)
            
            if state == self.STATE_AFTER:
                #break out of fsm loop
                break

            if state == self.STATE_INGAMEUNSURE:
                #check if vod is over
                if yt.playback_time >= yt.video_length:
                    yt.playback_time == yt.video_length

                    #change state
                    print(f"[DEBUG@{yt.get_time()}] VOD finished")
                    state = self.STATE_AFTER
                    continue
                
                #capture new frame
                frame = yt.get_frame(state, imglog_flag)

                #check for ranked match (indicating left lobby) in case of rage quit
                for r in range(self.igcheck):
                    frame_check = yt.get_frame(state, imglog_flag)
                    check = fr.read_text(
                        frame_in=frame_check, 
                        xa=600, 
                        xb=690, 
                        ya=570, 
                        yb=590, 
                        save_flag=imglog_flag,
                        time_id=yt.get_time(),
                        description="_cRankedMatch"
                    )
                    #check for trigger
                    if "RankedMatch" in check:
                        #if ranked match, go to pregame
                        print(f"[EVENT@{yt.get_time()}] Connection error. Leaving lobby with {opponent_name}")

                        #change state
                        state = self.STATE_PREGAME
                        break
                    #if no trigger, increment
                    else:
                        #increment video playback time
                        yt.skip_forward(self.pregame_interval)
                #else go to ingame
                else:
                    #advance video playback by minimum match length
                    yt.skip_forward(self.min_match_length - self.igcheck * self.pregame_interval)
                    
                    #change state
                    state = self.STATE_INGAME
            
        print(f"[DEBUG@{yt.get_time()}] Exiting State Machine")


#demo
if __name__ == "__main__":
    #initialize object
    tracker = Tekken8RankTracker(
        #must provide a url to a youtube vod, that has a 720p option (format '136')
        vod_url='https://www.youtube.com/watch?v=NKpNzW7lXk0',
        #optional: when (in seconds) to start recording (must be at least a couple seconds before starting matchmaking)
        start_time=3600,
        #optional: when (in seconds)to stop recording (must be after leaving a lobby)
        end_time=15420,
        #optional: set frame_log to False if you do not need to debug
        frame_log=True
    )
    #start scraping
    tracker.run_fsm()