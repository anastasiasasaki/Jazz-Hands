import os
import json 
import math 
import time 
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from midi_out import MidiOut, chord

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

# should fix the inverted hands issue - set to True if the labels on screen say Left for your right hand , if not leave it as is 
SWAP_HAND = False 

# this is for how much farther the fingertip must be from the wrist than the middle joint before the finger counts as straight. 
# test: increase if curled fingers are being counted as straight; lower it if straight fingers are being missed 
EXTEND_RATIO = 1.1 



# Download the model file once (first run only).
if not os.path.exists(MODEL_PATH):
    print("Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

# Load chords.json

# Each entry looks like: "two": {"fingers": "1100", "root": "E", "quality": "maj"}

# "fingers" is 4 characters for (index, middle, ring, pinky): 1 = finger straight, 0 = finger curled.  ignore thumb. "0000" is a fist and "1111" is four fingers up. 4 fingers give 16 possible patterns in total. 

# GESTURES :  (index, middle, ring, pinky) -> (name, midi notes)

GESTURES = {}
with open("chords.json") as f:
    for name, spec in json.load(f).items():
        fingers = spec["fingers"]

        # error out if the json file has the wrong format 
        if len(fingers) != 4 or set(fingers) - {"0", "1"}:
            raise SystemExit(f'chords.json: "{name}" needs "fingers" to be '
                             f'4 characters of 0/1, got {fingers!r}')
        
        pattern = tuple(c == "1" for c in fingers)  # "1100" -> (True, True, False, False)

        if pattern in GESTURES:
            raise SystemExit(f'chords.json: "{name}" uses the same fingers as '
                             f'"{GESTURES[pattern][0]}"')
        
        notes = chord(spec["quality"], spec["root"], spec.get("octave", 3))
        GESTURES[pattern] = (name, notes)

# Finger detection

# MediaPipe gives 21 landmark points per hand, numbered like this: 0 = wrist, thumb  1-4, index 5-8, middle 9-12, ring 13-16, pinky 17-20...  each finger the numbers go from the palm out to the tip:
#   e.g. index: 5 = base knuckle, 6 = middle knuckle (the PIP joint), 7 = upper joint, 8 = fingertip

# PIP = "proximal interphalangeal" joint = the middle knuckle of a finger, the first place the finger bends after the base knuckle ->  each pair below is (PIP joint number, fingertip number) for one finger 

FINGERS = [
    (6, 8),     # index
    (10, 12),   # middle
    (14, 16),   # ring
    (18, 20),   # pinky
]

def finger_states(lm):
    
    # return (index, middle, ring, pinky) as True (straight) / False (curled)

    # a straight finger = its tip far from the wrist, 
    # a curled finger = folds its tip back toward the palm, so the tip is as close to the wrist as the middle knuckle
    # this makes sure it works when your hand is tilted or turned 


    def d(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    return tuple(d(lm[0], lm[tip]) > EXTEND_RATIO * d(lm[0], lm[pip])
                 for pip, tip in FINGERS)


# which landmark pairs to connect with lines (skeleton) 

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm edge
]

# set up MediaPipe. VIDEO mode = hand it one frame at a time and wait
# needs each frame to come with a timestamp 

options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
)

landmarker = vision.HandLandmarker.create_from_options(options)

# quit if webcame fails 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Could not open the webcam.")

# VIDEO mode needs a timestamp in milliseconds for every frame, each new > last 
# milliseconds since the program started 
# last_ts force it to go up if two frames land in the same millisecond 

start = time.time()
last_ts = -1

# makes sure if a program crashes it closes the port instead of playing the note that it's stuck on 
# "with MidiOut() as midi" opens the virtual MIDI port, and when the block ends (even if the program crashes) it automatically silences and closes the port, so you never get a stuck note 
# __enter__/__exit__ in midi_out.py 

with MidiOut() as midi:
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # make sure its the raw video feed, not the flipped one
        # OpenCV uses BGR, MediaPipe wants RGB

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = max(int((time.time() - start) * 1000), last_ts + 1)
        last_ts = ts
        result = landmarker.detect_for_video(mp_image, ts)

        # mirror the image so left hand is left and right is right 

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # each frame starts without a chord 
        # gets a chord when the left hand is found && the finger pattern exists in chords.json 

        current = None  # (name, notes)

        for lm, handed in zip(result.hand_landmarks, result.handedness):
            label = handed[0].category_name  # "Left" or "Right"

            if SWAP_HAND:
                label = "Right" if label == "Left" else "Left"

            if label == "Left" and current is None:
                current = GESTURES.get(finger_states(lm))  # if not in chords.json then None

            # landmark x and y are fractions from 0 to 1 (x = how far vertically across the picture, y = how far down horizontally) 
            # multiply by width/height to get pixels 
            # picture was flipped, so point at fraction x in the raw frame is at 1 - x, so (1 - p.x) 

            pts = [(int((1 - p.x) * w), int(p.y * h)) for p in lm]

            for a, b in CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)

            for p in pts:
                cv2.circle(frame, p, 4, (0, 0, 255), -1)

            cv2.putText(frame, label, (pts[0][0], pts[0][1] + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # play chord, or silence if current is None (midi.play(None) turns off whatever is playing) 
        # midi_out.py ignores repeats of the same chord, so calling this every frame is fine 

        midi.play(current[1] if current else None)

        # testing delete 

        # text = f"Left hand: {current[0]}" if current else "Left hand: none"
        # cv2.putText(frame, text, (20, 40),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Hand demo (press q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()







# delete later 
""" # Which landmark points to connect with lines (the hand skeleton).
CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm edge
]

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Could not open the webcam.")

start = time.time()
last_ts = -1
while True:
    ok, frame = cap.read()
    if not ok:
        break
    # Mirror the image like a selfie view. If Left/Right look swapped on
    # your screen, comment out this line.
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    ts = max(int((time.time() - start) * 1000), last_ts + 1)  # must increase
    last_ts = ts
    result = landmarker.detect_for_video(mp_image, ts)

    h, w = frame.shape[:2]
    for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
        pts = [(int(p.x * w), int(p.y * h)) for p in landmarks]
        for a, b in CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)
        for p in pts:
            cv2.circle(frame, p, 4, (0, 0, 255), -1)
        label = handedness[0].category_name  # "Left" or "Right"
        cv2.putText(frame, label, (pts[0][0], pts[0][1] + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    cv2.imshow("Hand demo (press q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break """




