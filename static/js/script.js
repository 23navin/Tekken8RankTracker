function start_script() {
    $.ajax({
        type:'POST',
        url: '/start',
        success: function(data, status, request) {
            status_url = request.getResponseHeader('Location');
            update(status_url);
        }
    });
}

function pause_script() {
    $.ajax({
        type:'POST',
        url: '/playpause'
    });
}

function stop_script(){
    $.ajax({
        type:'POST',
        url: '/stop'
    });
}

function startstop() {
    $.ajax({
        type:'POST',
        url: '/init',
        success: function(data, status, request) {
            active_tasks = data['task_count'];
            if (active_tasks > 0) {
                pause_script();
            }
            else {
                start_script();
            }
        }
    });
}

function stop() {
    $.ajax({
        type:'POST',
        url: '/init',
        success: function(data, status, request) {
            active_tasks = data['task_count'];
            if (active_tasks > 0) {
                stop_script();
            }
        }
    });
}

$(function() {
    $('#start-button').click(startstop);
});

$(function() {
    $('#stop-button').click(stop);
});

function update(status_url) {
    $.getJSON(status_url, function(data) {
        vPROCESSING = data['state'] == "PROCESSING"
        xSUCCESS = data['state'] != "SUCCESS"
        xFAILURE = data['state'] != "FAILURE"
        xREVOKED = data['state'] != "REVOKED"


        document.getElementById('time_display').textContent=data['playback_time'];
        document.getElementById('state_display').textContent=data['game_state'];

        if (vPROCESSING) {
            document.getElementById('start-button').textContent="PAUSE";
        }
        else {
            document.getElementById('start-button').textContent="START";
        }

        if (xSUCCESS && xFAILURE && xREVOKED) {
            setTimeout(function() {
                update(status_url);
            }, 500);
        }
    });
}

window.onload = function() {
    $.ajax({
        type:'POST',
        url: '/init',
        success: function(data, status, request) {
            active_tasks = data['task_count'];
            if (active_tasks > 0) {
                status_url = request.getResponseHeader('Location');
                update(status_url);
            }
        }
    });
};