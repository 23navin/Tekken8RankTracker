from src.T8RankTracker import Tekken8RankTracker

#initialize object
vod = Tekken8RankTracker(
    #must provide a url to a youtube vod, that has a 720p option (format '136')
    vod_url='https://www.youtube.com/watch?v=xNwpdOUIbeg',

    #optional: when (in seconds) to start recording (must be at least a couple seconds before starting matchmaking)
    start_time=14810,

    #optional: when (in seconds)to stop recording (must be after leaving a lobby)
    # end_time=15420, 

    #optional: set frame_log to True if you want to debug
    frame_log=True,

    #optional: set fsm initial state if 'Ranked Match' indicator does not appear
    # initial_state=Tekken8RankTracker.STATE_PREGAME
)

#start scraping
while vod.info.is_fsm_active():
    vod.run_fsm()