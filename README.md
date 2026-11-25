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
python -m pip install mediapipe opencv-python mido python-rtmidi
python3 hand.py
```

### Windows:
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install opencv-python mediapipe mido python-rtmidi
python hand.py
```

## Features:
- Create music using right hand gestures to control chord roots
- Adjust MIDI quality using left hand gestures
- Output to DAW or online synthesizers

## Controls:
Perform these gestures in order to control the MIDI output.
### Right Hand: Roots


Palm facing backwards:

|Gesture|Root|
|:---|---:|
|Fist|C|
|Index|G|
|Index, Middle|D|
|Index, Middle, Ring|A|
|Index, Middle, Ring, Pinky|E|
|Middle, Ring, Pinky|B|

Palm facing forwards:

|Gesture|Root|
|:---|---:|
|Middle, Ring, Pinky|F#|
|Index, Middle, Ring, Pinky|C#|
|Index, Middle, Ring|Ab|
|Index, Middle|Eb|
|Index|Bb|
|Fist|F|

### Left Hand: Qualities

Palm direction here does not matter.

|Gesture|Quality|
|:---|---:|
|Fist|Major|
|Index|Minor|
|Index, Middle|Minor 7th|
|Index, Middle, Ring|Minor 7th flat 5|
|Index, Middle, Ring, Pinky|7th|
|Middle, Ring, Pinky|Major 7th|

Press 'Q' to exit program. 

### Debug controls 
Toggle 'D' for debug. 
Toggle 'W' to enable / disable visual feedback of quantization. 


## Material: 
You can use any DAW or software-based musical instrument.
https://www.onlinepianist.com/virtual-piano is an option that runs in your browser.


