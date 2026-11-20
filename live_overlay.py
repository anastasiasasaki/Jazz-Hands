import cv2

WINDOW_NAME = "Jazz Hands (press q to quit)"

def show_overlay(frame, 
                 left_hand_name="None", 
                 left_hand="None", 
                 right_hand_name="None",
                 right_hand="None", 
                 root="None", 
                 quality="None",
                 volume=0):

    if frame is None:
        return True

    frame = frame.copy()

    cv2.putText(frame, f"Left hand: {left_hand_name} {left_hand}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Right hand: {right_hand_name} {right_hand}",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Chord: {root} {quality}",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Volume: {volume}%",
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