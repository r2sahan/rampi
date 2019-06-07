#!/bin/bash
# 1-59 * * * *

DIN=/home/pi/timelapse/in
DOUT=/home/pi/timelapse/out

x=1
while [ $x -le 60 ]; do
filename=$(date -u +"%d%m%Y_%H%M-%S").jpg
fswebcam -d /dev/video0 -r 640x480 $DIN/$filename
fswebcam -d /dev/video1 -r 640x480 $DOUT/$filename
x=$(( $x + 1 ))
sleep 30;
done;

cd $DIN
ls *.jpg > timelapse.txt
mencoder -nosound -ovc lavc -lavcopts vcodec=mpeg4:aspect=16/9:vbitrate=8000000 -vf scale=640:480 -o timelapse.avi -mf type=jpeg:fps=24 mf://@timelapse.txt

cd $DOUT
ls *.jpg > timelapse.txt
mencoder -nosound -ovc lavc -lavcopts vcodec=mpeg4:aspect=16/9:vbitrate=8000000 -vf scale=640:480 -o timelapse.avi -mf type=jpeg:fps=24 mf://@timelapse.txt