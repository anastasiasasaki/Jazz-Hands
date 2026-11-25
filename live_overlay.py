import cv2

WINDOW_NAME = "Jazz Hands (press q to quit)"

def show_overlay(frame, left_hand="Unknown", right_hand="Unknown", root="None", quality="None",
                 volume=0):

    if frame is None:
        return True

    frame = frame.copy()

    overlay = frame.copy()
    cv2.rectangle(overlay, (10,10), (300,190), (30,30,30), -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    cv2.putText(frame, f"Left hand: {left_hand}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Right hand: {right_hand}",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"Chord: {root} {quality}",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    bar_width = round(200 * max(0, min(100, volume)) / 100)
    cv2.rectangle(frame, (20, 130), (220, 140), (60, 60, 60), -1)
    if bar_width > 0:
        cv2.rectangle(frame, (20, 130), (20 + bar_width, 140), (0, 255, 0), -1)
    cv2.rectangle(frame, (20, 130), (220, 140), (200, 200, 200), 1)

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
                left_hand="Open Palm",
                right_hand="Open Palm",
                root="C",
                quality="Major",
                volume=75
            ):
                break
    finally:
        close_overlay()