from pydub import AudioSegment
from pydub.playback import play


class SongConverter:

    def __init__(self, tempo=100):
        self.tempo = tempo
        self.beatTime = round(15000 / self.tempo)

    def getSound(self, note):
        if note.noteLong == 'r':
            return AudioSegment.silent(self.beatTime)
        try:
            return AudioSegment.from_wav("samples/" + note.noteLong + ".wav")[:note.duration * self.beatTime]
        except FileNotFoundError:
            return AudioSegment.silent(self.beatTime * note.duration)

    def precompileSong(self, score):
        output = AudioSegment.silent(duration=16 * self.beatTime * score.LENGTH)
        for channel in range(score.maxUsedChannels):
            currLine = AudioSegment.empty()
            for t in range(score.LENGTH * 16):
                if score.score[t][channel].fresh:
                    currLine = currLine + self.getSound(score.score[t][channel])
            output = output.overlay(currLine)
        return output

    def compileSong(self, score, toPlay=True, toExport=True):
        output = self.precompileSong(score)
        if toPlay:
            play(output)
        if toExport:
            output.export("result.wav", format="wav")
