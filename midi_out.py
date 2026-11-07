import mido


CHORDS = {
    'maj':   [0, 4, 7],
    'min':   [0, 3, 7],
    'aug':   [0, 4, 8],
    'dim':   [0, 3, 6],
    '7':     [0, 4, 7, 10],
    'maj7':  [0, 4, 7, 11],
    'min7':  [0, 3, 7, 10],
    'm7b5':  [0, 3, 6, 10],
    'dim7':  [0, 3, 6, 9],
}

NOTES = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}





class MidiOut:
    def __init__(self, name = 'Jass Hands Port'):
        self.port = mido.open_output(name, virtual=True)
        self.current_note = None

    # plays one note
    def play(self, note):
        if note == self.current_note:
            return
        if self.current_note is not None:
            self.port.send(mido.Message('note_off', note = self.current_note))
        if note is not None:
            self.port.send(mido.Message('note_on', note = note, velocity = 64))
        self.current_note = note

    # plays a chord based on note 
    def chord(quality, root, octave = 3):
        if quality not in CHORDS:
            raise ValueError(f"Unknown chord {quality!r}, pick one of {list(CHORDS)}")
        root_note = 12 * (octave + 1) + NOTES[root]
        return [root + i for i in CHORDS[quality]]
        



    # these allow it to work with a 'with' block
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.port.reset()
        self.port.close()

        