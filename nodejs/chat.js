var http = require('http');
var server = http.createServer(
function(req,res)
{
    res.writeHead(200);
    res.end('Hello Http');
}).listen(5000);

var io = require('socket.io').listen(server);
var fs = require('fs');
var archiver = require('archiver');

var cookie_reader = require('cookie');
var querystring = require('querystring');

var redis = require('redis');
var sub = redis.createClient('6379', 'redis');
var cli = redis.createClient('6379', 'redis');
//Subscribe to the Redis chat channel
sub.subscribe('chat');
var count = 0;


//Configure socket.io to store cookie set by Django

/*
 io.configure(function(){
 io.set('authorization', function(data, accept){
 if(data.headers.cookie){
 data.cookie = cookie_reader.parse(data.headers.cookie);
 console.log(data.cookie);
 return accept(null, true);
 }
 return accept('error', false);
 });
 io.set('log level', 1);
 });
 */

sqlite3 = require('sqlite3').verbose();
var db = new sqlite3.Database(__dirname+'/db.sqlite3');

var socket_jobid_map = {};

sub.on('message', function (channel, message)
{
    var msgarr = JSON.parse(message);

    if( 'message' in msgarr){
        console.log("Message recieved from django");
        console.log(msgarr.socketid);

        if('jobid' in msgarr){
            socket_jobid_map[msgarr.socketid] = msgarr.jobid;
            io.sockets.socket(msgarr.socketid).emit('message', {jobid: msgarr.jobid});
        }


        io.sockets.socket(msgarr.socketid).emit('message', {name: msgarr.message});
        console.log(msgarr.message);
    }

    if ('jobinfo' in msgarr){
            io.sockets.socket(msgarr.socketid).emit('message', {jobinfo: msgarr.jobinfo});
        }

    if( 'done' in msgarr){
        console.log("Message recieved from django");
        console.log(msgarr.socketid);

        if('jobid' in msgarr){
            socket_jobid_map[msgarr.socketid] = msgarr.jobid;
            io.sockets.socket(msgarr.socketid).emit('message', {jobid: msgarr.jobid});
        }

        io.sockets.socket(msgarr.socketid).emit('message', {done: msgarr.done});
        console.log(msgarr.message);
    }
    if( 'exit' in msgarr){
        console.log("Error recieved from django");
        console.log(msgarr.socketid);

        io.sockets.socket(msgarr.socketid).emit('message', {exit: msgarr.exit});
        console.log(msgarr.message);
    }


    else if('error' in msgarr)
    {
        if ('end' in msgarr){
            io.sockets.socket(msgarr.socketid).emit('error', {error: msgarr.error, end: 'yes'});
        }else {
             io.sockets.socket(msgarr.socketid).emit('error', {error: msgarr.error});
        }
    }
    else if('web_result' in msgarr)
    {
        io.sockets.socket(msgarr.socketid).emit('message', {web_result: msgarr.web_result});
        console.log("Web Result Sent");
        //io.sockets.socket(msgarr.socketid).emit('message', {name: msgarr.web_result});
    }
});


var send_generated_results = function(output, socketid)
{
    cli.llen(output, function(err, length){
        console.log(length);
        for(var i=0; i<length; i++)
        {
            cli.lpop(output, function(err, path){
                console.log(i, path);
                io.sockets.socket(socketid).emit('message', {picture: path, jobid: socket_jobid_map[socketid]});
            });
        }
    });
};

/**
 * Packages local files into a ZIP archive
 *
 * @param {dir} directory of source files.
 * @param {name} the zip archive file name
 * return {void}
 */

var writeZip = function(list, socketid) {
    var dir;
    cli.get("CLOUDCV_ABS_DIR", function(err, result){
        dir = result;
        console.log(dir);
        var zipFullPath = dir + "/media/pictures"+"/decaf-server-" + socketid + ".tar";
        var zipName = "/media/pictures"+"/decaf-server-" + socketid + ".tar",
        output = fs.createWriteStream(zipFullPath),
        archive = archiver('tar');
        console.log(zipName);
        archive.pipe(output);

        list.forEach(function(item){
            console.log(item);
            itemtoken = item.split('/');
            archive.append(fs.createReadStream(dir + item), { name: itemtoken[itemtoken.length -1] });
        });

        archive.finalize(function(err, written) {
            if (err) {
                throw err;
            }
            // do cleanup
            cleanUp(dir);
        });
        console.log("Done creating tar file");
        io.sockets.socket(socketid).emit('tarFile', {tarFile: zipName});
    });

};

/**
 * Returns array of file names from specified directory
 *
 * @param {dir} directory of source files.
 * return {array}
 */
getDirectoryList = function(dir){
    var fileArray = [],
        files = fs.readdirSync(dir);
    console.log(files);
    files.forEach(function(file){
        var obj = {name: file, path: dir};
        fileArray.push(obj);
    });
    return fileArray;
};


io.sockets.on('connection', function (socket)
    {
        console.log(socket.id);
        io.sockets.socket(socket.id).emit('message', {socketid: socket.id, visit: count});
        count = count + 1;

        socket.on('disconnect', function () {
            console.log("Disconnected User: " + socket.id);
            delete socket_jobid_map[socket.id];
        });

        socket.on('getsocketid', function(message){
                io.sockets.socket(socket.id).emit('message', {socketid : socket.id, visit:count});
            });

        socket.on('send_message', function (message) {
            console.log(message);
            if (message == 'ImageStitch') {

                cli.hget(socket_jobid_map[socket.id], 'result_path', function (err, output)
                {
                    if (err){
                       io.sockets.socket(socket.id).emit('error', {message: err, end: 'yes'});
                    }
                    else{
                        send_generated_results(output, socket.id);
                        io.sockets.socket(socket.id).emit('message', {request_data: 'request_data'});
                    }
                });


            }
            if (message == 'VOCRelease5') {

                cli.hget(socket_jobid_map[socket.id], 'result_path', function (err, output)
                {
                    if (err){
                       io.sockets.socket(socket.id).emit('error', {message: err, end: 'yes'});
                    }else{
                        send_generated_results(output, socket.id);
                        io.sockets.socket(socket.id).emit('message', {request_data: 'request_data'});
                    }
                });
            }
            if (message == 'features')
            {

                cli.hget(socket_jobid_map[socket.id], 'result_path', function (err, output)
                {
                    if (err){
                       io.sockets.socket(socket.id).emit('error', {message: err});
                    }else{
                        send_generated_results(output, socket.id);
                        io.sockets.socket(socket.id).emit('message', {request_data: 'request_data'});
                    }
                });
            }
            if (message == 'classify')
            {
                io.sockets.socket(socket.id).emit('message', {request_data: 'request_data'});
            }

            if (message == 'data') {
                cli.hget(socket_jobid_map[socket.id], 'output', function (err, output) {
                    io.sockets.socket(socket.id).emit('message', {data: output});
                    //console.log(obj);
                });

            }
            if (message == 'socketid') {
                //  console.log(socket.id);

                io.sockets.socket(socket.id).emit('message', {socketid: socket.id});
            }

        });

        socket.on('get_tar', function(message){
            io.sockets.socket(socket.id).emit('error', {message: 'hellodo'});
            writeZip(message.list_of_files, socket.id);

        });
    }
);


