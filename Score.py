from sys import stdout
from music_structures import *
from heapq import heappush
from collections import defaultdict

MELODY_LINE = 0
# TODO: Make sure rest of project matches up with BASS_LINE implementation
BASS_LINE = 1

BASS_LOW = Note.getIdLong('C2')
BASS_HIGH = Note.getIdLong('C4')
TREBLE_LOW = Note.getIdLong('C4')
TREBLE_HIGH = Note.getIdLong('C6')

# Interval constants
P8, m2, M2, m3, M3, P4, TRITONE, P5, m6, M6, m7, M7 = map(int, range(12))

# Hardcoded valid major chord progressions (key = previous chord, value = set of current chords)
# TODO: CREATE THE SET OF VIABLE PROGRESSIONS - IGNORE INVERSIONS FOR NOW
MAJOR_PROGRESSIONS = defaultdict()
MP = MAJOR_PROGRESSIONS
MP['I'] = ['I', 'I6', 'I6-4', 'IV', 'V', 'V6', 'V6-4', 'vii°6', 'V6-5', 'V4-3', 'V4-3/V']
MP['I6'] = ['I', 'ii6', 'V', 'V6-4', 'vii°6', 'V4-3']
MP['I6-4'] = ['I', 'I6-4', 'IV6', 'V']
MP['ii'] = ['V6', 'vii°6', 'V4-3/V']
MP['ii6'] = ['V', 'V6', 'vii°6', 'V7/V']
MP['IV'] = ['I6', 'I6-4', 'V', 'V6', 'V6-4', 'vii°6', 'V7/V']
MP['IV6'] = ['I6-4', 'V6']
MP['IV6-4'] = ['I', 'vi6', 'V6', 'vii°6']
MP['V'] = ['I', 'I6', 'V6-4']
MP['V6'] = ['I', 'vii6']
MP['V6-4'] = ['I', 'I6', 'vi6', 'V7']
MP['vi6'] = ['I', 'ii', 'IV6-4']
MP['vii°6'] = ['I', 'I6', 'I6-4', 'V6-4', 'vi', 'V7']
MP['V7'] = ['I', 'I6-4']
MP['V6-5'] = ['I', 'vii°6']
MP['V4-3'] = ['I', 'I6']
MP['V4-3/V'] = ['V']
MP['V7/V'] = ['V6']


# for i in range(3):
#    MAJOR_PROGRESSIONS[Chord.getHash(1, i)] = {Chord.getHash()}

