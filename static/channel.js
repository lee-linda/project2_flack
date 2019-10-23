
document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // When connected, configure button
    socket.on('connect', () => {

       // Notify the server user has joined
        socket.emit('joined');

        // Remove user's last channel when go to homepage
        document.querySelector('#home').addEventListener('click', () => {
            localStorage.removeItem('last_channel');
        });

        // When user leaves channel redirect to '/'
        document.querySelector('#leave').addEventListener('click', () => {
            // Notify the server user has left channel
            socket.emit('left');
            // Remove user's last channel, then go to homepage
            localStorage.removeItem('last_channel');
            window.location.replace('/');
        })

        // Remove user's last channel when logged out
        document.querySelector('#logout').addEventListener('click', () => {
            localStorage.removeItem('last_channel');
        });


        // 'Enter' key on textarea also sends message
        document.querySelector('#msg').addEventListener("keydown", event => {
            if (event.key == "Enter") {
                document.getElementById("send-button").click();
            }
        });

        // Send button emits a "send message" event
        document.querySelector('#send-button').addEventListener("click", () => {
            // Save time in format HH:MM:SS
            let timestamp = new Date;
            timestamp = timestamp.toLocaleTimeString();

            // Save user message
            let msg = document.getElementById("msg").value;

            socket.emit('send message', msg, timestamp);

            // Clear message bar
            document.getElementById("msg").value = '';
        });
    });

    // When user joins a channel, set last channel for user.
    socket.on('status', data => {
        // Save user current channel on localStorage
        localStorage.setItem('last_channel', data.channel)

    })

    // When a message is announced, append it to the textarea.
    socket.on('announce message', data => {
            // Format message
            let row = `${data.timestamp}` + ' [ ' + `${data.user}` + ' ]:  ' + `${data.msg}`
            document.querySelector('#chat').value += row + '\n'
        // }
    })

});
