import cv2

# puts text to the right of the screen
def align_text_right(frame, 
                    text, 
                    right_x, 
                    y, 
                    scale=0.8, 
                    color=(0, 255, 0), 
                    thickness=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.putText(frame, text, (right_x - text_w, y), font, scale, color, thickness, cv2.LINE_AA)

def align_text_center(frame, 
                    text, 
                    center_x, 
                    y, 
                    scale=0.8, 
                    color=(0, 255, 0), 
                    thickness=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.putText(frame, text, (center_x - text_w // 2, y), font, scale, color, thickness, cv2.LINE_AA)