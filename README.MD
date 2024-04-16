# Tekken 8 Rank Tracker

A Python script that uses OpenCV and PyTesseract to track a player's Tekken 8 rank progression from a youtube vod.

## Status

This is a personal project and my first time using python. It is not complete and will probably go through many revisions as I learn the language and get better at image/text detection.

As of right now: It is fully functional and can scrape a vod with few errors. There are a few edge cases that will cause it to miss key game events and break the fsm. I am also trying to find ways to speed up the script. Once I am happy with the data acquisition script, I will be creating a graphical representation of the data using react (like python, this will be my first time developing js so it will take some time).

If you come across this project, and have any thoughts on either the Tekken or Python aspects, I would love to hear from you (see my gh profile).

## To Do List

1. Detect when player is in training but not looking for match
2. Rating adj only tracks neg adjustments (filter red/blue channel)
3. Docker is missing libraries and won't build
4. Put rank images on a neutral-grey background. May improve matching accuracy.
   1. Vanquisher rank may be mis-identified as MightyRuler
   2. Destroyer rank may be mis-identified as Eliminator
   3. Brawler rank may be mis-identified as TekkenGod
5. use sequencematching for fighter detection
6. Add more context to console logging
7. pyTesseract reads numbers incorrectly sometimes (read 2550 as 2900)

## Features to add

1. Allow multiple resolutions
2. Multithreading
3. Graphical representation of data using React
