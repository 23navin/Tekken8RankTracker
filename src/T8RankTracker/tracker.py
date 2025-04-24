from cv2 import imencode
from re import sub

from .constants import fighter_list
from .constants import asciiColor as color

from .recognition import FrameRecognition, is_match, is_ready, is_TEKKENPROWESS

from .capture import YoutubeCapture

class Tekken8RankTracker:
    #API
    class api:
        def __init__(self, initial_state, start_time):
            self.package = {
                'playback_time': start_time,
                'game_state': initial_state,
                'frame': None
            }

        def update(self, playback_time, game_state, frame):
            self.package = {
                'playback_time': playback_time,
                'game_state': game_state,
                'frame': frame
            }

        def is_fsm_active(self) -> 'bool':
            if self.package['game_state'] != Tekken8RankTracker.STATE_AFTER:
                return True
            return False
        
        def get_time(self):
            return self.package['playback_time']
        
        def get_state(self):
            return self.package['game_state']

        def get_preview(self):
            buffer = imencode('.jpg', self.package['frame'])[1].tostring()
            return buffer

    #game states
    STATE_BEFORE = "beforeState"
    STATE_PREGAME = "pregameState"
    STATE_LOBBY = "lobbyState"
    EXIT_LOBBY = "lobbyExit"
    ENTRY_INGAME = "ingameEntryState"
    STATE_INGAME = "ingameState"
    STATE_INGAMEUNSURE = "rematchcheckState"
    STATE_PREGAMEWAIT = "ingamecheckState"
    STATE_POSTGAMERESULT = "gameresultState"
    ENTRY_POSTGAMEINTENT = "postgameEntry"
    STATE_POSTGAMEINTENT = "postgameState"
    STATE_AFTER = "afterState"

    #states that do not need a new frame
    ignore_frame_states = [
        STATE_LOBBY,
        EXIT_LOBBY,
        ENTRY_INGAME,
        ENTRY_POSTGAMEINTENT,
        STATE_AFTER
    ]

    def __init__(self, vod_url: str, format:str='136', start_time:int=0, end_time:int=None, vod_date:int=None, frame_log:bool=False, initial_state=STATE_BEFORE):
        #vod input
        self.url = vod_url

        #set playback parameters
        self.set_parameters()
        self.tekken_start = start_time
        self.tekken_end = end_time

        #number of rage-quit checks for a rematch
        self.igcheck = 3

        #setup video capture
        self.yt = YoutubeCapture(
            youtube_url=vod_url,
            format_id=format,
            playback_start=self.tekken_start,
            playback_end=end_time,
            vod_date=vod_date
        )
        
        #setup frame recognition
        self.fr = FrameRecognition()

        #setup api
        self.info = self.api(initial_state, self.tekken_start)

        #setup log flags
        self.log_flag = True
        self.imglog_flag = frame_log

        #setup fsm variables that have initial states
        self.no_fps = 0
        self.state = initial_state
        self.frame = None
        self.get_frame_flag = False

    def set_parameters(
            self,setup_int=10,
            pregame_int=2,
            ingame_int=12,
            postgame_outcome_int=1,
            postgame_intent_int=5,
            min_pregame=12,
            min_match=75,
            min_notekken=300
            ):
        #interval parameters
        self.setup_interval = setup_int
        self.pregame_interval = pregame_int
        self.ingame_interval = ingame_int
        self.postgame_outcome_interval = postgame_outcome_int
        self.postgame_intent_interval = postgame_intent_int

        #minimum length parameters
        self.min_pregame_length = min_pregame
        self.min_match_length = min_match

        #minimum amount of time for tekken to be closed before ending vod
        self.min_no_fps = min_notekken / self.pregame_interval

    def run_fsm(self):
        #check if a new frame is not required
        if self.state not in self.ignore_frame_states:
            #capture new frame
            self.frame = self.yt.get_frame(self.state, self.imglog_flag)

        #update API
        self.info.update(
            playback_time = self.yt.get_time(),
            game_state = self.state,
            frame = self.frame
            )

        #---FSM---
        if self.state == self.STATE_BEFORE:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                self.yt.log_EVENT("VOD Finished", True)

                #change state
                self.state = self.STATE_AFTER
                return

            #read text from cropped frame
            tRankedMatch = self.fr.read_text(
                frame_in=self.frame, 
                xa=600, 
                xb=690, 
                ya=570, 
                yb=590, 
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tRankedMatch"
            )
            #check for trigger
            if "RankedMatch" in tRankedMatch:
                self.yt.log_EVENT(
                    message="Tekken Launched.",
                    note="Entering matchmaking"
                )

                #change state
                self.state = self.STATE_PREGAME
            #if no trigger, increment
            else:
                #increment video playback time
                self.yt.skip_forward(self.setup_interval)

            #exit iteration
            return
        
        if self.state == self.STATE_PREGAME:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length
                
                self.yt.log_EVENT("VOD Finished", True)

                #change state
                self.state = self.STATE_AFTER
                return

            if self.tekken_end == 0 and self.tekken_start == 0:
                #check if fps counter is present
                fps_temp = self.fr.read_text(
                    frame_in=self.frame,
                    xa=0,
                    xb=60,
                    ya=0,
                    yb=25,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description='_fps'
                )
                #if fps counter is not present
                if not "fps" in fps_temp:
                    #increment counter
                    self.no_fps += 1
                    #if no fps counter for 5 minutes, assume that tekken has been closed
                    if self.no_fps > self.min_no_fps:
                        self.yt.log_EVENT("Tekken Closed")

                        self.state = self.STATE_AFTER
                #reset tracker
                else:
                    self.no_fps = 0

            #read text from cropped frame
            tSTAGE = self.fr.read_text(
                frame_in=self.frame, 
                xa=600, 
                xb=670, 
                ya=530, 
                yb=560, 
                threshold=190,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tSTAGE"
            )
            #check for trigger
            if is_match(tSTAGE, "STAGE"):
                #check if delayed enter into training
                tKAZUYA = self.fr.read_fighter(
                    frame_in=self.frame, 
                    xa=1060, 
                    xb=1230, 
                    ya=520, 
                    yb=570, 
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_tKAZUYA"
                )
                #if entering training
                if "KAZUYA" in tKAZUYA:

                    #increment video playback time
                    self.yt.skip_forward(self.pregame_interval)
                #if entering match
                else:
                    #change state
                    self.yt.log_EVENT("Entering Lobby")
                    self.state = self.STATE_LOBBY
            #if no trigger, increment
            else:
                #increment video playback time
                self.yt.skip_forward(self.pregame_interval)

            #exit iteration
            return
        
        if self.state == self.STATE_LOBBY:
            tSTAGE = self.fr.read_text(
                frame_in=self.frame, 
                xa=600, 
                xb=670, 
                ya=530, 
                yb=560, 
                threshold=190,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tSTAGE"
            )
            if not "STAGE" in tSTAGE.upper():
                opponent_fighter = None

                #change state
                self.state = self.EXIT_LOBBY
                return

            #find opponent fighter
            for width in self.fr.crop_widths:
                fighter_temp = self.fr.read_fighter(
                    frame_in=self.frame, 
                    xa=width, 
                    xb=1250, 
                    ya=450, 
                    yb=500,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_opponentfighter"
                )
                #check if valid fighter
                for fighter in fighter_list:
                    for string in fighter_temp:
                        if fighter in string:
                            self.opponent_fighter = fighter

                            #change state
                            self.state = self.EXIT_LOBBY

                            #exit iteration
                            return
                    else:
                        self.opponent_fighter = None
                        continue
                    break
                else:
                    continue
                break
            
            #check if delayed enter into training ('kazuya' text can be missed by ocr during an animation)
            tKAZUYA = self.fr.read_text(
                frame_in=self.frame, 
                xa=1060, 
                xb=1230, 
                ya=520, 
                yb=570, 
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_kazuya"
            )
            #if entering training
            if "KAZUYA" in tKAZUYA:
                self.yt.log_EVENT(
                    message="Leaving Lobby.",
                    note="Entering matchmaking"
                )

                #increment video playback time
                self.yt.skip_forward(self.pregame_interval)

                #change state
                self.state = self.STATE_PREGAME

            #read frames until fighter is legible
            else:
                #advance video playback
                self.yt.skip_forward(0.5)

                #capture new frame
                self.frame = self.yt.get_frame(self.state, self.imglog_flag)

            #exit iteration
            return
        
        if self.state == self.EXIT_LOBBY:
            opponent_fighter = self.opponent_fighter
            #add non-alphanumerics back to name if applicable
            if opponent_fighter == "JACK":
                opponent_fighter = "JACK-8"
            if opponent_fighter == "DEVILJIN":
                opponent_fighter = "DEVIL JIN"

            #find player fighter
            for width in self.fr.crop_widths:
                fighter_temp = self.fr.read_fighter(
                    frame_in=self.frame, 
                    xa=50, 
                    xb=450, 
                    ya=450, 
                    yb=500,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_playerfighter"
                )
                #check if valid fighter
                for fighter in fighter_list:
                    for string in fighter_temp:
                        if fighter in string:
                            player_fighter = fighter

                            break
                    else:
                        player_fighter = None
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
            player_rank = self.fr.read_rank(
                frame_in=self.frame,
                xa=390,
                xb=480,
                ya=530,
                yb=575,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_playerrank"
            )

            #find opponent name
            opponent_name = self.fr.read_text(
                frame_in=self.frame,
                xa=833,
                xb=980,
                ya=547,
                yb=563,
                threshold=170,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_opponentname"
            )
            
            #find opponent rank
            opponent_rank = self.fr.read_rank(
                frame_in=self.frame,
                xa=1140,
                xb=1230,
                ya=530,
                yb=575,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_opprank"
            )

            self.yt.new_lobby(player_fighter, player_rank, opponent_name, opponent_fighter, opponent_rank)
            self.yt.log_EVENT(
                message="Starting Match:",
                note=f"Player ({player_fighter} - {player_rank}) vs. {opponent_name} ({opponent_fighter} - {opponent_rank})"
            )

            #advance video playback by minimum pre game length
            self.yt.skip_forward(self.min_pregame_length)

            #change state
            self.state = self.STATE_PREGAMEWAIT

            #exit iteration
            return

        if self.state == self.ENTRY_INGAME:
            #prepare variables
            self.dynamic_interval = self.ingame_interval
            self.escape_interval = None
            self.escape_flag = None

            #change state
            self.state = self.STATE_INGAME

            #exit iteration
            return

        if self.state == self.STATE_INGAME:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                #assume player lost
                outcome = self.yt.OUTCOME_LOSS
                rating = self.yt.RATING_UNKNOWN

                if outcome == "Win":
                    outcome_log = f"{color.fg.GREEN}{outcome}{color.reset}"
                elif outcome == "Loss":
                    outcome_log = f"{color.fg.RED}{outcome}{color.reset}"
                else:
                    outcome_log = outcome
                self.yt.log_EVENT(
                    message="Match Result:",
                    note=f"{outcome_log} - Rating: {color.style.underline}{rating}{color.reset}"
                )

                #save incomplete match
                self.yt.match_result(outcome,rating)
                self.yt.save_result()

                #change state
                self.yt.log_EVENT("VOD Finished", True)
                self.state = self.STATE_AFTER
                return

            tOK = self.fr.read_text(
                frame_in=self.frame, 
                xa=625, 
                xb=652, 
                ya=398, 
                yb=430, 
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tOK"
            )
            #if new rank dialog
            if "OK" in tOK.upper():
                self.yt.log_EVENT("Match concluded")
                self.state = self.STATE_POSTGAMERESULT
                return
                
            #check if in replay
            tReplayHUD = self.fr.read_text(
                frame_in=self.frame,
                xa=286,
                ya=680,
                xb=905,
                yb=702,
                threshold=120,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tReplayHUD"
            ).lower()
            if any((
                "previous" in tReplayHUD,
                "next" in tReplayHUD,
                "round" in tReplayHUD,
                "menu" in tReplayHUD
            )):
                self.yt.log_EVENT(
                    message="Leaving Lobby.",
                    note="Player is watching a replay"
                )
                self.yt.end_lobby()

                #increment playback time
                self.yt.skip_forward(self.min_pregame_length)

                #change state
                self.state = self.STATE_BEFORE

            #check if still in ingame window
            tpTEKKENPROWESS = self.fr.read_text(
                frame_in=self.frame,
                xa=125,
                ya=28,
                xb=224,
                yb=47,
                invert=True,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tpTEKKENPROWESS"
            )
            toTEKKENPROWESS = self.fr.read_text(
                frame_in=self.frame,
                xa=1004,
                ya=28,
                xb=1102,
                yb=47,
                invert=True,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_toTEKKENPROWESS"
            )
            if is_TEKKENPROWESS(tpTEKKENPROWESS) or is_TEKKENPROWESS(toTEKKENPROWESS):
                tRankedMatch = self.fr.read_text(
                    frame_in=self.frame, 
                    xa=600, 
                    xb=690, 
                    ya=570, 
                    yb=590, 
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_tRankedMatch"
                )
                #check if in training
                if "RankedMatch" in tRankedMatch:
                    #rewind playback to last interval
                    self.yt.skip_forward(-(self.dynamic_interval-1))
                    
                    self.escape_flag = True
                    
                    #adjust dynamic interval
                    self.dynamic_interval /= 2
                    #prevent dynamic interval from getting too small and getting stuck
                    if self.dynamic_interval < 1:
                        self.dynamic_interval = 1
                else:
                    #first forward after backwards
                    if self.escape_flag:
                        self.escape_flag = False
                    #second consecutive forward
                    elif self.escape_flag == False:
                        #reset escape
                        self.escape_flag = None
                        self.escape_interval = None

                    #move playback forward
                    self.yt.skip_forward(self.dynamic_interval)
            else:
                #look for postgame trigger
                tYou = self.fr.read_text(
                    frame_in=self.frame,
                    xa=521,
                    ya=528,
                    xb=540,
                    yb=540,
                    invert=False,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_tYOU"
                )
                #if found, change state
                if "You" in tYou:
                    self.yt.log_EVENT("Match concluded")
                    self.state = self.STATE_POSTGAMERESULT
                    #go back a postgame interval to ensure that there is a match on next interval
                    self.yt.skip_forward(-self.postgame_outcome_interval)
                else:
                    if self.escape_interval:
                        if self.yt.playback_time == self.escape_interval:
                            #leave match, record loss
                            outcome = self.yt.OUTCOME_LOSS
                            rating = self.yt.RATING_UNKNOWN

                            if outcome == "Win":
                                outcome_log = f"{color.fg.GREEN}{outcome}{color.reset}"
                            elif outcome == "Loss":
                                outcome_log = f"{color.fg.RED}{outcome}{color.reset}"
                            else:
                                outcome_log = outcome
                            self.yt.log_EVENT(
                                message="Match Result:",
                                note=f"{outcome_log} - Rating: {color.style.underline}{rating}{color.reset}"
                            )

                            #save incomplete match
                            self.yt.match_result(outcome,rating)
                            self.yt.save_result()

                            self.state = self.STATE_PREGAME
                        else:
                            self.escape_flag = True
                            
                            #rewind playback to last interval
                            self.yt.skip_forward(-(self.dynamic_interval-1))
                    #if escape has not been set
                    else:
                        self.escape_flag = True
                        self.escape_interval = self.yt.playback_time

                        #rewind playback to last interval
                        self.yt.skip_forward(-(self.dynamic_interval-1))

            #exit iteration
            return
        
        if self.state == self.STATE_POSTGAMERESULT:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                #save incomplete data
                self.yt.save_result()

                #change state
                self.yt.log_EVENT("VOD finished", True)
                self.state = self.STATE_AFTER
                return

            tKAZUYA = self.fr.read_fighter(
                frame_in=self.frame, 
                xa=1060, 
                xb=1230, 
                ya=520, 
                yb=570, 
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tKAZUYA"
            )
            #if entering training
            if "KAZUYA" in tKAZUYA:
                self.yt.log_EVENT(
                    message="Leaving Lobby.",
                    note="Match ended without an outcome"
                )
                self.yt.end_lobby()

                #indicates opponent disconnected, save incomplete match
                self.yt.match_result(None, self.yt.RATING_UNKNOWN)
                self.yt.save_result()

                #change state
                self.state = self.STATE_PREGAME
                return
            
            #search for dots, indicating no rematch possible
            player_dots, opponent_dots, outcome = self.fr.count_match_dots(self.frame)
            #if dots are not legible
            if player_dots == -1 or opponent_dots == -1 or outcome == None:
                #skip forward and try to read again
                self.yt.skip_forward(self.postgame_outcome_interval)
            else:
                #read new rating value
                rating_temp = self.fr.read_text(
                    frame_in=self.frame,
                    xa=530,
                    xb=630,
                    ya=496,
                    yb=522,
                    noisy=True,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_rating"
                )
                #try to read a number from rating_temp
                try:
                    rating_temp = int(sub(r'\D','',rating_temp))
                #if number is not present
                except ValueError:
                    #skip forward and try to read again
                    self.yt.skip_forward(0.1)
                    return
                #if number is present, update rating
                else:
                    #check for adjustment
                    adjustment_temp = self.fr.read_text(
                        frame_in=self.frame,
                        xa=630,
                        xb=680,
                        ya=492,
                        yb=510,
                        threshold=40,
                        save_flag=self.imglog_flag,
                        time_id=self.yt.get_time(),
                        description="_radj"
                    )
                    #if negative adjustment
                    if '-' in adjustment_temp:
                        #see if there is a number
                        try:
                            adjustment = int(sub(r'\D','',adjustment_temp))
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
                            adjustment = int(sub(r'\D','',adjustment_temp))
                        #if not, ignore adjustment
                        except ValueError:
                            pass
                        #if there is a number, apply the adjustment
                        else:
                            #set rating
                            rating_temp += adjustment
                    rating = rating_temp

                    if outcome == "Win":
                        outcome_log = f"{color.fg.GREEN}{outcome}{color.reset}"
                    elif outcome == "Loss":
                        outcome_log = f"{color.fg.RED}{outcome}{color.reset}"
                    else:
                        outcome_log = outcome
                    self.yt.log_EVENT(
                        message="Match Result:",
                        note=f"{outcome_log} - Rating: {color.style.underline}{rating}{color.reset}"
                    )

                    self.yt.match_result(outcome, rating)
                    self.yt.save_result()
                
                #check if final match
                if player_dots == 2 or opponent_dots == 2:
                    #set outcome
                    if player_dots == 2:
                        outcome = self.yt.OUTCOME_WIN
                    else:
                        outcome = self.yt.OUTCOME_LOSS

                    self.yt.log_EVENT(
                        message="Leaving lobby",
                        note=f"with {self.yt.opponent_name}"
                    )
                    self.yt.end_lobby()

                    #advance video playback by minimum pre-game length
                    self.yt.skip_forward(self.min_pregame_length)

                    #change state
                    self.state = self.STATE_PREGAME
                #if intent unknown, change state
                else:
                    self.state = self.ENTRY_POSTGAMEINTENT

        if self.state == self.ENTRY_POSTGAMEINTENT:
            self.dynamic_interval = self.postgame_intent_interval
            self.playback = self.yt.get_time()
                
            self.state = self.STATE_POSTGAMEINTENT
        
            #exit iteration
            return
        
        if self.state == self.STATE_POSTGAMEINTENT:
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                #save incomplete data
                self.yt.save_result()

                #change state
                self.yt.log_EVENT("VOD finished", True)
                self.state = self.STATE_AFTER
                return
            
            #in case playback goes back into the game
            if self.yt.get_time() < self.playback:
                #advance playback past whatever noise caused it to happen
                self.yt.skip_forward(10)

            #check if still in postgame window
            player_dots, opponent_dots, outcome = self.fr.count_match_dots(self.frame)
            #if dots are not legible
            if player_dots == -1 or opponent_dots == -1:
                #rewind playback by dynamic interval
                self.yt.skip_forward(-(self.dynamic_interval-0.1))

                #adjust dynamic interval
                self.dynamic_interval /= 2
                #prevent dynamic interval from getting too small and getting stuck
                if self.dynamic_interval < 0.05:
                    self.yt.log_EVENT(
                        message="Leaving lobby",
                        note=f"with {self.yt.opponent_name}")
                    self.yt.end_lobby()

                    #advance video playback by minimum pre game length
                    self.yt.skip_forward(self.min_pregame_length)
                    
                    #change state
                    self.state = self.STATE_PREGAME
                    return

            #if postgame_outcome missed forced leave match
            elif player_dots == 2 or opponent_dots == 2:
                #set outcome
                if player_dots == 2:
                    outcome = self.yt.OUTCOME_WIN
                else:
                    outcome = self.yt.OUTCOME_LOSS

                self.yt.log_EVENT(
                    message="Leaving lobby",
                    note=f"with {self.yt.opponent_name}"
                )

                self.yt.end_lobby()

                #advance video playback by minimum pre-game length
                self.yt.skip_forward(self.min_pregame_length)

                #change state
                self.state = self.STATE_PREGAME
            else:
                #check for ready signals, indicating a rematch or end lobby
                player_intent = self.fr.read_text(
                    frame_in=self.frame,
                    threshold=50,
                    xa=1220,
                    xb=1270,
                    ya=480,
                    yb=500,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_playerintent"
                )
                opponent_intent = self.fr.read_text(
                    frame_in=self.frame,
                    threshold=50,
                    xa=1210,
                    xb=1260,
                    ya=550,
                    yb=580,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_opponentintent"
                )
                player_intent_inv = self.fr.read_text(
                    frame_in=self.frame,
                    threshold=50,
                    xa=1220,
                    xb=1270,
                    ya=480,
                    yb=500,
                    invert=False,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_playerintentinv"
                )
                opponent_intent_inv = self.fr.read_text(
                    frame_in=self.frame,
                    threshold=50,
                    xa=1210,
                    xb=1260,
                    ya=550,
                    yb=580,
                    invert=False,
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_opponentintentinv"
                )

                #check for 'cancel'
                if any((
                    "CANCEL" in player_intent.upper(),
                    "CANCEL" in player_intent_inv.upper(),
                    "CANCEL" in opponent_intent.upper(),
                    "CANCEL" in opponent_intent_inv.upper()
                )):
                    self.yt.log_EVENT(
                        message="Leaving lobby",
                        note=f"with {self.yt.opponent_name}")
                    self.yt.end_lobby()

                    #advance video playback by minimum pre game length
                    self.yt.skip_forward(self.min_pregame_length)
                    
                    #change state
                    self.state = self.STATE_PREGAME
                    return
                #check for 'ready'
                elif (is_ready(player_intent) or is_ready(player_intent_inv)) and (is_ready(opponent_intent) or is_ready(opponent_intent_inv)):
                    self.yt.rematch()
                    self.yt.log_EVENT(message="Starting rematch")
                    
                    #advance video playback by minimum pre game length
                    self.yt.skip_forward(self.min_pregame_length)

                    #change state
                    self.state = self.STATE_INGAMEUNSURE
                else:
                    #rewind playback by dynamic interval
                    self.yt.skip_forward(self.dynamic_interval)

            #exit iteration
            return

        if self.state == self.STATE_AFTER:
            #exit iteration
            return

        if self.state == self.STATE_PREGAMEWAIT:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                #change state
                self.yt.log_EVENT("VOD finished", True)
                self.state = self.STATE_AFTER
                return

            #check if left prematch lobby
            tSTAGE = self.fr.read_text(
                frame_in=self.frame, 
                xa=600, 
                xb=670, 
                ya=530, 
                yb=560, 
                threshold=190,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tSTAGE"
            )
            #if still in lobby
            if "STAGE" in tSTAGE.upper():
                self.yt.skip_forward(3)
            else:
                tOK = self.fr.read_text(
                    frame_in=self.frame, 
                    xa=625, 
                    xb=652, 
                    ya=398, 
                    yb=430, 
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_tOK"
                )
                #if connection error
                if "OK" in tOK.upper():
                    self.yt.log_EVENT(
                        message="Leaving Lobby.",
                        note="Connection error"
                    )
                    self.yt.end_lobby()

                    #advance playback by minimum pregame length
                    self.yt.skip_forward(self.min_pregame_length)

                    #change state
                    self.state = self.STATE_PREGAME
                #else go to ingame
                else:
                    #advance video playback by minimum match length
                    self.yt.skip_forward(self.min_match_length)
                    
                    #change state
                    self.state = self.ENTRY_INGAME

            #check if in a replay
            tAttackStartupFrames = self.fr.read_text(
                frame_in=self.frame, 
                xa=940, 
                xb=1059, 
                ya=582, 
                yb=595, 
                threshold=100,
                save_flag=self.imglog_flag,
                time_id=self.yt.get_time(),
                description="_tAttackStartupFrames"
            )
            if is_match("AttackStartupFrames", tAttackStartupFrames):
                self.yt.log_EVENT(
                    message="Leaving Lobby.",
                    note="Player is watching a replay"
                )
                self.yt.end_lobby()

                #increment playback time
                self.yt.skip_forward(self.min_pregame_length)

                #change state
                self.state = self.STATE_BEFORE

            #exit iteration
            return

        if self.state == self.STATE_INGAMEUNSURE:
            #check if vod is over
            if self.yt.playback_time >= self.yt.video_length:
                self.yt.playback_time == self.yt.video_length

                #change state
                self.yt.log_EVENT("VOD finished", True)
                self.state = self.STATE_AFTER
                return

            #check for ranked match (indicating left lobby) in case of rage quit
            for _ in range(self.igcheck):
                frame_check = self.yt.get_frame(self.state, self.imglog_flag)
                tRankedMatch = self.fr.read_text(
                    frame_in=frame_check,
                    xa=600, 
                    xb=690, 
                    ya=570, 
                    yb=590, 
                    save_flag=self.imglog_flag,
                    time_id=self.yt.get_time(),
                    description="_cRankedMatch"
                )
                #check for trigger
                if "RankedMatch" in tRankedMatch:
                    #if ranked match, go to pregame
                    self.yt.log_EVENT(
                        message="Connection error.",
                        note=f"Leaving lobby with {self.yt.opponent_name}"
                    )
                    self.yt.end_lobby()

                    #change state
                    self.state = self.STATE_PREGAME
                    break
                #if no trigger, increment
                else:
                    #increment video playback time
                    self.yt.skip_forward(self.pregame_interval)
            #else go to ingame
            else:
                #advance video playback by minimum match length
                self.yt.skip_forward(self.min_match_length - self.igcheck * self.pregame_interval)
                
                #change state
                self.state = self.ENTRY_INGAME

            #exit iteration
            return
        
#demo
if __name__ == "__main__":
    #initialize object
    tracker = Tekken8RankTracker(
        #must provide a url to a youtube vod, that has a 720p option (format '136')
        vod_url='https://www.youtube.com/watch?v=zeZ1NWkMKsI',

        #optional: when (in seconds) to start recording (must be at least a couple seconds before starting matchmaking)
        start_time=17541,

        #optional: when (in seconds)to stop recording (must be after leaving a lobby)
        # end_time=17600,

        #optional: video date (if not the same as the upload date)
        vod_date=20240223,

        #optional: set frame_log to True if you want to debug
        frame_log=True,

        #optional: set fsm initial state if 'Ranked Match' indicator does not appear
        # initial_state=Tekken8RankTracker.STATE_PREGAME
    )
    
    #start scraping
    while tracker.info.is_fsm_active():
        tracker.run_fsm()
        # print(tracker.info.get_preview())