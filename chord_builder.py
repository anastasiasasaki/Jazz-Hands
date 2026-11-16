"""
ChordBuilder: turns chord names from chords.json into MIDI note numbers.

This is the "simple factory" from section 5.5 of the report: it takes a description of what to build (quality, root, octave) and returns the result (a list of MIDI notes).
"""

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

NOTES = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
         'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10,
         'Bb': 10, 'B': 11}


def chord(quality, root, octave=3):
    
    # Return the MIDI notes of a chord, e.g. chord('maj', 'C') -> [48, 52, 55]

    # root can be a note name ('C', 'F#', 'Bb') or a MIDI number (48) 
    
    if quality not in CHORDS:
        raise ValueError(f"Unknown chord {quality!r}, pick one of {list(CHORDS)}")

    if isinstance(root, int):
        root_note = root
    elif root in NOTES:
        root_note = 12 * (octave + 1) + NOTES[root]
    else:
        raise ValueError(f"Unknown root {root!r}")

    return [root_note + i for i in CHORDS[quality]]
