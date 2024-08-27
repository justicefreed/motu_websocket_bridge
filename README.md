# MOTU AVB Websocket Bridge

A tornado websocket server to bridge HTTP requests to/from a MOTU AVB interface's datastore API.

For Datastore API, see [MOTU AVB Datastore API Docs](https://cdn-data.motu.com/downloads/audio/AVB/docs/MOTU%20AVB%20Web%20API.pdf)

For testing connectivity to a virtual device, use my [MOTU Development AVB Server](https://github.com/ChristopherJohnston/motu_server) repository.

# Usage

In the command line at the project root, call

```
./run --avbserver http://localhost:8888 --port 8889
```

Websocket connections can be made from, for example, Chrome DevTools as follows:

```
var ws = new WebSocket("ws://localhost:8889/datastore");
ws.onopen = function() {
    console.log("opened")
};

ws.onmessage = function (evt) {
    console.log(evt.data)
};
```

Updates can be sent using:

```
ws.send(JSON.stringify({ "ext/ibankDisplayOrder": "2:1:0"}));
```
