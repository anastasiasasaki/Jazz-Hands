"""

Jazz Hands main script aka the Hand 

Left hand  -> static finger pattern picks the chord (chords.json)

"""
import json
import math
import time
import urllib.request
from collections import namedtuple
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from chord_builder import chord
from live_overlay import show_overlay, close_overlay
from midi_out import MidiOut

# Files are looked up next to this script, so it works from any folder.
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "hand_landmarker.task"
CHORDS_PATH = BASE_DIR / "chords.json"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

# Set to True if the labels on screen say Left for your right hand.
SWAP_HAND = False

# How much farther the fingertip must be from the wrist than the middle joint before the finger counts as straight. Raise it if curled fingers count as straight; lower it if straight fingers are missed. 
EXTEND_RATIO = 1.1

# One recognised left-hand gesture: name from chords.json, a label for the overlay
# (e.g. "E maj") and the MIDI notes.
Gesture = namedtuple("Gesture", ["name", "label", "notes"])


# ---------------------------------------------------------------- 
# setup
# ---------------------------------------------------------------- 

def load_gestures(path):

    # Read chords.json and return {(index, middle, ring, pinky): Gesture}.

    # "fingers" is 4 characters for (index, middle, ring, pinky):
    # 1 = finger straight, 0 = finger curled. The thumb is ignored.
    
    gestures = {}
    with open(path) as f:
        for name, spec in json.load(f).items():
            fingers = spec["fingers"]
            if len(fingers) != 4 or set(fingers) - {"0", "1"}:
                raise SystemExit(f'chords.json: "{name}" needs "fingers" to be '
                                 f'4 characters of 0/1, got {fingers!r}')

            pattern = tuple(c == "1" for c in fingers)  # "1100" -> (True, True, False, False)
            if pattern in gestures:
                raise SystemExit(f'chords.json: "{name}" uses the same fingers as '
                                 f'"{gestures[pattern].name}"')

            notes = chord(spec["quality"], spec["root"], spec.get("octave", 3))
            gestures[pattern] = Gesture(name, f'{spec["root"]} {spec["quality"]}', notes)

    return gestures


def make_landmarker():

    # Download the MediaPipe model on first run, then create the hand landmarker. 

    if not MODEL_PATH.exists():
        print("Downloading model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
    )

    return vision.HandLandmarker.create_from_options(options)


# ---------------------------------------------------------------- 
# left hand
# ---------------------------------------------------------------- 

# MediaPipe gives 21 landmarks per hand: 0 = wrist, thumb 1-4, index 5-8, middle 9-12, ring 13-16, pinky 17-20. Each pair is (PIP joint, fingertip), where PIP is the middle knuckle of the finger. 

FINGERS = [
    (6, 8),     # index
    (10, 12),   # middle
    (14, 16),   # ring
    (18, 20),   # pinky
]

def finger_states(lm):
    
    # Return (index, middle, ring, pinky) as True (straight) / False (curled).

    # A straight finger has its tip far from the wrist; a curled finger folds its tip back toward the palm, so the tip is about as close to the wrist as the middle knuckle. Comparing distances (not angles) works when the hand is tilted or turned.
    
    def d(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    return tuple(d(lm[0], lm[tip]) > EXTEND_RATIO * d(lm[0], lm[pip])
                 for pip, tip in FINGERS)


# ----------------------------------------------------------------
# right hand  (TODO list)
# ----------------------------------------------------------------

# TODO: volume_from_height(lm) -> a whole number from 0 to 100. Pick one point on the hand (e.g. 9 = base of the middle finger). In the picture y = 0 is the top, so flip it so a higher hand means louder. Use only the middle part of the frame (e.g. 15%-85% of the height) as the 0-100 range, and smooth the number so it doesn't shake.

# TODO: pitch_from_palm(lm) -> a whole number like -1 / 0 / +1 (octave down / same / up). Palm direction may be unreliable, so test first (e.g. compare the x of the wrist with the x of point 9). Make it harder to switch than to stay, so it doesn't flicker near the limit. 

# TODO: in main(), handle the "Right" hand inside the hand loop. Keep the volume and pitch values outside the loop so they stay the same when the hand leaves the frame. Pass them to show_overlay(volume=..., pitch=...). Pitch must be a whole number. 

# TODO: send them to MIDI. Move the chord notes by 12 for each octave before midi.play(), and change MidiOut.play() so it uses the volume (note velocity, or CC 7). 


# ----------------------------------------------------------------
# drawing - for the on-screen skeleton 
# ---------------------------------------------------------------- 



# Which landmark pairs to connect with lines (the hand skeleton).

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                 # palm edge
]


