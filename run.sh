#!/bin/sh
rm start.m3u main.m3u prefix prefix postfix space
rm -r gates pins intermediate
mkdir -p gates pins intermediate
printf "#EXTINF:123,result " > ./prefix
printf " " > ./space
printf "\nvlc://pause:10" > ./postfix
printf 0 > ./pins/0
printf 1 > ./pins/1
python3 gen.py
/Applications/VLC.app/Contents/MacOS/VLC -I macosx --extraintf http --http-password a --http-port 80 ./start.m3u
