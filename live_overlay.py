import cv2
from utilities import align_text_right, align_text_center

WINDOW_NAME = "Jazz Hands (press q to quit, d for debug, w for quantize)"

def show_overlay(frame, 
                debug,
                quantize,
                left_hand_name="-", 
                left_hand="-", 
                right_hand_name="-",
                right_hand="-", 
                root="-", 
                quality="-",
                volume=0):

    # reads the frame's size in pixels
    # frame is a numpy array or something
    h, w = frame.shape[:2]

    if frame is None:
        return True

    frame = frame.copy()

    if debug:
        cv2.putText(frame,
                    f"Left hand: {left_hand_name} {left_hand}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        align_text_right(frame, 
                        f"Right hand: {right_hand_name} {right_hand}",
                        w - 20,
                        40,
                        0.8, (0, 255, 0), 2)
        
    else:
        cv2.putText(frame,
                    f"Left hand: {left_hand_name}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
        align_text_right(frame, 
                        f"Right hand: {right_hand_name}",
                        w - 20,
                        40,
                        0.8, (0, 255, 0), 2)

    

    align_text_center(frame,
                    f"Chord: {root} {quality}",
                    w // 2,
                    40,
                    1.3, (0, 255, 0), 2)

    if quantize:
        align_text_center(frame,
                            f"Quantize",
                            w // 2,
                            80,
                            1.3, (0, 255, 0), 2)

    cv2.putText(frame, f"Volume: {volume}%",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.imshow(WINDOW_NAME, frame)


    try:
        if cv2.getWindowProperty(
            WINDOW_NAME, cv2.WND_PROP_VISIBLE
        ) < 1:
            return False
    except cv2.error:
        return False

    return True


def close_overlay():
    cv2.destroyAllWindows()


#Below is a test function to demonstrate the overlay functionality.
if __name__ == "__main__":
    import numpy as np

    # Create a black background (640x480)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    try:
        while True:
            if not show_overlay(
                frame,
                gesture="Open Palm",
                chord="C Major",
                volume=75,
                pitch=2
            ):
                break
    finally:
        close_overlay()