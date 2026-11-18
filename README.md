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

### Windows:

In the `midi_out.py` file, change line 46 to: virtual=False
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install opencv-python mediapipe mido python-rtmidi
python hand.py
```

## TODO: 
- Finalize Windows compatibility
- Deploy the application

## Material: 
You can use any DAW or software-based musical instrument.
https://www.onlinepianist.com/virtual-piano is an option that runs in your browser.
