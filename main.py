from Score import *
from SongConverter import *

LENGTH = 8
KEY = ['C', 'MAJOR']
TEMPO = 100

score = Score(LENGTH, KEY)
songConverter = SongConverter(TEMPO)

if __name__ == '__main__':

    # This part is here while I figure out how to write tests in pycharm
    score.write_sample()
    score.harmonize()
    score.print_score()
    songConverter.compileSong(score, toPlay=True, toExport=False)
