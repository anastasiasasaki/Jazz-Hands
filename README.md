# Jazz-Hands 

GitHub site: https://github.com/anastasiasasaki/Jazz-Hands 

## Start: 

```git clone git@github.com:anastasiasasaki/Jazz-Hands.git``` 

## Environment setup: 
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mediapipe opencv-python
pip install mido python-rtmidi
python3 hand.py
```

Windows:
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install opencv-python mediapipe mido python-rtmidi
python hand.py
```

On Windows, create a MIDI output in loopMIDI before running the app, then
select that port as the MIDI input in your DAW. By default, `MidiOut` prefers
a port containing `Jazz Hands Port`; otherwise, it uses the first available
MIDI output. Pass a specific port name to `MidiOut` in `hand.py` if needed.

## TODO: 
- Revisit what should be organized into MVP, Should, Future 
- Make all the tasks into issues 

## Material: 
You can use any DAW or software-based musical instrument.
https://www.onlinepianist.com/virtual-piano is an option that runs in your browser.
