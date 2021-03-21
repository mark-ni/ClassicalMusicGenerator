class Note:
    idShortByNote = {'A': 0, 'A#': 1, 'B': 2, 'C': 3, 'C#': 4, 'D': 5, 'D#': 6,
                     'E': 7, 'F': 8, 'F#': 9, 'G': 10, 'G#': 11}

    noteShortById = {0: 'A', 1: 'A#', 2: 'B', 3: 'C', 4: 'C#', 5: 'D', 6: 'D#',
                     7: 'E', 8: 'F', 9: 'F#', 10: 'G', 11: 'G#'}

    def __init__(self, noteLong, duration, fresh=False):
        """Note(str type, int duration) -> Note
        type: String (such as "E2") denoting tone and octave
        duration: measured in number of 16 beats

        A note like A2 would have the following values:
        - noteIDLong: 12
        - noteIDShort: 0
        - noteShort: 'A'
        - noteLong: 'A2'
        """
        self.noteLong = noteLong

        if noteLong != 'r':
            self.noteIdLong = self.getIdLong(self.noteLong)
            self.noteShort = noteLong[:-1]
            self.noteIdShort = self.getIdShort(self.noteShort)
        else:
            self.noteShort = 'r'
            self.noteIDLong = 100
            self.noteIDShort = 'this is a rest'

        self.duration = duration
        self.fresh = fresh

    def __str__(self):
        return self.noteLong  # + ',' + str(self.duration)

    def __gt__(self, other):
        return self.noteIdLong > other.noteIdLong

    def __lt__(self, other):
        return self.noteIdLong < other.noteIdLong

    @staticmethod
    def getIdLong(noteLong):
        if noteLong == 'r':
            return 100
        is_a_b = int(noteLong[0] not in ['A', 'B'])
        return Note.getIdShort(noteLong[:-1]) + 12 * (int(noteLong[-1]) - is_a_b)

    @staticmethod
    def getIdShort(noteShort):
        return Note.idShortByNote[noteShort]

    @staticmethod
    def getNoteLong(noteIdLong):
        if noteIdLong == 100:
            return 'r'
        return Note.noteShortById[noteIdLong % 12] + str((noteIdLong + 9) // 12)

    @staticmethod
    def getNoteShort(noteIdShort):
        return Note.noteShortById[noteIdShort]


class Chord:

    roman = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v', 6: 'vi', 7: 'vii'}
    inversion5 = {0: '', 1: '6', 2: '6-4'}
    inversion7 = {0: '7', 1: '6-5', 2: '4-3', 3: '4-2'}

    def __init__(self, quality, rel, inversion, notes, key):
        self.quality = quality
        self.rel = rel
        self.inversion = inversion
        self.notes = notes
        self.key = key

        self.seventh = False
        if len(notes) == 4:
            self.seventh = True

        self.child = 'i'
        self.setChild()

    def __str__(self):
        return self.getChordString(self.rel, self.quality, self.inversion, self.seventh)

    # Used for selecting the best classification of chords for a given beat -- we need to compare between
    # chords with equal point values at some point
    #
    # Specific implementation:
    # In general, 3-note chords are more flexible and viable than 4-note chords so they are preferred
    def __lt__(self, other):
        return len(self.notes) < len(other.notes)

    def setChild(self):
        if self.quality in ['MAJOR', 'MAJOR_SEVENTH', 'SEVENTH', 'AUGMENTED']:
            self.child = self.child.upper()
        if not self.seventh:
            return
        childRel = (self.rel - 5) % 7 + 1
        baseQuality = self.key[1]
        intervalQualities = ChordFamily.getIntervalQualities(baseQuality)
        childQuality = intervalQualities[childRel - 1]
        self.child = self.getChordString(childRel, childQuality)

    def getChordString(self, rel, quality, inversion=-1, seventh=False):
        string = Chord.roman[rel]
        if seventh:
            string = 'v'

        # Account for Key
        if quality.upper() in ['MAJOR', 'MAJOR_SEVENTH', 'SEVENTH']:
            string = string.upper()
        elif quality.upper() == 'AUGMENTED':
            string = string.upper()
            string += '⁺'
        elif quality.upper() in ['DIMINISHED', 'DIMINISHED_SEVENTH']:
            string += '°'

        # Add inversion
        if seventh and inversion != -1:
            string += Chord.inversion7[inversion]
        elif not seventh and inversion != -1:
            string += Chord.inversion5[inversion]

        # Always use relative dominant 7
        if self.child.upper() != 'I':
            string += '/' + self.child

        return string


class ChordFamily:
    def __init__(self, noteShort, quality, key):
        self.noteShort = noteShort
        self.quality = quality
        self.key = key
        self.base = self.setBaseChordVals()

    def setBaseChordVals(self):
        if self.quality == 'MAJOR':
            li = [0, 4, 7]
        elif self.quality == 'MINOR':
            li = [0, 3, 7]
        elif self.quality == 'DIMINISHED':
            li = [0, 3, 6]
        elif self.quality == 'AUGMENTED':
            li = [0, 4, 8]
        elif self.quality == 'DIMINISHED_SEVENTH':
            li = [0, 3, 6, 9]
        elif self.quality == 'MINOR_SEVENTH':
            li = [0, 3, 7, 10]
        elif self.quality == 'SEVENTH':
            li = [0, 4, 7, 10]
        elif self.quality == 'MAJOR_SEVENTH':
            li = [0, 4, 7, 11]
        else:
            print("Key: ", str(self.key), "quality: ", self.quality)
            print("CHORD SET NOT FOUND")
            return -1
        gap = (Note.getIdShort(self.noteShort) - Note.getIdShort(self.key[0])) % 12

        for i in range(len(li)):
            li[i] = (li[i] + gap) % 12
        return li

    def getChord(self, baseNoteIdShort):
        inversion = 0
        while inversion < len(self.base) and baseNoteIdShort != self.base[inversion]:
            inversion += 1

        if inversion == len(self.base):
            print("ERROR WITH CHORD FAMILY", self.noteShort, self.quality, self.key[0])
            quit()

        rel = (ord(self.noteShort) - ord(self.key[0])) % 7 + 1
        return Chord(self.quality, rel, inversion, self.base, self.key)

    @staticmethod
    def getIntervals(quality):
        if quality == 'MAJOR':
            return [0, 2, 4, 5, 7, 9, 11]
        elif quality == 'MINOR':
            return [0, 2, 3, 5, 7, 8, 10]
        else:
            print(quality, "ChordFamily.getIntervals(quality)")
            quit()

    @staticmethod
    def getIntervalQualities(quality):
        if quality == 'MAJOR':
            return ['MAJOR', 'MINOR', 'MINOR', 'MAJOR', 'MAJOR', 'MINOR', 'DIMINISHED']
        elif quality == 'MINOR':
            return ['MINOR', 'DIMINISHED', 'AUGMENTED', 'MINOR', 'MAJOR', 'MAJOR', 'DIMINISHED']
        else:
            print(quality, "ChordFamily.getIntervals(quality)")
            quit()
