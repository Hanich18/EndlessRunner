# import the necessary packages
import numpy as np
import cv2
import threading
DEFAULT_HEIGHT = 175
DEFAULT_JUMP_THRESH = 10
DEFAULT_CROUCH_THRESH = 20
DEFAULT_LEFT_RIGHT_THRESH = 20
class Scanner:

    def __init__(self, callback) -> None:
        self.defult_y = 0
        self.defult_height = 0
        self.largest_box = None
        self.jump_thresh = DEFAULT_JUMP_THRESH
        self.crouch_thresh = DEFAULT_CROUCH_THRESH
        self.center = 0
        self.left_right_thresh = DEFAULT_LEFT_RIGHT_THRESH
        self.callback = callback
        self.last_action = ""

        # initialize the HOG descriptor/person detector
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        cv2.startWindowThread()

        # open webcam video stream
        self._cap = cv2.VideoCapture(0)

    def calibrate(self):
        x, y, w, h = self.largest_box
        print(x,y,w,h)
        self.scale = h / DEFAULT_HEIGHT
        self.jump_thresh = DEFAULT_JUMP_THRESH * self.scale
        self.crouch_thresh = DEFAULT_CROUCH_THRESH * self.scale
        self.left_right_thresh = DEFAULT_LEFT_RIGHT_THRESH * self.scale

        self.defult_y = y + h // 2
        self.defult_height = h
        self.center = x + w // 2
        print("calibrated")

    def test_for_action(self):
        action = None
        (x, y, w, h) = self.largest_box
        if self.defult_y - (y+ h // 2) > self.jump_thresh:
            action = "JUMP"
        elif h+self.crouch_thresh < self.defult_height:
            action = "TOOK"
        elif x+w//2 > self.center + self.left_right_thresh:
            action = "RIGHT"
        elif x+w//2 < self.center - self.left_right_thresh:
            action = "LEFT"
        else:
            action = "CENTER"
        
        if action is not None:
            if self.last_action != action:
                self.last_action = action
                self.callback(action)

    def find_shoes(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_gray = np.array([0, 5, 50], np.uint8)
        upper_gray = np.array([200, 200, 200], np.uint8)
        mask_gray = cv2.inRange(hsv, lower_gray, upper_gray)
        img_res = cv2.bitwise_and(img, img, mask = mask_gray)

        cv2.imshow("res", img_res)
        
    def run_scanner(self):
        thread = threading.Thread(target=self.scan)
        thread.start()
    
    def scan(self):
        while True:
            # Capture frame-by-frame
            ret, frame = self._cap.read()
            frame=cv2.flip(frame, 1)
            # resizing for faster detection
            frame = cv2.resize(frame, (320, 240))
            # using a greyscale picture, also for faster detection
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # detect people in the image
            # returns the bounding boxes for the detected objects
            boxes, weights = self._hog.detectMultiScale(frame, winStride=(2,2) )
            boxes = Scanner.find_largest(boxes)
            if boxes:
                largest_box = boxes[0]
                x, y, w, h = largest_box
                
                cropped_person = frame[y:y+h,x:x+w]
                cropped_person = cv2.resize(cropped_person,(320,520))

                #cv2.imshow("person",cropped_person)
                self.largest_box = largest_box
                
                #finding shoes:
                #self.find_shoes(cropped_person)

                # test for actions:
                self.test_for_action()

            boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])

            for (xA, yA, xB, yB) in boxes:
                # display the detected box in the colour picture
                cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 255, 0), 2)


            # Display the resulting frame
            frame = cv2.resize(frame, (720, 480))
            cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.waitKey(1) & 0xFF == ord(' '):
                self.calibrate()

        # When everything done, release the capture
        self._cap.release()
        # finally, close the window
        cv2.destroyAllWindows()
        cv2.waitKey(1)
    
    @staticmethod
    def get_surface(box):
        x, y, w, h = box
        return w * h

    @staticmethod
    def find_largest(boxes):
        if len(boxes) == 0:
            return boxes
        return [max(boxes, key = Scanner.get_surface)]

if __name__ == "__main__":
    scan = Scanner(lambda action: print(action))
    scan.run_scanner()