import os
import json 
import math 
import time 
import urllib.request
from midi_out import MidiOut, chord, CHORDS, set_volume
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from live_overlay import show_overlay
from utilities import align_text_center



print([line for line in cv2.getBuildInformation().splitlines() if "GUI:" in line])


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


settings = {
    "debug": False,
    "quantize": True
}




# Each entry looks like: "two": {"fingers": "1100", "root": "E", "quality": "maj"}

# "fingers" is 4 characters for (index, middle, ring, pinky): 1 = finger straight, 0 = finger curled.  ignore thumb. "0000" is a fist and "1111" is four fingers up. 4 fingers give 16 possible patterns in total. 

# GESTURES_LEFT_HAND :  (index, middle, ring, pinky) -> (name, midi notes)
# this gets the chord quality
GESTURES_LEFT_HAND = {}
# with open("quality.json") as f:
with open("quality.json", encoding="utf-8") as f:
    for name, spec in json.load(f).items():
        fingers = spec["fingers"]

        # error out if the json file has the wrong format 
        if len(fingers) != 4 or set(fingers) - {"0", "1"}:
            raise SystemExit(f'quality.json: "{name}" needs "fingers" to be '
                             f'4 characters of 0/1, got {fingers!r}')
        
        pattern = tuple(c == "1" for c in fingers)  # "1100" -> (True, True, False, False)

        if pattern in GESTURES_LEFT_HAND:
            raise SystemExit(f'quality.json: "{name}" uses the same fingers as '
                             f'"{GESTURES_LEFT_HAND[pattern][0]}"')
        
        GESTURES_LEFT_HAND[pattern] = (name, spec["quality"])

        if spec["quality"] not in CHORDS:
            raise SystemExit(f'quality.json: "{name}" has unknown quality {spec["quality"]!r}')

# this gets the root of the chord
GESTURES_RIGHT_HAND = {}
# with open("roots.json") as f:
with open("roots.json", encoding="utf-8") as f:
    for name, spec in json.load(f).items():
        fingers = spec["fingers"]

        # error out if the json file has the wrong format 
        if len(fingers) != 4 or set(fingers) - {"0", "1"}:
            raise SystemExit(f'roots.json: "{name}" needs "fingers" to be '
                             f'4 characters of 0/1, got {fingers!r}')
        
        pattern = tuple(c == "1" for c in fingers)  # "1100" -> (True, True, False, False)

        if (pattern, spec["angle"]) in GESTURES_RIGHT_HAND:
            raise SystemExit(f'roots.json: "{name}" uses the same pattern as '
                             f'"{GESTURES_RIGHT_HAND[(pattern, spec["angle"])][0]}"')
        
        GESTURES_RIGHT_HAND[(pattern, spec["angle"])] = (name, spec["root"], spec["angle"])

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


# check angle of palm
def palm_spread_angle(lm, w, h):
    # convert to pixels
    wx, wy = lm[0].x * w, lm[0].y * h
    ix, iy = lm[5].x * w, lm[5].y * h
    px, py = lm[17].x * w, lm[17].y * h

    v1 = (ix - wx, iy - wy) # line from wrist to base of index finger
    v2 = (px - wx, py - wy) # line from wrist to base of pinkie finger

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    cross = v1[0] * v2[1] - v1[1] * v2[0]

    return math.degrees(math.atan2(cross, dot))


# calculates volume as percentage based on palm center height relative to window size
# volume is in ints from 0-127 because of how CC7 midi channel volume operates
def vol_calculate(lm, h):
    # convert to pixels
    wy = lm[0].y * h
    my = lm[9].y * h

    # average of wrist and middle knuckle should be about center of palm
    palm_height = (wy + my) / 2

    max_h = h / 2  # 100% when palm is at or higher than halfway up from bottom
    min_h = h - h / 5  # 0% when palm center is at or lower than a fifth from bottom

    if palm_height < max_h:
        return 127
    if palm_height > min_h:
        return 0

    return int(127 * (min_h - palm_height) / (min_h - max_h))

# which landmark pairs to connect with lines (skeleton) 

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm edge
]

# # set up MediaPipe. VIDEO mode = hand it one frame at a time and wait
# # needs each frame to come with a timestamp 
# options = vision.HandLandmarkerOptions(
#     base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
#     running_mode=vision.RunningMode.VIDEO,
#     num_hands=2,
# )

# set upp MediaPipe to run independently
latest_result = None
landmarker_time = 0

volume = 0

def on_result (result, output_image, timestamp_ms):
    global latest_result, landmarker_time
    latest_result = result
    # new landmarker latency calculation reuses the VIDEO mode timestamps
    landmarker_time = (time.time() - start) * 1000 - timestamp_ms

options = vision.HandLandmarkerOptions(
    base_options = mp_python.BaseOptions(model_asset_path = MODEL_PATH),
    running_mode = vision.RunningMode.LIVE_STREAM,
    num_hands = 2,
    result_callback = on_result,
)


landmarker = vision.HandLandmarker.create_from_options(options)

# quit if webcame fails 
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Could not open the webcam.")

# 720p resoukltion :D
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


