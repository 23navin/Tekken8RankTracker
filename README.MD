# Tekken 8 Rank Tracker

A Python script that uses OpenCV and PyTesseract to track a player's Tekken 8 rank progression from a youtube vod. This is a personal project and my first time using python. It is not complete and will probably go through many revisions as I learn the language and get better at image/text detection.

## To Do List

1. Calibrate sampling intervals and skips (to increase performance)
2. Find a way to make cv2.set(CAP_PROP_POS_MSEC) faster (to increase performance)
3. Find a way to detect when the player has stopped playing Tekken before the vod has finished (to increase performance)
4. Improve 'left lobby' detection (by reading match result dots and inferring whether a rematch is possible or not)

## Features to add

1. Automate finding vods and queueing them for processing. Right now, the script has to be run manually on each vod.
2. Output all game/rank data to csv (so that it can be analyzed)
3. Create an graphic interface to represent rank data usng react (to highlight interesting trends)
