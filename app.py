#web framework
from flask import Flask, render_template, jsonify, url_for, request, session, redirect, Response

#queue api
from celery import Celery

#server api
from redis import Redis

#task
from src.T8RankTracker.tracker import Tekken8RankTracker
from src.T8RankTracker.constants import asciiColor as asciiColor

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

#logging
def message(message:str):
    # print(f"[ACTION] {message}")
    print(f"{asciiColor.bg.GREEN} [ACTION] {asciiColor.reset}{asciiColor.bg.bright.GREEN} {message} {asciiColor.reset}")


#main task
@celery.task(bind=True)
def mtask(self, video_link, video_date, start_time, end_time, frame_log, initial_state):
    #response package
    dpackage = {
        'playback_time' : 'initializing',
        'game_state' : 'initializing',
        'preview' : None
    }
    #update redis
    self.update_state(state='PROCESSING', meta=dpackage)
    redis.set("current_task", self.request.id)

    #initialize task
    tracker = Tekken8RankTracker(
        vod_url=video_link,
        format='311', #avc1.640020 1280x720 60
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
                message("pausing...")
                self.update_state(state='PAUSED', meta=dpackage)
            sleep(1)
        if task.state == 'RESUME':
            message("resuming...")
            self.update_state(state='PROCESSING', meta=dpackage)

        #run tracker
        tracker.run_fsm()
        
        #update response package
        dpackage['playback_time'] = tracker.info.get_time()
        dpackage['game_state'] = tracker.info.get_state()

        imag = tracker.info.get_preview()
        # print(imag)
        
        preview_buffer = b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + imag + b'\r\n'
        dpackage['preview'] = preview_buffer

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
    
    return redirect(url_for('index'))

@app.route('/set', methods=['POST'])
def set_inputs():
    data = request.get_json()
    
    session['video_link'] = data['video_link']
    session['video_date'] = data['video_date']
    session['start_time'] = data['start_time']
    session['end_time'] = data['end_time']
    session['initial_state'] = data['init_state']
    session['frame_log'] = data['log_input']
    
    message(f"autosaved inputs \nvideo_link: {session['video_link']}\nvideo_date: {session['video_date']}\nstart_time: {session['start_time']}\nend_time: {session['end_time']}\ninitial_state: {session['initial_state']}\nframe_log: {session['frame_log']}")
    
    return '', 204

@app.route('/init', methods=['POST'])
def get_ids():
    cinfo = celery.control.inspect().active().popitem()[1]
    response = {'task_count': len(cinfo)}

    if len(cinfo):
        task_id = cinfo[0].get('id')
        HTTPresponse = {
            'taskID': task_id
            # 'Tstatus': url_for('tracker_status', task_id=task_id),
            # 'Tpreview': url_for('tracker_preview', task_id=task_id)
        }
        return jsonify(response), 200, HTTPresponse
    else:
        return jsonify(response), 200

@app.route('/start', methods=['POST'])
def run_tracker():

    video_link = session['video_link']
    
    start_time = session['start_time']
    if start_time == '':
        start_time = None
    else:
        start_time = int(start_time)
        
    end_time = session['end_time']
    if end_time == '':
        end_time = None
    else:
        end_time = int(end_time)
    
    video_date = int(session['video_date'])

    if session['initial_state']:
        initial_state = Tekken8RankTracker.STATE_PREGAME
    else:
        initial_state = Tekken8RankTracker.STATE_BEFORE

    if session['frame_log']:
        frame_log = True
    else:
        frame_log = False

    task = mtask.apply_async(args=[video_link, video_date, start_time, end_time, frame_log, initial_state])

    message(f"Task {task.id} started")
    
    HTTPresponse = {
        'taskID': task.id
        # 'Tstatus': url_for('tracker_status', task_id=task.id),
        # 'Tpreview': url_for('tracker_preview', task_id=task.id)
    }

    return jsonify({}), 202, HTTPresponse


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
    
    message(f"Task {task.id} stopped")

    return jsonify ({}), 200

@app.route('/status/<task_id>')
def tracker_status(task_id):
    task = mtask.AsyncResult(task_id)

    if task.state == 'SUCCESS':
        response = {
            'state' : task.state,
            'playback_time' : 'celerySuccess',
            'game_state' : 'celerySuccess',
        }
        
        message(f"Task {task_id} completed successfully")
        
    elif task.state == 'FAILURE':
        response = {
            'state' : task.state,
            'playback_time' : "celeryFailure",
            'game_state' : "celeryFailure",
        }
        
        message(f"Task {task_id} failed")
        
    elif task.state == 'REVOKED':
        response = {
            'state' : task.state,
            'playback_time' : "revoked",
            'game_state' : "revoked",
        }
        
        message(f"Task {task_id} revoked")
        
    elif task.state == 'PENDING' or task.state == 'STARTED':
        response = {
            'state' : task.state,
            'playback_time' : 'celeryPending',
            'game_state' : 'celeryPending',
        }
        
    else:
        response = {
            'state' : task.state,
            'playback_time' : task.info.get('playback_time', '--'),
            'game_state' : task.info.get('game_state', '--'),
        }

    return jsonify(response)

@app.route('/preview/<task_id>/<playback_time>')
def tracker_preview(task_id, playback_time):
    task = mtask.AsyncResult(task_id)
    image = task.info.get('preview')

    return Response(image, mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="23232", debug=True)