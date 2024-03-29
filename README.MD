# Tekken 8 Rank Tracker

A Python script that uses OpenCV and PyTesseract to track a player's Tekken 8 rank progression from a youtube vod.

## Status

This is a personal project and my first time using python. It is not complete and will probably go through many revisions as I learn the language and get better at image/text detection.

As of right now: It is fully functional and can scrape a vod with few errors. There are a few edge cases that will cause it to miss key game events and break the fsm. I am also trying to find ways to speed up the script. Once I am happy with the data acquisition script, I will be creating a graphical representation of the data using react (like python, this will be my first time developing js so it will take some time).

If you come across this project, and have any thoughts on either the Tekken or Python aspects, I would love to hear from you (see my gh profile).

## To Do List

1. Detect when player is in training but not looking for match
2. Rating adj only tracks neg adjustments (filter red/blue channel)
3. Tesseract has a hard time recognizing single-digit numbers (eg. a clean image of a '0' returns nothing, 'JACK-8' is read as 'JACK-B')
4. Improve opponent name detection
5. Docker is missing libraries and won't build
6. Save incomplete postgame if vod ends early
7. Seperate some while loops into their own states
   1. Seperate entering match loop from pre game
   2. Seperate waiting for rematch or leave lobby loop from post game
8. Support higher resolutions

## Features to add

1. Automatically find all Tekken vods in a youtube channel
2. Allow multiple resolutions
3. Multithreading
4. Graphical representation of data using React
