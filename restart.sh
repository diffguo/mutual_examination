#/bin/sh

kill -9 `cat /run/mutual_examination.pid`
sleep 1
uwsgi uwsgi.ini