
import os
import requests

from collections import deque
from flask import Flask, flash, jsonify, session, render_template, request, redirect, url_for
from flask_session import Session

from flask_socketio import SocketIO, emit, join_room, leave_room
from helpers import error, login_required


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)


# Keep track of users logged in, channel lists and messages in each channel
usersLogged = []
channel_list = []
channelsMessages = dict()


@app.route("/")
@login_required
def index():
    return render_template("index.html", channel_list=channel_list)


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    ''' Save username on a Flask session after user submit the sign in form '''

    # Forget any username
    session.clear()

    username = request.form.get("username")

    if request.method == "POST":

        # Ensure username was submitted
        if not username:
            return error("Missing username", 400)
        # Check if username already exists
        if username in usersLogged:
            return error("Username already taken.", 400)

        usersLogged.append(username)

        session['username'] = username

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("signin.html")


@app.route("/create", methods=['GET', 'POST'])
@login_required
def create():
    ''' Create new channel after user is logged in. '''

    newChannel = request.form.get("newChannel")

    if request.method == "POST":

        # Ensure channel name is submitted
        if not newChannel:
            return error("Missing channel name.", 400)

        if newChannel in channel_list:
            return error("Channel already exists.", 400)

        channel_list.append(newChannel)
        session['current_channel'] = newChannel

        # Add channel to a global dict of channels with messages. Every channel is a deque with maxlen of 100.
        # Once length of deque reach 100, when new items are added, a corresponding number of items are discarded from the opposite end.
        # https://docs.python.org/3/library/collections.html#collections.deque
        channelsMessages[newChannel] = deque(maxlen=100)

        # Redirect user to channel page
        return redirect(url_for('channel', curChannel=newChannel))

    else:
        return redirect("/")


@app.route("/channel/<curChannel>", methods=['GET', 'POST'])
@login_required
def channel(curChannel):
    ''' Display current channel. '''

    session['current_channel'] = curChannel

    if request.method == "POST" or curChannel not in channel_list:
        return redirect("/")
    else:
        # Redirect user to current channel page
        return render_template("channel.html", curChannel=curChannel, messages=channelsMessages[curChannel])


@app.route("/logout")
def logout():
    """Log user out"""

    # Remove from list
    try:
        usersLogged.remove(session['username'])
    except ValueError:
        pass

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    return redirect("/")


@socketio.on("joined")
def joined():
    """ Update status that user has entered the channel """

    # Save current channel to join room.
    room = session.get('current_channel')

    join_room(room)

    emit('status', {'channel': room})


@socketio.on("left")
def left():
    """ Update room when user leaves the channel """

    room = session.get('current_channel')

    leave_room(room)


@socketio.on("send message")
def send_msg(msg, timestamp):
    """ Receive message with timestamp, then broadcast on the channel """

    # Broadcast only to users on the same channel.
    room = session.get('current_channel')

    channelsMessages[room].append([timestamp, session.get('username'), msg])

    emit('announce message', {
        'user': session.get('username'),
        'timestamp': timestamp,
        'msg': msg},
        room=room)


if __name__ == "__main__":
    socketio.run(app)
