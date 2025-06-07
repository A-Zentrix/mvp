import cv2
from deepface import DeepFace


def face():
    n=0
    domin_emotion=""
    # Load Camera
    cap = cv2.VideoCapture(0)
    faceCascde = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while True:
        ret, frame = cap.read()
        if n!=0:
            cap.release()
            cv2.destroyAllWindows()
            return domin_emotion
        try:
            result = DeepFace.analyze(frame, actions=['emotion'])
            result = result[0]
            # Detect Faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascde.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, result['dominant_emotion'], (0, 50), font, 1, (0, 255, 0), 2, cv2.LINE_4);
            domin_emotion=result['dominant_emotion']
            n=1
        except:
            print("face not detect")
            n=0
        cv2.imshow("Frame", frame)


        key = cv2.waitKey(1)
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


