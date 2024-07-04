import os
import numpy as np
import cv2
import face_recognition
import datetime
from firebase_admin import db
from firebase_admin import storage


def fetch_encodings_and_ids_from_firebase():
    # Firebase database reference
    reference = db.reference('/Encoding')

    # Initialize lists to store student IDs and encodings
    student_ids = []
    encodings = []

    # Iterate over each student ID
    for student_id in reference.get():
        # Append the student ID to the list
        student_ids.append(student_id)
        # Iterate over each index (0, 1, ...) under the student ID node
        data = db.reference(f'/Encoding/{student_id}').get()
        for index in data:
            # Convert the encoding list from JSON to numpy array
            encoding_array = np.array(index)
            # Append the encoding to the list of encodings for the current student
            encodings.append(encoding_array)

    return student_ids, encodings


def run_face_recognition(teacher_id, topic_covered):
 
    bucket = storage.bucket()

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    # Importing the modes into a list
    current_directory = os.path.dirname(__file__)

    background = os.path.join(current_directory, 'static', 'teacher', 'Resources', 'background.png')
    imgBackground = cv2.imread(background)

    # Construct the path to the Modes directory
    folderModePath = os.path.join(current_directory, 'static', 'teacher', 'Resources', 'Modes')

    modePathList = os.listdir(folderModePath)
    imgModeList = []
    # print(modePathList)
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    # Fetch encodings and student IDs from Firebase
    studentIds, encode_list_known = fetch_encodings_and_ids_from_firebase()
    # print(encode_list_known)
    modeType = 0
    counter = 0
    roll_no = -1
    imgStudent = []

    while True:
        success, img = cap.read()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.5)
                faceDis = face_recognition.face_distance(encode_list_known, encodeFace)
                # print("matches", matches)
                # print("faceDis", faceDis)

                matchIndex = np.argmin(faceDis)
                # print("Matched Index", matchIndex)

                if matches[matchIndex]:
                    # print(studentIds[matchIndex])
                    roll_no = studentIds[matchIndex]
                    if counter == 0:
                        counter = 1
                        modeType = 1

            if counter != 0:
                if counter == 1:

                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")

                    # Path to teacher's attendance record
                    teacher_ref = db.reference(f'Attendance/{teacher_id}')

                    # Check if the teacher ID exists
                    if not teacher_ref.get():
                        # If teacher ID does not exist, create the initial structure
                        teacher_ref.set({})

                    # Path to student's attendance record under the teacher's ID
                    student_ref = teacher_ref.child(roll_no)

                    # Check if the student roll number exists
                    if not student_ref.get():
                        # If student roll number does not exist, create the initial structure
                        student_ref.set({
                            'total_attendance': 0,
                            current_date: {
                                'last_attendance_time': '00:00:00',
                                'topics_covered': topic_covered
                            }
                        })

                    # Check if current date exists under the student's attendance record
                    if not student_ref.child(current_date).get():
                        # If current date does not exist, create the initial structure
                        student_ref.child(current_date).set({
                            'last_attendance_time': '00:00:00',
                            'topics_covered': topic_covered
                        })

                    studentInfo = db.reference(f"Student/{roll_no}").get()
                    studentAtt = db.reference(f'Attendance/{teacher_id}/{roll_no}/{current_date}/').get()
                    studenttotal = db.reference(f'Attendance/{teacher_id}/{roll_no}/').get()
                    current_date_ref = db.reference(f'Attendance/{teacher_id}/{roll_no}/{current_date}')

                    # Get the Image from Storage
                    blob = bucket.get_blob(f"Images/{roll_no}.jpg")
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    time_object = datetime.datetime.strptime(studentAtt['last_attendance_time'], "%H:%M:%S")

                    # Get the current datetime object
                    current_datetime = datetime.datetime.now()

                    # Calculate the elapsed time in seconds since last attendance
                    # Construct datetime object using current date and time from studentAtt
                    datetimeObject = datetime.datetime.combine(current_datetime.date(), time_object.time())

                    # Calculate elapsed time in seconds since last attendance
                    secondElapsed = (current_datetime - datetimeObject).total_seconds()

                    # print("Datetime Object:", datetimeObject)
                    # print("Current Datetime:", current_datetime)
                    # print("Elapsed Time in Seconds:", secondElapsed)
                    # Check if more than 60 seconds have elapsed since last attendance
                    if secondElapsed > 60:
                        # Reference to the student's attendance record
                        ref = db.reference(f"Attendance/{teacher_id}/{roll_no}/")

                        # Increment the total attendance count
                        studenttotal["total_attendance"] += 1

                        # Update total attendance count in the database
                        ref.child("total_attendance").set(studenttotal["total_attendance"])

                        # Update the value of topics_covered under current_date
                        current_date_ref.update({'topics_covered': topic_covered})

                        # Update last attendance time in the database
                        ref.child(current_date).child("last_attendance_time").set(
                            datetime.datetime.now().strftime("%H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if modeType != 3:

                    if 10 < counter < 20:
                        modeType = 2

                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        cv2.putText(imgBackground, str(studenttotal["total_attendance"]), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)

                        cv2.putText(imgBackground, str(studentInfo["batch"]), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        cv2.putText(imgBackground, str(roll_no), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                        (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w)//2
                        cv2.putText(imgBackground, str(studentInfo["name"]), (808+offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        imgBackground[175:175+216, 909:909+216] = imgStudent

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = []
                        imgStudent = []
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            modeType = 0
            counter = 0

        # cv2.imshow("Webcam", img)
        cv2.imshow("Face Attendance", imgBackground)

        key = cv2.waitKey(2) & 0xFF
        if key == 27:  # ESC Key
            break

        # Check if the window close button is clicked
        if cv2.getWindowProperty('Face Attendance', cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_face_recognition()
