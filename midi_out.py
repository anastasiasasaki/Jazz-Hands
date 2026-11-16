import mido
import platform 

class MidiOut:
    def __init__(self, name='Jazz Hands Port'):
        self.current_notes = []

        if platform.system() == "Darwin":  # macOS
            self.port = mido.open_output(name, virtual=True)
        
        else:  # Windows
            ports = mido.get_output_names()
            if not ports:
                raise RuntimeError(
                    "No MIDI output ports found. On Windows, install and open loopMIDI first."
                )
            
            # Prefer a port matching `name` if the user created one in loopMIDI, otherwise use the first port
            matching_ports = [p for p in ports if name in p]
            target_port = matching_ports[0] if matching_ports else ports[0]
            self.port = mido.open_output(target_port)

    

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
