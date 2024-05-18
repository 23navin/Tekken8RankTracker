#web framework
from flask import Flask, render_template, jsonify, url_for, request, session, redirect

#queue api
from celery import Celery

#server api
from redis import Redis

#task
from src.T8RankTracker import Tekken8RankTracker

#
from time import sleep
import json

#setup Flask object
app = Flask(__name__)
app.config['SECRET_KEY'] = 'buh'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


#setup Celery object
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

#setup Redis object
redis = Redis()

#main task
@celery.task(bind=True)
def mtask(self, video_link, video_date, start_time, end_time, frame_log, initial_state):
    #response package
    dpackage = {
        'playback_time' : 'initialzing',
        'game_state' : 'initializing',
        'preview' : None
    }
    #update redis
    self.update_state(state='PROCESSING', meta=dpackage)
    redis.set("current_task", self.request.id)

    #initialize task
    tracker = Tekken8RankTracker(
        vod_url=video_link,
        start_time=start_time,
        end_time=end_time,
        vod_date=video_date,
        frame_log=frame_log,
        initial_state=initial_state
    )

    #loop
    while tracker.info.is_fsm_active():
        #pause/play celery task
        task = celery.AsyncResult(self.request.id)
        while task.state == 'PAUSING' or task.state == 'PAUSED':
            if task.state == 'PAUSING':
                print("pausing...")
                self.update_state(state='PAUSED', meta=dpackage)
            sleep(1)
        if task.state == 'RESUME':
            print("resuming...")
            self.update_state(state='PROCESSING', meta=dpackage)

        #run tracker
        tracker.run_fsm()
        
        #update response package
        dpackage['playback_time'] = tracker.info.get_time()
        dpackage['game_state'] = tracker.info.get_state()
        dpackage['preview'] = tracker.info.get_preview()

        #update redis
        self.update_state(state='PROCESSING', meta=dpackage)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template(
            "index.html", 
            video_link=session.get('video_link',''),
            video_date=session.get('video_date',''),
            start_input=session.get('start_time',''),
            end_input=session.get('end_time',''),
            init_state=session.get('initial_state',"None"),
            log_input=session.get('frame_log',"on")
        )
    
    video_link = request.form['video_link']
    session['video_link'] = video_link

    video_date = request.form['video_date']
    session['video_date'] = video_date

    start_time = request.form['start_time']
    session['start_time'] = start_time

    end_time = request.form['end_time']
    session['end_time'] = end_time

    initial_state = request.form.get('init_state')
    session['initial_state'] = initial_state

    frame_log = request.form.get('log_input')
    session['frame_log'] = frame_log
    
    return redirect(url_for('index'))

@app.route('/init', methods=['POST'])
def get_ids():
    cinfo = celery.control.inspect().active().popitem()[1]
    response = {'task_count': len(cinfo)}

    if len(cinfo):
        return jsonify(response), 200, {'Location': url_for('tracker_status', task_id=cinfo[0].get('id'))}
    else:
        return jsonify(response), 200

@app.route('/start', methods=['POST'])
def run_tracker():

    video_link = session['video_link']
    video_date = int(session['video_date'])
    start_time = int(session['start_time'])
    end_time = int(session['end_time'])

    if session['initial_state']:
        initial_state = Tekken8RankTracker.STATE_PREGAME
    else:
        initial_state = Tekken8RankTracker.STATE_BEFORE

    if session['frame_log']:
        frame_log = True
    else:
        frame_log = False

    task = mtask.apply_async(args=[video_link, video_date, start_time, end_time, frame_log, initial_state])
    return jsonify({}), 202, {'Location': url_for('tracker_status', task_id=task.id)}


@app.route('/playpause', methods=['POST'])
def pause_tracker():
    task_id = celery.control.inspect().active().popitem()[1][0].get('id')
    task = celery.AsyncResult(task_id)

    key = f"celery-task-meta-{task_id}"
    bstr = redis.get(key)
    task_dict = json.loads(bstr)

    if task.state != 'PROCESSING':
        task_dict['status'] = "RESUME"
    else:
        task_dict['status'] = "PAUSING"

    ostr = json.dumps(task_dict)
    redis.set(key, ostr)

    return jsonify({}), 200

@app.route('/stop', methods=['POST'])
def stop_tracker():
    task_id = celery.control.inspect().active().popitem()[1][0].get('id')
    task = celery.AsyncResult(task_id)
    task.revoke(terminate=True)

    return jsonify ({}), 200

@app.route('/status/<task_id>')
def tracker_status(task_id):
    task = mtask.AsyncResult(task_id)

    if task.state == 'SUCCESS':
        response = {
            'state' : task.state,
            'playback_time' : task.info.get('playback_time', '--'),
            'game_state' : task.info.get('game_state', '--'),
        }
    elif task.state == 'FAILURE' or task.state == 'REVOKED':
        response = {
            'state' : task.state,
            'playback_time' : "revoked",
            'game_state' : "revoked",
        }
    elif task.state == 'PENDING' or task.state == 'STARTED':
        response = {
            'state' : task.state,
            'playback_time' : 'celeryPending',
            'game_state' : 'celeryPending',
            # 'preview' : task.info.get('preview')
        }
    else:
        response = {
            'state' : task.state,
            'playback_time' : task.info.get('playback_time', '--'),
            'game_state' : task.info.get('game_state', '--'),
            # 'preview' : task.info.get('preview')
        }

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="23232", debug=True)