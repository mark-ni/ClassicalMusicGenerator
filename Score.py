from sys import stdout
from music_structures import *
from heapq import heappush

MELODY_LINE = 0
# TODO: Make sure rest of project matches up with BASS_LINE implementation
BASS_LINE = 1

BASS_LOW = Note.getIdLong('C2')
BASS_HIGH = Note.getIdLong('C4')
TREBLE_LOW = Note.getIdLong('C2')
TREBLE_HIGH = Note.getIdLong('C4')


class Score:

    def __init__(self, LENGTH, KEY, MAX_KEYS=10):
        self.LENGTH = LENGTH

        # Just a safeguard!
        if LENGTH > 32:
            quit()

        self.MAX_KEYS = MAX_KEYS
        self.KEY = KEY
        self.KEY_NOTE_ID_SHORT = Note.getIdShort(KEY[0])
        self.score = [[Note('r', 1, True) for _ in range(MAX_KEYS)] for __ in range(16 * LENGTH)]
        self.chordSet = self.generateChordSet()
        self.chordBank = [list() for _ in range(LENGTH * 4)]

        # TODO: replace the 0 with a null or default chord value
        self.chords = [0 for _ in range(LENGTH * 4)]

        # Records the highest number of used channels at any given point to optimize
        # extraction of wav file at the end
        # Probably not needed lol
        self.maxUsedChannels = 0

    def add_note(self, noteLong, duration, time, measure):
        channel = 0
        while channel < self.MAX_KEYS - 1:
            if self.score[measure * 16 + time][channel].noteLong == 'r':
                break
            channel += 1
        self.maxUsedChannels = max(self.maxUsedChannels, channel + 1)
        for timeLeft in range(duration, 0, -1):
            self.score[measure * 16 + time + duration - timeLeft][channel] = Note(noteLong, timeLeft)
        self.score[measure * 16 + time][channel].fresh = True

    def assessFitChord(self, chordFam, noteShortsStrong):
        """Returns a score for how well a chord family would fit to describe
        the set of notes on a certain beat

        Specific Implementation Used:
        - The lower the point score, the better the fit
        - Subtract from points for every note in the chord family that matches
        what is being played."""
        points = 0
        for noteShort in noteShortsStrong:
            if noteShort in chordFam.base:
                points -= 200
        return points

    def assessFitBassNote(self, beat, chord, noteIdLong):
        """Returns a score for how good a given bass note is given the beat and chord

        Specific Implementation Used:
        - 1. No intervals greater than a fifth. Only accept intervals of 2,3, P4, and P5
        - 2. No parallel fifths
        - 3. Points for contrary motion
        - 4. Preference given to less motion but also vary conjunct/disjunct motion
            - The higher the number of the last x disjunct movements, the worse the
            score awarded for disjunct motion
                - Can apply this concept later to add 8th notes and stuff
        - 5. Give points for cadences in the right place
            - Cadences considered:
        """
        # 1

        # 2

        # 3

        # 4

        # 5

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
            chordNoteShort = Note.getNoteShort((self.KEY_NOTE_ID_SHORT + intervals[i - 1]) % 12)
            chordQuality = intervalKeys[i - 1]
            chordSet[dict_keys[i]] = ChordFamily(chordNoteShort, chordQuality, self.KEY)

        # Implement V7s later: right now just hardcode V7/V
        # TODO: REPLACE THIS HARDCODED THING WITH ACTUAL DICT KEY IMPLEMENTATION
        chordSet['V7/V'] = ChordFamily('D', 'SEVENTH', self.KEY)
        chordSet['V7/ii'] = ChordFamily('A', 'SEVENTH', self.KEY)
        chordSet['V7/IV'] = ChordFamily('C', 'SEVENTH', self.KEY)
        chordSet['V7/vi'] = ChordFamily('E', 'SEVENTH', self.KEY)
        chordSet['V7/iii'] = ChordFamily('B', 'SEVENTH', self.KEY)
        chordSet['V7'] = ChordFamily('G', 'SEVENTH', self.KEY)
        return chordSet

    def generateChordBank(self):
        for beat in range(self.LENGTH * 4):

            strongNotes = self.getStrongNotes(beat)

            if len(strongNotes) > 0:
                baseNoteIdShort = (min(strongNotes).noteIdShort - self.KEY_NOTE_ID_SHORT) % 12
            else:
                continue

            strongNoteShorts = set([(note.noteIdShort - self.KEY_NOTE_ID_SHORT) % 12 for note in strongNotes])

            # Search all chord families for possible matches and add possible chords to
            # The list of chords
            chords = []
            for chordFam in self.chordSet.values():
                # The more points, the worse
                if baseNoteIdShort not in chordFam.base:
                    continue
                points = self.assessFitChord(chordFam, strongNoteShorts)

                # TODO later: compare notes on non-dominant beats with scale
                heappush(chords, [points, chordFam.getChord(baseNoteIdShort)])

            if len(chords) > 0:
                bestScore = chords[0][0]
                i = 0
                while i < len(chords) and chords[i][0] <= bestScore + 50:
                    i += 1
                self.chordBank[beat] = [chords[j][1] for j in range(i)]
            else:
                print("UNRECOGNIZED NOTE")
                quit()

    # Reserved for future implementation of checking notes on all parts of the beat
    #
    # def getAllNoteLongs(self, beat):
    #     allNotes = self.getStrongNotes(beat)
    #     for beat1 in range(beat + 1, beat + 4):
    #         for note in self.score[beat1]:
    #             if note.noteLong != 'r':
    #                 allNotes.add(note)
    #     return allNotes

    def getPossibleBassNotes(self, noteIdShort, beat):
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
            return {noteIdShort + Note.getIdLong('A2')}

        prevBassNote = self.score[beat - 1][BASS_LINE]
        if prevBassNote.noteIdShort == noteIdShort:
            return {prevBassNote.noteIdLong}
        elif noteIdShort < prevBassNote.noteIdShort:
            lower = prevBassNote.noteIdLong - (prevBassNote.noteIdShort - noteIdShort)
            higher = prevBassNote.noteIdLong + ((noteIdShort - prevBassNote.noteIdShort) % 12)
        else:
            lower = prevBassNote.noteIdLong - ((prevBassNote.noteIdShort - noteIdShort) % 12)
            higher = prevBassNote.noteIdLong + (noteIdShort - prevBassNote.noteIdShort)

        returnSet = set()
        if BASS_LOW <= lower <= BASS_HIGH:
            returnSet.add(lower)
        if BASS_LOW <= higher <= BASS_HIGH:
            returnSet.add(higher)
        return returnSet

    def getStrongNotes(self, beat):
        strongNotes = set()
        for note in self.score[beat * 4]:
            if note.noteLong != 'r':
                strongNotes.add(note)
        return strongNotes

    def harmonize(self):
        self.generateChordBank()
        self.harmonizeBass()

    def harmonizeBass(self):
        """Adds a bass line to accompany a single note melody"""
        for beat in range(self.LENGTH * 4):

            # create set of notes played on strong part of beat -- always of size 1 for now
            strongNotes = self.getStrongNotes(beat)

            # If nothing was played here, don't harmonize this beat.
            if len(strongNotes) == 0:
                continue

            # Find the best possible chord / note / interval match
            # for the current beat
            bestChord = None
            bestNoteIdLong = 0
            mostPoints = 0

            soprano = strongNotes.pop()
            if len(strongNotes) == 0:
                for chord in self.chordBank[beat]:
                    for noteIdShort in chord.notes:
                        for noteIdLong in self.getPossibleBassNotes(noteIdShort, beat):
                            points = self.assessFitBassNote(beat, chord, noteIdLong)
                            if points >= mostPoints:
                                mostPoints = points
                                bestNoteIdLong = noteIdLong
                                bestChord = chord
            else:
                print("No implementation for double notes in melodies yet!!")
                quit()

            bestNoteLong = Note.getNoteLong(bestNoteIdLong)
            self.add_note(bestNoteLong, 4, 4 * (beat % 4), beat // 4)
            self.chords[beat] = bestChord

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
