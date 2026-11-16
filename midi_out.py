import mido


class MidiOut:
    def __init__(self, name='Jazz Hands Port'):
        self.port = mido.open_output(name, virtual=True)
        self.current_notes = []

    # plays a chord or single note
    # play None for silence

    def play(self, notes):
        if notes is None:
            notes = []
        elif isinstance(notes, int):
            notes = [notes]
        if notes == self.current_notes:
            return
        for n in self.current_notes:
            self.port.send(mido.Message('note_off', note=n))
        for n in notes:
            self.port.send(mido.Message('note_on', note=n, velocity=64))
        self.current_notes = notes

    # these allow it to work with a 'with' block
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.port.reset()
        self.port.close()
