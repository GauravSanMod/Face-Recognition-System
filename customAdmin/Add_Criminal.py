import mimetypes
import requests
import concurrent.futures
import pandas as pd
import io
from PIL import Image
import numpy as np
import face_recognition
import firebase_admin
from firebase_admin import credentials, db, storage


# cred = credentials.Certificate('./main/facerecoginitonsystem-firebase-adminsdk-bmyi0-529f7ce1e1.json')
# firebase_admin.initialize_app(cred, {
#     "databaseURL": "https://facerecoginitonsystem-default-rtdb.firebaseio.com/",
#     "storageBucket": "facerecoginitonsystem.appspot.com"
# })

# Define the endpoint URL
url = "https://nia.gov.in/AutoCompleteService.asmx/GetWantedDetail"


def fetch_record(wanted_id):
    payload = {
        'WantedId': f'{wanted_id}',
        'siteId': '1',
        'languageId': '1'
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed for WantedId {wanted_id}: {e}")
        return None

    try:
        response_data = response.json()
        data = response_data.get('d', {})

        return {
            'WantedId': data.get('WantedId'),
            'SiteId': data.get('SiteId'),
            'LanguageId': data.get('LanguageId'),
            'Name': data.get('Name'),
            'Photo': data.get('Photo'),
            'Aliases': data.get('Aliases'),
            'Parentage': data.get('Parentage'),
            'Address': data.get('Address'),
            'IsDeleted': data.get('IsDeleted')
        }
    except (ValueError, KeyError) as e:
        print(f"Failed to parse JSON response for WantedId {wanted_id}: {e}")
        return None


def generate_face_encodings(image_data):
    image_stream = io.BytesIO(image_data)
    image_pil = Image.open(image_stream)
    image_rgb = image_pil.convert("RGB")
    image_np = np.array(image_rgb)
    face_locations = face_recognition.face_locations(image_np)
    if len(face_locations) == 0:
        return None
    face_encodings = face_recognition.face_encodings(image_np, face_locations)
    return face_encodings


def store_encodings(wanted_id, encodings):
    reference = db.reference(f'/Criminal_encoding/{wanted_id}')
    encodings_lists = [encoding.tolist() for encoding in encodings]
    reference.set(encodings_lists)


def fetch_and_process_image(wanted_id, photo_name):
    try:
        photo_url = f"https://nia.gov.in/writereaddata/Portal/Wanted/{wanted_id}_1_1_{photo_name}"
        response = requests.get(photo_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Failed to fetch photo for WantedId {wanted_id}: {e}")
        return None


def save_criminal_image(image_data, image_name):
    bucket = storage.bucket()
    folder_path = 'Criminal_img/'

    content_type, _ = mimetypes.guess_type(image_name)
    blob = bucket.blob(folder_path + image_name)

    blob.upload_from_string(image_data, content_type=content_type)
    image_url = blob.public_url

    return image_url


def save_criminal_data(Name, WantedId, Aliases, Parentage, Address, IsDeleted, Photo):
    # Reference to the Firebase Realtime Database
    ref = db.reference('Criminal')

    # Create a new child node with the student's roll number as the key
    Crim_ref = ref.child(str(WantedId))

    # Set the student data in the Firebase Realtime Database
    Crim_ref.set({
        'Name': Name,
        'Aliases': Aliases,
        'Parentage': Parentage,
        'WantedId': WantedId,
        'Address': Address,
        'IsDeleted': IsDeleted,
        'Photo': Photo,
    })

    return True


def fetch_data_store(start, end):
    start_id = start
    end_id = end
    datalist = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(fetch_record, i) for i in range(start_id, end_id + 1)]

        for future in concurrent.futures.as_completed(futures):
            data = future.result()
            if data:
                datalist.append(data)

    df = pd.DataFrame(datalist)
    df.dropna(subset=['Photo', 'IsDeleted'], inplace=True)

    filtered_df = df[
        (df['Photo'] != 'imgnotavailable.jpg') &
        (df['Photo'] != 'notavailable.jpg') &
        (df['IsDeleted'] == False)
        ]

    for index, row in filtered_df.iterrows():
        image_data = fetch_and_process_image(row['WantedId'], row['Photo'])
        if image_data:
            encodings = generate_face_encodings(image_data)
            if encodings:
                store_encodings(row['WantedId'], encodings)
                save_criminal_image(image_data, f"{row['WantedId']}_{row['Photo']}")
                # student_details = {
                #     'Name': row['Name'],
                #     'WantedId': row['WantedId'],
                #     'Aliases': row['Aliases'],
                #     'Parentage': row['Parentage'],
                #     'Address': row['Address'],
                #     'IsDeleted': row['IsDeleted'],
                #     'Photo': row['Photo'],
                # }
                save_criminal_data(
                    Name=row['Name'],
                    WantedId=row['WantedId'],
                    Aliases=row['Aliases'],
                    Parentage=row['Parentage'],
                    Address=row['Address'],
                    IsDeleted=row['IsDeleted'],
                    Photo=row['Photo']
                )
            else:
                print(f"No faces found in the image for WantedId {row['WantedId']}")
        else:
            print(f"Failed to fetch or process image for WantedId {row['WantedId']}")

    print("Done")


if __name__ == "__main__":
    fetch_data_store()

