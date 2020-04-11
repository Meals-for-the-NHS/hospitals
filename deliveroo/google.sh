#!/bin/bash

delay="0.8"
while read url; do
	echo downloading "$url"
	chromium "$url"
	sleep $delay
	xdotool mousemove 1900 80 key ctrl+s
	sleep $delay
	xdotool key KP_Enter
	sleep $delay
	xdotool key ctrl+w
	sleep $delay
done <google.urls

