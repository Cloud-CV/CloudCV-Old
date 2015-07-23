/node_modules/forever/bin/forever -w start /home/user/chat.js
sleep 0.5
/node_modules/forever/bin/forever --fifo logs 0
