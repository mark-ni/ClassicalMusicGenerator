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
a given melody. For now, just implement a bass line that complements a soprano line (completed)

4) Generate a simple melody and transpose to music data structure

5) Web implementation using Flask

-----

<h3>Other notes</h3>
Piano samples taken from online soundbanks found at http://freepats.zenvoid.org/
- All keys except 4 come from Upright Piano KW (http://freepats.zenvoid.org/Piano/honky-tonk-piano.html)
- D#3, F#2, and F#4 are taken from Piano FB (http://freepats.zenvoid.org/Piano/acoustic-grand-piano.html - top source)
- G2 was recorded manually with quicktime and the Guzhe piano app on my phone

The sample song used to test the algorithms in this project is a version of question 6 on the 1998 AP Music Theory Exam, transposed to C Major: https://secure-media.collegeboard.org/apc/music-theory-released-exam-1998.pdf
