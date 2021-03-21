from sys import stdout
from music_structures import *
from heapq import heappush

MELODY_LINE = 0
# TODO: Make sure rest of project matches up with BASS_LINE implementation
# TODO: Manually run through all code to differentiate between where notes are relative to C and not relative
BASS_LINE = 1


class Score:

    def __init__(self, LENGTH, KEY, MAX_KEYS=10):
        self.LENGTH = LENGTH

        # Just a safeguard!
        if LENGTH > 32:
            quit()

        self.MAX_KEYS = MAX_KEYS
        self.KEY = KEY
        self.KEYID = Note.getValueByKey(KEY[0])
        self.score = [[Note('r', 1, True) for _ in range(MAX_KEYS)] for __ in range(16 * LENGTH)]
        self.chordSet = self.generateChordSet()
        self.chordBank = [list() for _ in range(LENGTH * 4)]
        self.chords = [0 for _ in range(LENGTH * 4)]

        # Records the highest number of used channels at any given point to optimize
        # extraction of wav file at the end
        self.maxUsedChannels = 0

    def add_note(self, key, duration, time, measure):
        channel = 0
        while channel < self.MAX_KEYS - 1:
            if self.score[measure * 16 + time][channel].key == 'r':
                break
            channel += 1
        self.maxUsedChannels = max(self.maxUsedChannels, channel + 1)
        for timeLeft in range(duration, 0, -1):
            self.score[measure * 16 + time + duration - timeLeft][channel] = Note(key, timeLeft)
        self.score[measure * 16 + time][channel].fresh = True

    def assessFitChord(self, chordFam, strongKeysOnBeat):
        points = 0
        for note in strongKeysOnBeat:
            if note in chordFam.base:
                points -= 100
            else:
                points += 100
        return points

    def assessFitNote(self, beat, chord, note):
        """Returns a score for how good a given beat, chord, and note"""
        return 0

    def generateChordSet(self):
        """Gives the set of usable chords based on the quality of the piece (Major / minor).
        Could definitely implement pre-generation later."""
        quality = self.KEY[1]
        chordSet = {}
        intervals = ChordFamily.getIntervals(quality)
        intervalKeys = ChordFamily.getIntervalQualities(quality)

        # TODO: REPLACE THIS HARDCODED THING WITH ACTUAL DICT KEY IMPLEMENTATION
        dict_keys = {1: 'I', 2: 'ii', 3: 'iii', 4: 'IV', 5: 'V', 6: 'vi', 7: 'vii°'}
        if quality == 'MINOR':
            dict_keys = {1: 'i', 2: 'ii°', 3: 'III⁺', 4: 'iv', 5: 'V', 6: 'VI', 7: 'vii°'}

        for i in range(1, 8):
            chordKeyNoOct = Note.getKeyByValue((self.KEYID + intervals[i - 1]) % 12)
            chordQuality = intervalKeys[i - 1]
            # rel = (ord(chordKeyNoOct[0]) - ord(self.KEY[0][0])) % 7 + 1
            chordSet[dict_keys[i]] = ChordFamily(chordKeyNoOct, chordQuality, self.KEY[0])

        # Implement V7s later: right now just hardcode V7/V
        # TODO: REPLACE THIS HARDCODED THING WITH ACTUAL DICT KEY IMPLEMENTATION
        chordSet['V7/V'] = ChordFamily('D', 'SEVENTH', self.KEY[0])
        chordSet['V7/ii'] = ChordFamily('A', 'SEVENTH', self.KEY[0])
        chordSet['V7/IV'] = ChordFamily('C', 'SEVENTH', self.KEY[0])
        chordSet['V7/vi'] = ChordFamily('E', 'SEVENTH', self.KEY[0])
        chordSet['V7/iii'] = ChordFamily('B', 'SEVENTH', self.KEY[0])
        chordSet['V7'] = ChordFamily('G', 'SEVENTH', self.KEY[0])
        return chordSet

    def generateChordBank(self):
        for beat in range(self.LENGTH * 4):
            strongKeysOnBeat = self.getStrongKeysOnBeat(beat)
            # allKeysOnBeat = self.getAllKeysOnBeat(beat)
            if len(strongKeysOnBeat) > 0:
                baseNote = (min(strongKeysOnBeat) - self.KEYID) % 12
            else:
                continue
            strongKeysOnBeat = set([(i - self.KEYID) % 12 for i in strongKeysOnBeat])

            # Search all chord families for possible matches and add possible chords to
            # The list of chords
            chords = []
            for chordFam in self.chordSet.values():
                # The more points, the worse
                if baseNote not in chordFam.base:
                    continue
                points = self.assessFitChord(chordFam, strongKeysOnBeat)

                # TODO later: compare notes on non-dominant beats with scale
                heappush(chords, [points, chordFam.getChord(baseNote, self.KEY)])

            if len(chords) > 0:
                bestScore = chords[0][0]
                i = 0
                while i < len(chords) and chords[i][0] <= bestScore + 50:
                    i += 1
                self.chordBank[beat] = [chords[j][1] for j in range(i)]
            else:
                print("UNRECOGNIZED NOTE")
                quit()

    def getAllKeysOnBeat(self, beat):
        allKeysOnBeat = self.getStrongKeysOnBeat(beat)
        for beat1 in range(beat + 1, beat + 4):
            for note in self.score[beat1]:
                if note.key != 'r':
                    allKeysOnBeat.add(note.keyid)
        return allKeysOnBeat

    def getPossibleBassNotes(self, noteIDNoOct, beat):
        """Given an octaveless note, returns a set of the possible nonoctaveless
        notes that could be reasonably played on a given beat for the bass line

        NoteIDNoOct = int (0: 'A', 1: 'A#', 3:'C'...)
        beat = int (15: Measure 4 beat 4, 1: Measure 1 beat 2)

        Returns a keyid (0:A0, 2: B0,...)

        Specific Implementation Used:
        - If it's the first beat of the song, choose the note between A2 and G3
        (based on finding the line in the bass clef closest to the middle)
        - Else if the (n-1)th beat has the same note as the nth beat, play the note
        again.
        - Else: Return a set of two notes, one less than an octave lower than the
         (n-1)th beat, and one less than an octave higher than the (n-1)th beat"""
        if beat == 0:
            return {noteIDNoOct + Note.findKeyID('A2')}

        # TODO: CHECK KEYIDS AND STUFF!!
        prevBassNote = self.score[beat - 1][BASS_LINE].keyid
        if prevBassNote % 12 == noteIDNoOct:
            return {prevBassNote}
        elif noteIDNoOct < prevBassNote % 12:
            lower = prevBassNote - ((prevBassNote % 12) - noteIDNoOct)
            higher = prevBassNote + ((noteIDNoOct - (prevBassNote % 12)) % 12)
        else:
            lower = prevBassNote - (((prevBassNote % 12) - noteIDNoOct) % 12)
            higher = prevBassNote + (noteIDNoOct - (prevBassNote % 12))
        return {lower, higher}

    def getStrongKeysOnBeat(self, beat):
        strongKeysOnBeat = set()
        for note in self.score[beat * 4]:
            if note.key != 'r':
                strongKeysOnBeat.add(note.keyid)
        return strongKeysOnBeat

    def harmonize(self):
        self.generateChordBank()
        self.harmonizeBass()

    def harmonizeBass(self):
        """Adds a bass line to accompany a single note melody"""
        for beat in range(self.LENGTH * 4):

            # create set of notes played on strong part of beat -- always of size 1 for now
            strongKeysOnBeat = self.getStrongKeysOnBeat(beat)
            # If nothing was played here, don't harmonize this beat.
            if len(strongKeysOnBeat) == 100:
                continue

            # Find the best possible chord / note / interval match
            # for the current beat
            bestFitChord = None
            bestFitNote = None
            mostPoints = 0

            for chord in self.chordBank[beat]:
                for noteIDNoOct in chord.notes:
                    soprano = strongKeysOnBeat.pop()
                    if len(strongKeysOnBeat) == 0 and (soprano - self.KEYID) % 12 != noteIDNoOct:
                        for note in self.getPossibleBassNotes(noteIDNoOct, beat):
                            points = self.assessFitNote(beat, chord, note)
                            if points >= mostPoints:
                                mostPoints = points
                                bestFitNote = note
                                bestFitChord = chord
                    elif len(strongKeysOnBeat) != 0:
                        print("No implementation for double notes in melodies yet!!")
                        quit()
                    else:
                        continue

            self.add_note(bestFitNote, 4, 4 * (beat % 4), beat // 4)
            self.chords[beat] = bestFitChord

    def print_score(self):
        for i in range(self.LENGTH):
            for j in range(16):
                stdout.write(str([str(x) for x in self.score[i * 16 + j]]))
            stdout.write('\n')

    def print_score_chords(self):
        for i in range(self.LENGTH):
            for j in range(4):
                stdout.write(str(self.chords[i * 4 + j]) + '\t')
            stdout.write('\n')

    def print_score_chordBank(self):
        for i in range(self.LENGTH * 4):
            for j in range(len(self.chordBank[i])):
                stdout.write(str(self.chordBank[i][j]) + '\t')
            stdout.write('\n')

    def write_sample(self, voices=1):
        song = [['G4', 4, 0, 0], ['E4', 4, 4, 0], ['D4', 6, 8, 0], ['E4', 2, 14, 0],
                ['F4', 4, 0, 1], ['D4', 4, 4, 1], ['C4', 8, 8, 1],
                ['A4', 4, 0, 2], ['G4', 4, 4, 2], ['C5', 4, 8, 2], ['C5', 2, 12, 2], ['B4', 2, 14, 2],
                ['A4', 4, 0, 3], ['F#4', 4, 4, 3], ['G4', 8, 8, 3],
                ['A4', 4, 0, 4], ['F4', 4, 4, 4], ['D4', 4, 8, 4], ['E4', 2, 12, 4], ['F4', 2, 14, 4],
                ['G4', 4, 0, 5], ['E4', 2, 4, 5], ['D4', 2, 6, 5], ['C4', 4, 8, 5], ['C5', 2, 12, 5],
                ['B4', 2, 14, 5],
                ['A4', 4, 0, 6], ['F4', 4, 4, 6], ['E4', 2, 8, 6], ['D4', 2, 10, 6], ['C4', 2, 12, 6],
                ['B3', 2, 14, 6],
                ['C4', 16, 0, 7]]
        for note in song:
            self.add_note(note[0], note[1], note[2], note[3])
        if voices == 2:
            for i in range(self.LENGTH):
                self.add_note('C4', 4, 0, i)
                self.add_note('B3', 4, 4, i)
                self.add_note('A3', 4, 8, i)
                self.add_note('G3', 4, 12, i)
