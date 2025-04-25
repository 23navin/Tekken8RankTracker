# getting yt frames and image processing
import yt_dlp as youtube_dl

# data logging
from pathlib import Path
import csv

import cv2

# file management
import os
import shutil
import errno

from src.T8RankTracker.constants import asciiColor as color
from src.T8RankTracker.helpers import save_frame

#convert seconds to milli-seconds
def sec_to_ms(sec):
    return sec*1000

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

#class to handle youtube video stream and saving match information to log csv
class YoutubeCapture:
    OUTCOME_WIN = "Win"
    OUTCOME_LOSS = "Loss"
    RATING_UNKNOWN = "Unknown"

    def __init__(self, youtube_url, format_id, playback_start=0, playback_end=None, vod_date=None, log_path=r"bin/log.csv", img_path=r"bin/img"):
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
        self.playback_time = playback_start

        #extract metadata with youtube-dl
        self.log_DEBUG("Loading Youtube video")
        ydl_opts={
            "cookiefile": "bin/cookies.txt",
        }
        
        ydl=youtube_dl.YoutubeDL(ydl_opts)
        info_dict=ydl.extract_info(self.url, download=False)
        
        #get url for format
        formats = info_dict.get('formats',None)
        for f in formats:
            if f.get('resolution') == '1280x720' and f.get('video_ext') == 'mp4':
                direct_url = f.get('url')
                break
        else:
            self.log_DEBUG("Format not found")
            return

        #create cv2 object using url
        self.cap = cv2.VideoCapture(direct_url)
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time))
        
        #get video length
        if playback_end == None:
            self.video_length = info_dict.get('duration')
        else:
            self.video_length = playback_end
        
        #get video display_id for url reconstruction
        self.video_id = info_dict.get('display_id')

        #get video upload date
        if vod_date == None:
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

    def log_EVENT(self, message="", italic=False ,note=""):
        out = f"{color.bg.CYAN}{color.fg.WHITE}EVENT@{self.get_time()}{color.reset} "
        if message:
            if italic:
                out += f"{color.style.italic}{color.fg.WHITE}{message}{color.reset}"
            else:
                out += f"{color.style.bold}{color.fg.WHITE}{message}{color.reset}"

        if note:
            out += f" {note}"

        print(out)

    def log_DEBUG(self, message):
        print(f"{color.bg.BLUE}{color.fg.WHITE}DEBUG@{self.get_time()}{color.reset} {message}")
    
    def get_frame(self, type, save_flag):
        ret, frame = self.cap.read()
        if not ret: #figure out better error handling
            self.log_DEBUG("frame error")

        save_frame(frame, self.get_time(), type, save_flag)
        return frame

    def skip_forward(self,interval):
        self.playback_time+=interval
        self.cap.set(cv2.CAP_PROP_POS_MSEC, sec_to_ms(self.playback_time)) # advance by interval

    def get_time(self):
        time = round(self.playback_time,3)
        return time
    
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