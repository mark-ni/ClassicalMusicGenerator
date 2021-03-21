from Score import *
from SongConverter import *

LENGTH = 8
KEY = ['C', 'MAJOR']
TEMPO = 100

score = Score(LENGTH, KEY)
songConverter = SongConverter(TEMPO)

if __name__ == '__main__':
    score.write_sample()
    score.harmonize()
    songConverter.compileSong(score, toPlay=True, toExport=False)
