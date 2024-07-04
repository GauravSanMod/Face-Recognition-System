import numpy as np
import cv2
import face_recognition
import requests
from django.http import JsonResponse
from firebase_admin import db, storage
from win10toast import ToastNotifier
import mimetypes
import smtplib
from email.message import EmailMessage


def fetch_encodings_and_ids_from_firebase():
    # Firebase database reference
    reference = db.reference('/Criminal_encoding')

    # Initialize lists to store student IDs and encodings
    wanted_ids = []
    encodings = []

    # Iterate over each student ID
    for wanted_id in reference.get():
        # Append the student ID to the list
        wanted_ids.append(wanted_id)
        # Iterate over each index (0, 1, ...) under the student ID node
        data = db.reference(f'/Criminal_encoding/{wanted_id}').get()
        for index in data:
            # Convert the encoding list from JSON to numpy array
            encoding_array = np.array(index)
            # Append the encoding to the list of encodings for the current student
            encodings.append(encoding_array)

    return wanted_ids, encodings


def send_email_alert(police_email, criminal_name, wanted_id, location, image_url):
    email_address = 'gaurav8bp2@gmail.com'
    email_password = 'vwua kney qdsg yygb'

    msg = EmailMessage()
    msg.set_content(f"""
    Alert: Criminal recognized with the following details:
    Name: {criminal_name}
    Wanted ID: {wanted_id}
    Location: {location}
    Image URL: {image_url}
    """)
    msg['Subject'] = 'Criminal Alert'
    msg['From'] = email_address
    msg['To'] = police_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


def get_current_location():
    try:
        # Send a request to the Google Maps Geocoding API to get location information based on the user's IP address
        response = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
                                params={'key': 'AIzaSyD1-OO3WfdYozIqTos4KjMI193hXD6MxkU', 'address': 'me'})
        data = response.json()

        # Extract latitude and longitude from the response
        if 'results' in data and data['results']:
            location = data['results'][0]['geometry']['location']
            return JsonResponse({'location': location})
        else:
            return JsonResponse({'error': 'Location data not found'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def fetch_criminal_details(wanted_id):
    reference = db.reference(f'/Criminal/{wanted_id}')
    details = reference.get()
    if details:
        return details.get('Name')
    return None


def save_criminal_image(image_data, image_name):
    bucket = storage.bucket()
    folder_path = 'Captured_img/'

    content_type, _ = mimetypes.guess_type(image_name)
    blob = bucket.blob(folder_path + image_name)

    blob.upload_from_string(image_data, content_type=content_type)
    image_url = blob.public_url

    return image_url


def run_recognition():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    # Fetch encodings and student IDs from Firebase
    wanted_ids, encode_list_known = fetch_encodings_and_ids_from_firebase()
    police_email = "modakgaurav2@gmail.com"  # Direct email address to send info

    toaster = ToastNotifier()

    while True:
        success, img = cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.3)
                faceDis = face_recognition.face_distance(encode_list_known, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    wanted_id = wanted_ids[matchIndex]
                    toaster.show_toast("Face Recognition", f"Criminal recognized: {wanted_id}")
                    criminal_name = fetch_criminal_details(wanted_id)
                    location = get_current_location()

                    # Save the captured image
                    img_name = f"{wanted_id}.jpg"
                    _, img_encoded = cv2.imencode('.jpg', img)
                    img_data = img_encoded.tobytes()
                    image_url = save_criminal_image(img_data, img_name)

                    # Send email with details and image URL
                    send_email_alert(police_email, criminal_name, wanted_id, location, image_url)
                    break

        cv2.imshow("Face Recognition", img)  # Show the OpenCV window
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_recognition()
