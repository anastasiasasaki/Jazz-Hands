import cv2

WINDOW_NAME = "Jazz Hands"

def show_overlay(frame, gesture="Unknown", chord="None",
                 volume=0, pitch=0):

    if frame is None:
        return True

    frame = frame.copy()

    cv2.putText(frame, f"Gesture: {gesture}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Chord: {chord}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Volume: {volume}%",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Pitch: {pitch:+d}",
                (20, 160), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.imshow(WINDOW_NAME, frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        return False

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