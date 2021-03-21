# ClassicalMusicGenerator
(Work in Progress)

Program to convert back and forth between sheet music and computer-readable data,
allowing for implementation of logical music structures like chords, and auto-generation
of melodies and harmonies

-------------

<h3> Instructions </h3>

1) Install ffmpeg if it's not on your computer already. On Mac this is:

brew install ffmpeg

2) Run main.py

------

<h3>General planned stages of development</h3>

1) Implement basic structure for music score and use audio library to play a song inputted
manually into the files (completed)

2) Create system of musical data structures, most importantly chords. Given a score,
identify and rank the best fits for chords for every strong beat (completed)

3) Using basic classical music theory principles, implement a fsm-esque system to harmonize
a given melody. For now, just implement a bass line that complements a soprano line

4) Generate a simple melody and transpose to music data structure

5) Web implementation using Flask