class Score:

    def __init__(self, LENGTH, KEY, MAX_KEYS=10):
        self.LENGTH = LENGTH

        # Just a safeguard!
        if LENGTH > 32:
            print("The song is too long!")
            quit()

        self.MAX_KEYS = MAX_KEYS
        self.KEY = KEY
        self.KEY_NOTE_ID_SHORT = Note.getIdShort(KEY[0])
        self.score = [[Note('r', 1, True) for _ in range(MAX_KEYS)] for __ in range(16 * LENGTH)]
        self.chordSet = self.generateChordSet()
        self.chordBank = [list() for _ in range(LENGTH * 4)]

        # TODO: replace the 0 with a null or default chord value
        self.chords = [Chord(KEY[1], 1, [0, 4, 7], KEY) for _ in range(LENGTH * 4)]

        # Records the highest number of used channels at any given point to optimize
        # extraction of wav file at the end
        # Probably not needed lol
        self.maxUsedChannels = 0

        self.bassDisjunctMotion = 0

        print("Finished construction of Score")

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
            if (noteShort - self.KEY_NOTE_ID_SHORT) % 12 in chordFam.baseRelNotes:
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
        - 5. Award points for good transitions of chords (such as V-I on the last measure),
            deduct points for bad ones (such as vii-iii).
        - 6. Make sure the piece ends with a V or a I
        - 7. Try to avoid using 7ths if possible
        - 8. Treble and Bass never cross
        """
        chord.setBaseNote(noteIdLong % 12)

        points = 500
        # Handle special case: beat = 0
        # Must be tonic / 0th inv
        # If treble note is not in tonic, then subdominant/dominant 0th inv
        if beat == 0:
            if chord.inversion == 0 and not chord.seventh:
                if chord.rel == 1:
                    return 1000
                elif chord.rel == 5:
                    return 200
                elif chord.rel == 4:
                    return 200
            return 0

        # Rule 1: NO PARALLEL INTERVALS
        lastTrebleNote = self.score[beat * 4 - 1][MELODY_LINE].noteIdLong
        lastBassNote = self.score[beat * 4 - 1][BASS_LINE].noteIdLong
        currTrebleNote = self.score[beat * 4][MELODY_LINE].noteIdLong

        if lastTrebleNote != 100 and currTrebleNote != 100:
            if lastTrebleNote - lastBassNote == currTrebleNote - noteIdLong:
                if (lastTrebleNote - lastBassNote) % 12 in (P8, P5, TRITONE):
                    if lastTrebleNote != currTrebleNote:
                        return 0

        # Rule 2: NO BASS INTERVALS > a 5th
        if abs(noteIdLong - lastBassNote) > P5 or abs(noteIdLong - lastBassNote) == TRITONE:
            return 0
        # Rule 3: Contrary motion is good!
        if lastTrebleNote < currTrebleNote and noteIdLong < lastBassNote \
                or lastTrebleNote > currTrebleNote and noteIdLong > lastBassNote:
            if abs(lastTrebleNote - currTrebleNote <= 4):
                points += 40
        elif lastTrebleNote == currTrebleNote and lastBassNote == noteIdLong:
            points += 200

        # Rule 4: Promote disjunct motion!
        # Idea is self.bassDisjunctMotion stores an integer value: the higher it is,
        # the more disjunct motion there has been recently. This score will be inversely
        # proportional to how much we want disjunct motion.
        if abs(noteIdLong - lastBassNote) >= 3:
            points += (-10) * (self.bassDisjunctMotion + (abs(noteIdLong - lastBassNote)))
        elif abs(noteIdLong - lastBassNote) in (1, 2):
            points += 10 * (self.bassDisjunctMotion - 2)
        else:
            points -= 50

        # Rule 5: Give a lot of points for good chord progression!
        lastChord = self.chords[beat - 1]
        if str(chord) in MAJOR_PROGRESSIONS.get(str(lastChord), {}):
            points += 500
        elif str(chord) == str(lastChord):
            if lastTrebleNote == currTrebleNote and lastBassNote == noteIdLong:
                points += 500

        # Subrule for 5: Don't use bad chords!
        if chord.rel == 3 or (chord.rel == 2 and chord.inversion == 2) or (chord.rel == 7 and chord.inversion != 1) \
                or (chord.rel == 6 and chord.inversion != 1):
            points -= 500

        # Rule 6: End on a good cadence!
        currTrebleDuration = self.score[beat * 4][MELODY_LINE].duration
        # print(currTrebleDuration)
        timeLeft = (self.LENGTH * 4 - beat)
        if currTrebleDuration >= timeLeft:
            if chord.rel == 1 and chord.inversion == 0:
                points += 2000
            elif chord.rel == 5 and self.chords[beat - 1].rel == 1:
                points += 1000

        # Sub rule for 6: don't use certain chords in the last 2 measures to
        # simplify the progressions available
        else:
            if beat >= self.LENGTH * 4 - 6:
                if "I" in MP.get(str(chord), {}) and str(chord) not in ("I", "I6"):
                    points += 500

        # Rule 7: Treble and Bass should never cross
        if currTrebleNote <= noteIdLong:
            return 0

        # Rule 8: Discourage use of 6/4s
        if chord.inversion == 2 and not chord.seventh:
            if chord.rel not in (1, 5):
                points -= 100

        # Rule 9: Discourage doubling of notes
        # Also, chords consisting of one note are always in the key of that note,
        # not some inversion of some other chord
        if currTrebleNote % 12 == noteIdLong % 12:
            if chord.inversion != 0:
                return 0
            points -= 50

        # Rule 10: Discourage notes that are too high or too low
        # Note: This rule would be unnecessary in a non-greedy algorithm
        if noteIdLong < Note.getIdLong('G2'):
            points -= 20 * (Note.getIdLong('F#2') - noteIdLong + 1)
        elif noteIdLong > Note.getIdLong('F#3'):
            points -= 20 * (noteIdLong - Note.getIdLong('F#3') + 1)

        # Rule -1: Halve points for 7th notes because it's way easier to satisfy reqs and we want to avoid them
        if len(chord.relNotes) == 4:
            points //= 2

        return points

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
        # chordSet['V7/ii'] = ChordFamily('A', 'SEVENTH', self.KEY)
        # chordSet['V7/IV'] = ChordFamily('C', 'SEVENTH', self.KEY)
        # chordSet['V7/vi'] = ChordFamily('E', 'SEVENTH', self.KEY)
        # chordSet['V7/iii'] = ChordFamily('B', 'SEVENTH', self.KEY)
        chordSet['V7'] = ChordFamily('G', 'SEVENTH', self.KEY)
        return chordSet

    def generateChordBank(self):
        for beat in range(self.LENGTH * 4):

            strongNotes = self.getStrongNotes(beat)

            if len(strongNotes) > 0:
                baseNoteIdShort = min(strongNotes).noteIdShort
            else:
                continue

            strongNoteShorts = set([note.noteIdShort for note in strongNotes])

            # Search all chord families for possible matches and add possible chords to
            # The list of chords
            chords = []
            for chordFam in self.chordSet.values():
                # The more points, the worse
                if (baseNoteIdShort - self.KEY_NOTE_ID_SHORT) % 12 not in chordFam.baseRelNotes:
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
        print("Finished chord bank generation")

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
        self.print_score_chordBank()
        print()
        self.harmonizeBass()
        print()
        self.mergeBass()
        self.print_bass_line()

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
                    for relNoteIdShort in chord.relNotes:
                        noteIdShort = (relNoteIdShort + self.KEY_NOTE_ID_SHORT) % 12
                        for noteIdLong in self.getPossibleBassNotes(noteIdShort, beat):
                            points = self.assessFitBassNote(beat, chord, noteIdLong)
                            print("Points: ", points, Note.getNoteLong(noteIdLong), chord)
                            if points > mostPoints:
                                mostPoints = points
                                bestNoteIdLong = noteIdLong
                                bestChord = chord
            else:
                print("No implementation for double notes in melodies yet!!")
                quit()

            bestChord.setBaseNote(bestNoteIdLong % 12)
            bestNoteLong = Note.getNoteLong(bestNoteIdLong)

            # Calculate new value for disjunct motion
            if beat > 0:
                lastBassNoteIdLong = self.score[beat * 4 - 1][BASS_LINE].noteIdLong
                if abs(bestNoteIdLong - lastBassNoteIdLong) >= 3:
                    self.bassDisjunctMotion += abs(bestNoteIdLong - lastBassNoteIdLong)
                elif abs(bestNoteIdLong - lastBassNoteIdLong) in (1, 2):
                    self.bassDisjunctMotion -= 1

            self.add_note(bestNoteLong, 4, 4 * (beat % 4), beat // 4)
            self.chords[beat] = bestChord
            print(beat, mostPoints, bestNoteIdLong, bestChord, self.bassDisjunctMotion)
            print('\n')

    def mergeBass(self):
        ind = self.LENGTH * 16 - 2
        while ind >= 0:
            if self.score[ind][BASS_LINE].noteIdLong == self.score[ind + 1][BASS_LINE].noteIdLong:
                self.score[ind][BASS_LINE].duration = self.score[ind + 1][BASS_LINE].duration + 1
                self.score[ind + 1][BASS_LINE].fresh = False
            ind -= 1

    def print_score(self):
        for i in range(self.LENGTH):
            for j in range(4):
                stdout.write(str([str(x) for x in self.score[i * 16 + j * 4]]))
            stdout.write('\n')

    def print_score_chords(self):
        for i in range(self.LENGTH):
            stdout.write(str(i * 4) + ":\t")
            for j in range(4):
                stdout.write(str(self.chords[i * 4 + j]) + '\t')
            stdout.write('\n')

    def print_score_chordBank(self):
        for i in range(self.LENGTH * 4):
            stdout.write(str(i) + ":\t")
            for j in range(len(self.chordBank[i])):
                stdout.write(str(self.chordBank[i][j]) + '\t')
            stdout.write('\n')

    def print_bass_line(self):
        for i in range(self.LENGTH):
            stdout.write(str(self.score[i * 16][BASS_LINE]) + "\t")
            stdout.write(str(self.score[i * 16][BASS_LINE].duration) + "\t")
            stdout.write(str(self.score[i * 16 + 4][BASS_LINE]) + "\t")
            stdout.write(str(self.score[i * 16 + 4][BASS_LINE].duration) + "\t")
            stdout.write(str(self.score[i * 16 + 8][BASS_LINE]) + "\t")
            stdout.write(str(self.score[i * 16 + 8][BASS_LINE].duration) + "\t")
            stdout.write(str(self.score[i * 16 + 12][BASS_LINE]) + "\t")
            stdout.write(str(self.score[i * 16 + 12][BASS_LINE].duration) + "\t")
            print()


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
        print("Finished writing of sample")
