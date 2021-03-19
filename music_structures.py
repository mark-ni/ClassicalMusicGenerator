class Note:
    def __init__(self, key, duration, fresh=False):
        """Note(str type, int duration) -> Note
        type: String (such as "E2") denoting tone and octave
        duration: measured in number of 16 beats"""
        self.key = key
        # print("Note: self.findKeyID(",key,")")
        self.keyid = self.findKeyID(key)
        self.duration = duration
        self.fresh = fresh

    def __str__(self):
        return self.key  # + ',' + str(self.duration)

    def __gt__(self, other):
        return self.keyid > other.keyid

    def findKeyID(self, key):
        if key == 'r':
            return 100
        is_a_b = int(key[0] not in ['A', 'B'])
        return Note.getValueByKey(key[:-1]) + 12 * (int(key[-1]) - is_a_b)

    @staticmethod
    def getValueByKey(octaveLessKey):
        keyValues = {'A': 0, 'A#': 1, 'B': 2, 'C': 3, 'C#': 4, 'D': 5, 'D#': 6,
                     'E': 7, 'F': 8, 'F#': 9, 'G': 10, 'G#': 11}
        return keyValues[octaveLessKey]

    @staticmethod
    def getKeyByValue(num):
        valueKeys = {0: 'A', 1: 'A#', 2: 'B', 3: 'C', 4: 'C#', 5: 'D', 6: 'D#',
                     7: 'E', 8: 'F', 9: 'F#', 10: 'G', 11: 'G#'}
        return valueKeys[num]


class Chord:
    def __init__(self, quality, rel, inversion, notes, masterKey):
        self.quality = quality
        self.rel = rel
        self.inversion = inversion
        self.notes = notes
        self.masterKey = masterKey

        self.seventh = False
        if len(notes) == 4:
            self.seventh = True

        self.child = 'i'
        self.setChild()

    def __gt__(self, other):
        return len(self.notes) < len(other.notes)

    def __str__(self):
        return self.getChordString(self.rel, self.quality, self.inversion, self.seventh)

    def setChild(self):
        if self.quality in ['MAJOR', 'MAJOR_SEVENTH', 'SEVENTH', 'AUGMENTED']:
            self.child = self.child.upper()
        if not self.seventh:
            return
        childRel = (self.rel - 1 - 4) % 7 + 1
        baseQuality = self.masterKey[1]
        # intervals = ChordFamily.getIntervals(baseQuality)
        intervalQualities = ChordFamily.getIntervalQualities(baseQuality)

        childQuality = intervalQualities[childRel - 1]
        self.child = self.getChordString(childRel, childQuality)

    def getChordString(self, rel, quality, inversion=-1, seventh=False):
        roman = {1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v', 6: 'vi', 7: 'vii'}
        inversion5 = {0: '', 1: '6', 2: '6-4'}
        inversion7 = {0: '7', 1: '6-5', 2: '4-3', 3: '4-2'}
        string = roman[rel]
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
            string += inversion7[inversion]
        elif not seventh and inversion != -1:
            string += inversion5[inversion]

        # Always use relative dominant 7
        if self.child.upper() != 'I':
            string += '/' + self.child

        return string


class ChordFamily:
    def __init__(self, keyNoOct, quality, baseKeyNoOct):
        self.keyNoOct = keyNoOct
        self.quality = quality
        self.baseKeyNoOct = baseKeyNoOct
        self.base = self.setBaseChordVals()

    def setBaseChordVals(self):
        li = 0
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
            print("Key: ", self.keyNoOct, "quality: ", self.quality)
            print("CHORD SET NOT FOUND")
            return -1
        gap = (Note.getValueByKey(self.keyNoOct) - Note.getValueByKey(self.baseKeyNoOct)) % 12
        for i in range(len(li)):
            li[i] = (li[i] + gap) % 12
        return li

    def getChord(self, lowestNoteNoOct, masterKey):
        inversion = 0
        while inversion < len(self.base) and lowestNoteNoOct != self.base[inversion]:
            inversion += 1

        if inversion == len(self.base):
            print("ERROR WITH CHORD FAMILY", self.keyNoOct, self.quality, self.baseKeyNoOct)
            quit()

        rel = (ord(self.keyNoOct[0]) - ord(self.baseKeyNoOct[0])) % 7 + 1
        return Chord(self.quality, rel, inversion, self.base, masterKey)


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
