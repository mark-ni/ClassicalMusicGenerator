from pydub import AudioSegment
from pydub.playback import play
from sys import stdout
from heapq import heappush
from music_structures import *

LENGTH = 8
MAX_KEYS = 10
TEMPO = 100
BEAT_TIME = round(15000 / TEMPO)
KEY = ['C', 'MAJOR']
KEYID = -1  # Will be set below

if LENGTH > 32:
    quit()

# ID for the key the song is played in
KEYID = Note.getValueByKey(KEY[0])
# Score of music
Score = [[Note('r', 1, True) for j in range(MAX_KEYS)] for i in range(16 * LENGTH)]
# Records the highest number of used channels at any given point to optimize
# extraction of wav file at the end
maxUsedChannels = [0]


def generateChordSet(quality):
    chordSet = {}
    intervals = ChordFamily.getIntervals(quality)
    intervalKeys = ChordFamily.getIntervalQualities(quality)

    # TODO: REPLACE THIS HARDCODED THING WITH ACTUAL DICT KEY IMPLEMENTATION
    dict_keys = {1: 'I', 2: 'ii', 3: 'iii', 4: 'IV', 5: 'V', 6: 'vi', 7: 'vii°'}
    if quality == 'MINOR':
        dict_keys = {1: 'i', 2: 'ii°', 3: 'III⁺', 4: 'iv', 5: 'V', 6: 'VI', 7: 'vii°'}

    for i in range(1, 8):
        chordKeyNoOct = Note.getKeyByValue((KEYID + intervals[i - 1]) % 12)
        chordQuality = intervalKeys[i - 1]
        rel = (ord(chordKeyNoOct[0]) - ord(KEY[0][0])) % 7 + 1
        chordSet[dict_keys[i]] = ChordFamily(chordKeyNoOct, chordQuality, KEY[0])

    # Implement V7s later: right now just hardcode V7/V
    # TODO: REPLACE THIS HARDCODED THING WITH ACTUAL DICT KEY IMPLEMENTATION
    chordSet['V7/V'] = ChordFamily('D', 'SEVENTH', KEY[0])
    chordSet['V7/ii'] = ChordFamily('A', 'SEVENTH', KEY[0])
    chordSet['V7/IV'] = ChordFamily('C', 'SEVENTH', KEY[0])
    chordSet['V7/vi'] = ChordFamily('E', 'SEVENTH', KEY[0])
    chordSet['V7/iii'] = ChordFamily('B', 'SEVENTH', KEY[0])
    chordSet['V7'] = ChordFamily('G', 'SEVENTH', KEY[0])
    return chordSet


# Set of viewable chord files
ChordSet = generateChordSet(KEY[1])
Chords = [0 for i in range(LENGTH * 4)]


def add_note(key, duration, time, measure):
    channel = 0
    while channel < MAX_KEYS - 1:
        if Score[measure * 16 + time][channel].key == 'r':
            break
        channel += 1
    maxUsedChannels[0] = max(maxUsedChannels[0], channel + 1)
    for timeLeft in range(duration, 0, -1):
        # print("add_note: Note(",key,timeLeft,")")
        Score[measure * 16 + time + duration - timeLeft][channel] = Note(key, timeLeft)
    Score[measure * 16 + time][channel].fresh = True


def getSound(note):
    if note.key == 'r':
        return AudioSegment.silent(BEAT_TIME)
    try:
        return AudioSegment.from_wav("samples/" + note.key + ".wav")[:note.duration * BEAT_TIME]
    except FileNotFoundError:
        return AudioSegment.silent(BEAT_TIME * note.duration)


def write_sample_song():
    song = [['G4', 4, 0, 0], ['E4', 4, 4, 0], ['D4', 6, 8, 0], ['E4', 2, 14, 0],
            ['F4', 4, 0, 1], ['D4', 4, 4, 1], ['C4', 8, 8, 1],
            ['A4', 4, 0, 2], ['G4', 4, 4, 2], ['C5', 4, 8, 2], ['C5', 2, 12, 2], ['B4', 2, 14, 2],
            ['A4', 4, 0, 3], ['F#4', 4, 4, 3], ['G4', 8, 8, 3],
            ['A4', 4, 0, 4], ['F4', 4, 4, 4], ['D4', 4, 8, 4], ['E4', 2, 12, 4], ['F4', 2, 14, 4],
            ['G4', 4, 0, 5], ['E4', 2, 4, 5], ['D4', 2, 6, 5], ['C4', 4, 8, 5], ['C5', 2, 12, 5], ['B4', 2, 14, 5],
            ['A4', 4, 0, 6], ['F4', 4, 4, 6], ['E4', 2, 8, 6], ['D4', 2, 10, 6], ['C4', 2, 12, 6], ['B3', 2, 14, 6],
            ['C4', 16, 0, 7]]
    for note in song:
        # print("write_sample_song: add_note(", note[0],note[1],note[2],note[3], ")")
        add_note(note[0], note[1], note[2], note[3])
    #for i in range(LENGTH):
    #    add_note('C4', 4, 0, i)
    #    add_note('C4', 4, 4, i)
    #    add_note('C4', 4, 8, i)
    #    add_note('C4', 4, 12, i)


