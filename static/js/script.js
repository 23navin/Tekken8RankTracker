// preview window
var preview_created = false;
var img = new Image();

function start_script() {
    $.ajax({
        type:'POST',
        url: '/start',
        success: function(data, status, request) {
            task_id = request.getResponseHeader('taskID');
            // status_url = request.getResponseHeader('Tstatus');
            // preview_url = request.getResponseHeader('Tpreview');

            update(task_id);
        }
    });

    preview_created = false;
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

function update(task_id) {
    $.getJSON('/status/'+task_id, function(data) {
        // state logic prep
        vPROCESSING = data['state'] == "PROCESSING"
        vSUCCESS = data['state'] == "SUCCESS"
        xSUCCESS = data['state'] != "SUCCESS"
        xFAILURE = data['state'] != "FAILURE"
        xREVOKED = data['state'] != "REVOKED"

        gstate = data['game_state']

        // telemetry
        document.getElementById('time_display').textContent=data['playback_time'];
        document.getElementById('state_display').textContent=data['game_state'];

        // preview
        if (vPROCESSING) {
            if (!preview_created) {
                var canvas = document.getElementById("previewCanvas")
                canvas.width = 1280;
                var ctx = canvas.getContext('2d');
                
                img.src = '/preview/'+task_id+'/'+data['playback_time'];
                
                img.onload = function() {
                    ctx.drawImage(img, 0, 0, 1280, 720)
                };

                preview_created = true;
            }

            img.src = '/preview/'+task_id+'/'+data['playback_time'];
        }

        // start/pause button text
        if (vPROCESSING) {
            document.getElementById('start-button').textContent="PAUSE";
        }
        else {
            document.getElementById('start-button').textContent="START";
        }

        if (vSUCCESS) {
            document.getElementById('start-button').textContent="START";
        }

        // call next update
        if (xSUCCESS && xFAILURE && xREVOKED) {
            setTimeout(function() {
                update(task_id);
            }, 500);
        }
    });
}

window.onload = function() {
    // check if there is a task currently running
    $.ajax({
        type:'POST',
        url: '/init',
        success: function(data, status, request) {
            active_tasks = data['task_count'];
            if (active_tasks > 0) {
                task_id = request.getResponseHeader('taskID');
                // status_url = request.getResponseHeader('Tstatus');
                // preview_url = request.getResponseHeader('Tpreview');

                update(task_id);
            }
        }
    });
};

$(function() {
    $('.inputs input').on('change', function() {
        console.log("Input changed!");  // Debug message

        let formData = {
            video_link: $('input[name="video_link"]').val(),
            video_date: $('input[name="video_date"]').val(),
            start_time: $('input[name="start_time"]').val(),
            end_time: $('input[name="end_time"]').val(),
            init_state: $('input[name="init_state"]').is(':checked'),
            log_input: $('input[name="log_input"]').is(':checked')
        };

        $.ajax({
            type: 'POST',
            url: '/set',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log("Inputs auto-saved.");
            },
            error: function() {
                console.error("Failed to auto-save inputs.");
            }
        });
    });
});