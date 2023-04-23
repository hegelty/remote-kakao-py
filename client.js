importClass(
    java.net.ServerSocket,
    java.io.BufferedReader,
    java.io.InputStreamReader,
    java.io.OutputStream,
);

var socket = null;

const thread = new java.lang.Thread(
    new java.lang.Runnable({
            run() {
                socket = new java.net.Socket("192.168.0.8", 8080);
                socket.setSoTimeout(3000);
                msg = JSON.stringify({
                    "t": 0
                })
                output = socket.getOutputStream();
                output.write((new java.lang.String(msg)).getBytes());
                output.flush();
                socketReciver();
            }
        }
    )
)

function socketReciver() {
    try {
        let input = socket.getInputStream();
        let new_message = true;
        let msg_size = 0;
        let msg_size_2 = 0;
        let recv_data = [];
        let line = new java.nio.ByteBuffer.allocate(128).array();
        while(1) {
            try {
                if(new_message) {
                    input.read(line);
                    let decoded = String.fromCharCode.apply(null, line);
                    let header_size = (decoded.split('\n')[0] + "\n").length;
                    msg_size = parseInt(decoded.split('\n')[0].slice(1,-1)) - 128 + header_size;
                    msg_size_2 = msg_size + 128;
                    new_message = false;
                    recv_data = decoded.slice(header_size);
                }
                else if(msg_size > 128) {
                    input.read(line);
                    msg_size -= 128;
                    recv_data = recv_data.concat(String.fromCharCode.apply(null, line));
                }
                else {
                    if (msg_size > 0) {
                        let line = new java.nio.ByteBuffer.allocate(msg_size).array();
                        input.read(line);
                        recv_data = recv_data.concat(String.fromCharCode.apply(null, line));
                    }
                    new_message = true;
                    msg_size = 0;

                    Log.d(recv_data);
                    let data = JSON.parse(recv_data);
                    input.close();
                    input = socket.getInputStream();

                    Log.d(JSON.stringify(data));
                    kakaoSender(data);
                }

                if(socket.isConnected() && socket.getKeepAlive()) {
                    socket.setKeepAlive(true);
                    if(!socket.getKeepAlive()) {
                        socket.close();
                        return 1;
                    }
                }
            } catch (e) {
                Log.e(e + " " + e.lineNumber);
                return 1;
            }
        }
        return;
    } catch (e) {
        Log.e(e);
    }
}

function socketSender(msg) {
    output = socket.getOutputStream();
    output.write((new java.lang.String(msg)).getBytes());
    output.flush();
}

function kakaoSender(msg) {
    if(msg.t == 0) {
        Api.replyRoom(msg.r, msg.m);
    }
}

function onStartCompile() {
	return thread.interrupt();
}
thread.start();

function responseFix(room, msg, sender, isGroupChat, replier, imageDB, packageName) {
    socketSender(JSON.stringify({
        "r": room,
        "m": msg,
        "s": sender,
        "G": isGroupChat
    }));
}

// notification fix by DarkTornado
// https://cafe.naver.com/nameyee/39192
function onNotificationPosted(sbn, sm) {
    var packageName = sbn.getPackageName();
    if (!packageName.startsWith("com.kakao.tal")) return;
    var actions = sbn.getNotification().actions;
    if (actions == null) return;
    var userId = sbn.getUser().hashCode();
    for (var n = 0; n < actions.length; n++) {
        var action = actions[n];
        if (action.getRemoteInputs() == null) continue;
        var bundle = sbn.getNotification().extras;

        var msg = bundle.get("android.text").toString();
        var sender = bundle.getString("android.title");
        var room = bundle.getString("android.subText");
        if (room == null) room = bundle.getString("android.summaryText");
        var isGroupChat = room != null;
        if (room == null) room = sender;
        var replier = new com.xfl.msgbot.script.api.legacy.SessionCacheReplier(packageName, action, room, false, "");
        var icon = bundle.getParcelableArray("android.messages")[0].get("sender_person").getIcon().getBitmap();
        var image = bundle.getBundle("android.wearable.EXTENSIONS");
        if (image != null) image = image.getParcelable("background");
        var imageDB = new com.xfl.msgbot.script.api.legacy.ImageDB(icon, image);
        com.xfl.msgbot.application.service.NotificationListener.Companion.setSession(packageName, room, action);
        if (this.hasOwnProperty("responseFix")) {
            responseFix(room, msg, sender, isGroupChat, replier, imageDB, packageName, userId != 0);
        }
    }
}