def generateChordStructure():
    for beat in range(LENGTH * 4):
        # create set of notes played on strong part of beat
        dominantKeysOnBeat = set()
        baseNote = 100
        for note in Score[beat * 4]:
            if note.key != 'r':
                baseNote = min(baseNote, note.keyid)
                dominantKeysOnBeat.add((note.keyid - KEYID) % 12)
        # create set of notes played on strong and weak part of beat
        allKeysOnBeat = set()
        backUpBaseNote = 100
        for beat1 in range(beat + 1, beat + 4):
            for note in Score[beat1]:
                if note.key != 'r':
                    backUpBaseNote = min(backUpBaseNote, note.keyid)
                    allKeysOnBeat.add((note.keyid - KEYID) % 12)
        # find lowest beat
        if baseNote == 100:
            baseNote = backUpBaseNote
        if baseNote == 100:
            continue
        baseNote = (baseNote - KEYID) % 12

        # Search all chord families for possible matches and add possible chords to
        # The list of chords
        chords = []
        for chordFam in ChordSet.values():
            # The more points, the worse
            points = 0
            if baseNote not in chordFam.base:
                continue
            for note in dominantKeysOnBeat:
                if note in chordFam.base:
                    points -= 100
                else:
                    points += 100

            # TODO later: compare notes on nondominant beats with scale
            heappush(chords, [points, chordFam.getChord(baseNote, KEY)])

        if len(chords) > 0:
            bestScore = chords[0][0]
            i = 0
            while i < len(chords) and chords[i][0] <= bestScore + 50:
                i += 1
            Chords[beat] = [chords[j][1] for j in range(i)]
        else:
            Chords[beat] = ['UNRECOGNIZED NOTE']


def assessFit():
    return 0


def harmonize():
    for beat in range(LENGTH * 4):
        dominantKeysOnBeat = set()
        baseNote = 100
        for note in Score[beat * 4]:
            if note.key != 'r':
                baseNote = min(baseNote, note.keyid)
                dominantKeysOnBeat.add((note.keyid - KEYID) % 12)
        # create set of notes played on strong and weak part of beat
        allKeysOnBeat = set()
        for beat1 in range(beat + 1, beat + 4):
            for note in Score[beat1]:
                if note.key != 'r':
                    backUpBaseNote = min(backUpBaseNote, note.keyid)
                    allKeysOnBeat.add((note.keyid - KEYID) % 12)
        # find lowest beat
        if baseNote == 100:
            baseNote = backUpBaseNote
        if baseNote == 100:
            continue
        baseNote = (baseNote - KEYID) % 12
        for chord in Chords[beat]:



def print_score():
    for i in range(LENGTH):
        for j in range(16):
            stdout.write(str([str(x) for x in Score[i * 16 + j]]))
        stdout.write('\n')


def print_chords():
    for i in range(LENGTH * 4):
        for j in range(len(Chords[i])):
            stdout.write(str(Chords[i][j]) + '\t')
        stdout.write('\n')


def precompile_song():
    output = AudioSegment.silent(duration=16 * BEAT_TIME * LENGTH)
    for channel in range(maxUsedChannels[0]):
        currLine = AudioSegment.empty()
        for t in range(LENGTH * 16):
            if Score[t][channel].fresh:
                currLine = currLine + getSound(Score[t][channel])
        print(len(currLine))
        print(len(output))
        output = output.overlay(currLine)
        print(len(output))
    return output


def compile_song(output):
    play(output)
    output.export("result.wav", format="wav")


if __name__ == '__main__':
    write_sample_song()
    generateChordStructure()
    # print(str(ChordSet))
    # print_score()
    print_chords()

    # song = precompile_song()
    # compile_song(song)
