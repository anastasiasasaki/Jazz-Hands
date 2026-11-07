import os
import time
import urllib.request
from midi_out import MidiOut, chord

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

# Download the model file once (first run only).
if not os.path.exists(MODEL_PATH):
    print("Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)



options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
)
landmarker = vision.HandLandmarker.create_from_options(options)

# Which landmark points to connect with lines (the hand skeleton).
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
# open virtual midi port
with MidiOut() as midi:
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


        # # FORMATS FOR MIDI OUTPUT
        # midi.play(48) # plays C
        # midi.play(None) # stops output
        # midi.play(chord('maj7', 'C')) # plays C7 major
        # midi.play(chord('maj7', 'C', 2)) # plays C7 major one octave down
        # # check midi_out.py for all the chord and note names
        # midi.play(chord('maj7', 48)) # plays C7 major
        # NOTE ON THESE: They don't play right away. The program needs to run a second or two before your DAW will connect to the midi port. The play() function won't replay a note that's already playing, so because of that putting the commands like this won't make a sound. I made a little demo below to actually play sound. (as long as your hand is visible)
                        
        # MIDI OUTPUT DEMO
        if result.hand_landmarks:
            # midi.play(chord('maj7', 'C'))
            # midi.play(48)
            # midi.play(chord('maj7', 48))
            # midi.play(chord('maj7', 'C'))
            midi.play(chord('maj7', 'C', 4))
        else:
            midi.play(None)
            

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
            break
    
cap.release()
cv2.destroyAllWindows()