# VIDEO mode needs a timestamp in milliseconds for every frame, each new > last 
# milliseconds since the program started 
# last_ts force it to go up if two frames land in the same millisecond 
last_ts = -1
start = time.time()

# makes sure if a program crashes it closes the port instead of playing the note that it's stuck on 
# "with MidiOut() as midi" opens the virtual MIDI port, and when the block ends (even if the program crashes) it automatically silences and closes the port, so you never get a stuck note 
# __enter__/__exit__ in midi_out.py 

# FORMATS FOR MIDI OUTPUT
# midi.play(48) # plays C
# midi.play(None) # stops output
# midi.play(chord('maj7', 'C')) # plays C7 major
# midi.play(chord('maj7', 'C', 2)) # plays C7 major one octave down
# check midi_out.py for all the chord and note names
# midi.play(chord('maj7', 48)) # plays C7 major
# NOTE ON THESE: They don't play right away. The program needs to run a second or two before your DAW will connect to the midi port. The play() function won't replay a note that's already playing, so because of that putting the commands like this won't make a sound. I made a little demo below to actually play sound. (as long as your hand is visible)

right_palm_angle = "1"

last_second = 0
last_time = time.time()

with MidiOut() as midi:
    while True:
        # check for keypresses
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"): break
        if key == ord("d"): settings["debug"] = not settings["debug"]
        if key == ord("w"): settings["quantize"] = not settings["quantize"]



        # reads the video frame from the webcam
        ok, frame = cap.read()
        if not ok:
            break

        # make sure its the raw video feed, not the flipped one
        # OpenCV uses BGR, MediaPipe wants RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        # gives every frame a timestamp in ms for mediapipe
        ts = max(int((time.time() - start) * 1000), last_ts + 1)
        last_ts = ts
        
        # new landmarker detect that runs asynchronously
        landmarker.detect_async(mp_image, ts)
        result = latest_result

        # mirror the image so left hand is left and right is right
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # fps counter
        if settings["debug"]:
            now = time.time()
            fps = 1 / (now - last_time)
            last_time = now
        

        # each frame starts without a chord 
        # gets a chord when the left hand is found && the finger pattern exists in chords.json 

        quality = None # (name, "maj") from left hand
        root = None # (name, "C") from right hand
        left_hand_gesture = None
        right_hand_gesture = None

        hands = zip(result.hand_landmarks, result.handedness) if result else []
        for lm, handed in hands:
            label = handed[0].category_name  # "Left" or "Right"

            


            if SWAP_HAND:
                label = "Right" if label == "Left" else "Left"

            if label == "Left" and quality is None:
                left_hand_gesture = finger_states(lm)
                quality = GESTURES_LEFT_HAND.get(left_hand_gesture)

            if label == "Right":
                # check right palm angle
                angle = palm_spread_angle(lm, w, h) # compute palm angle
                if angle >= 3:
                    right_palm_angle = "1" 
                elif angle <= -3:
                    right_palm_angle = "0"

                set_volume(midi, vol_calculate(lm, h))
                volume = midi.current_volume
                    
                right_hand_gesture = finger_states(lm)
                root = GESTURES_RIGHT_HAND.get((right_hand_gesture, right_palm_angle))
                

            # landmark x and y are fractions from 0 to 1 (x = how far vertically across the picture, y = how far down horizontally) 
            # multiply by width/height to get pixels 
            # picture was flipped, so point at fraction x in the raw frame is at 1 - x, so (1 - p.x) 
            # this section draws the hand skeleton over the image
            pts = [(int((1 - p.x) * w), int(p.y * h)) for p in lm]

            for a, b in CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)

            for p in pts:
                cv2.circle(frame, p, 4, (0, 0, 255), -1)

            cv2.putText(frame, label, (pts[0][0], pts[0][1] + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

            # debug view for right hand angle 
            if label == "Right" and settings["debug"]:
                text = f"right hand angle: {angle:.01f}"
                cv2.putText(frame, text, (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # debug view for fps, hand landmarker time, camera resolution
        if settings["debug"]:
            cv2.putText(frame, f"{fps:.0f} fps", (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"{landmarker_time:.0f} landmarker miliseconds", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} webcam video", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # play chord, or silence if current is None (midi.play(None) turns off whatever is playing) 
        # midi_out.py ignores repeats of the same chord, so calling this every frame is fine 
        if quality and root:
            if settings["quantize"]:
                if not last_second == int(time.time()):
                    midi.play(chord(quality[1], root[1]))
            else:        
                midi.play(chord(quality[1], root[1]))
        else:
            if settings["quantize"]:
                if not last_second == int(time.time()):
                    midi.play(None)
            else:        
                midi.play(None)
    
        if settings["quantize"]:
            if not last_second == int(time.time()):
                last_second = int(time.time())
                align_text_center(frame, 
                    ".", 
                    w // 2, 
                    90,
                    20)
        
        # show the overlay
        if right_hand_gesture and left_hand_gesture and quality and root:
            show_overlay(frame, settings["debug"], settings["quantize"], volume, quality[0], left_hand_gesture, root[0], right_hand_gesture, root[1], quality[1])
        else:
            show_overlay(frame, settings["debug"], settings["quantize"])


cap.release()
cv2.destroyAllWindows()