def draw_hand(frame, lm, label):
    
    # Draw the skeleton and the Left/Right label on the (mirrored) frame.

    h, w = frame.shape[:2]
    
    # The picture was flipped, so a point at fraction x in the raw frame is at 1 - x.
    
    pts = [(int((1 - p.x) * w), int(p.y * h)) for p in lm]

    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2)
    
    for p in pts:
        cv2.circle(frame, p, 4, (0, 0, 255), -1)
    
    cv2.putText(frame, label, (pts[0][0], pts[0][1] + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)


# ---------------------------------------------------------------- 
# main loop
# ---------------------------------------------------------------- 

def detect_hands(landmarker, frame, ts):

    # Run MediaPipe on one raw (unflipped) BGR frame; return [(label, landmarks)]. 

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect_for_video(mp_image, ts)

    hands = []
    
    for lm, handed in zip(result.hand_landmarks, result.handedness):
        label = handed[0].category_name  # "Left" or "Right"
        
        if SWAP_HAND:
            label = "Right" if label == "Left" else "Left"
        
        hands.append((label, lm))
    
    return hands

# ---------------------------------------------------------------- 
# main
# ---------------------------------------------------------------- 

def main():
    gestures = load_gestures(CHORDS_PATH)
    landmarker = make_landmarker()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise SystemExit("Could not open the webcam.")

    # VIDEO mode needs a timestamp in ms for every frame, each one larger than the last. last_ts forces it up if two frames land in the same millisecond.
    
    start = time.time()
    last_ts = -1

    try:
        # "with" silences and closes the virtual MIDI port even if the program
        # crashes, so a note never gets stuck.
        with MidiOut() as midi:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                ts = max(int((time.time() - start) * 1000), last_ts + 1)
                last_ts = ts
                hands = detect_hands(landmarker, frame, ts)

                frame = cv2.flip(frame, 1)   # mirror so left is left on screen

                current = None       # Gesture, or None if no chord this frame

                # RIGHT HAND (todo): the volume and pitch values need to live outside this loop, so they keep their last value when the right hand leaves the frame (or reset to a default - decide which).
                # Start them from a sensible default before the loop begins.

                for label, lm in hands:
                    if label == "Left" and current is None:
                        current = gestures.get(finger_states(lm))

                    # RIGHT HAND (todo): handle label == "Right" here, calling the
                    # functions from the "right hand" section above to update the
                    # volume and pitch values.

                    draw_hand(frame, lm, label)

                # RIGHT HAND (todo): apply the pitch range to the chord notes
                # before play() (for example shift by 12 semitones per octave and
                # keep every note inside 0-127). MidiOut.play() only takes notes
                # and sends a fixed velocity of 64, so volume needs a change in
                # midi_out.py: either use the volume as note velocity (only applies
                # when a chord starts) or send a control change message for
                # volume (CC 7), which some synths ignore until you map it.
                # A new note list makes play() retrigger the chord, which is fine.

                # play() ignores repeats, so calling this every frame is fine.
                midi.play(current.notes if current else None)

                # RIGHT HAND (todo): pass volume= and pitch= to show_overlay().
                # It already accepts both. Volume is printed with a "%" sign, and
                # pitch must be an int, because it is formatted with ":+d" and a
                # float would raise an error. Until then the overlay shows 0 for both.
                keep_going = show_overlay(
                    frame,
                    gesture=current.name if current else "None",
                    chord=current.label if current else "None",
                )

                if not keep_going:
                    break
    
    finally:
        cap.release()
        close_overlay()


if __name__ == "__main__":
    main()
