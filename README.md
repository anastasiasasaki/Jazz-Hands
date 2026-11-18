# Jazz-Hands 

GitHub site: https://github.com/anastasiasasaki/Jazz-Hands 

## Start: 

```git clone git@github.com:anastasiasasaki/Jazz-Hands.git``` 

## Environment setup: 
### MacOS:
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mediapipe opencv-python
pip install mido python-rtmidi
python3 hand.py
```

<<<<<<< HEAD
Windows:
=======
### Windows:

In the `midi_out.py` file, change line 46 to: virtual=False
>>>>>>> main
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install opencv-python mediapipe mido python-rtmidi
python hand.py
```

<<<<<<< HEAD
On Windows, create a MIDI output in loopMIDI before running the app, then
select that port as the MIDI input in your DAW. By default, `MidiOut` prefers
a port containing `Jazz Hands Port`; otherwise, it uses the first available
MIDI output. Pass a specific port name to `MidiOut` in `hand.py` if needed.
=======
## Features:
- Create music using right hand gestures to control chord roots
- Adjust MIDI quality using left hand gestures
- Output to DAW or online synthesizers

## Controls:
Perform these gestures in order to control the MIDI output.
### Right Hand: Roots
Fist: C\
Index: D\
Index, Middle: E\
Index, Middle, Ring: F\
Index, Middle, Ring, Pinky: G\
Pinky: A

### Left Hand: Qualities
Fist: Major\
Index: Minor\
Index, Middle: Augmented\
Index, Middle, Ring: Diminished\
Index, Middle, Ring, Pinky: 7th Chord\
Pinky: Major 7th Chord

>>>>>>> main

## TODO: 
- Finalize Windows compatibility
- Deploy the application
- Finalize report after polishing program

## Material: 
You can use any DAW or software-based musical instrument.
https://www.onlinepianist.com/virtual-piano is an option that runs in your browser.
