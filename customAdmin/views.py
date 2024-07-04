import json
import mimetypes
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from firebase_admin import db, storage
from .decorator import AdminDeco
import datetime
from .Add_Criminal import fetch_data_store, save_criminal_data
from .Recognition_function import run_recognition
import face_recognition
from PIL import Image
import io
import numpy as np


def admin_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        admin_ref = db.reference(f'Admin')
        admin_data = admin_ref.get()

        if admin_data is not None and 'Password' in admin_data:
            admin_password = admin_data['Password']
            admin_email = admin_data['Email']

            if admin_password == password and admin_email == email:
                # Authentication successful, store admin id in session
                request.session['ID'] = admin_data['ID']
                messages.success(request, 'Login successful!')
                return redirect('dashboard')

        messages.error(request, 'Invalid email or password.')
    return render(request, "customAdmin/login.html")


@AdminDeco
def dashboard(request):
    student_ref = db.reference("Student/")
    student_data = student_ref.get()
    students = []
    student_count = 0
    if student_data:
        for roll_no, info in student_data.items():
            # Serve image
            image_url = f"/serve_image/{roll_no}"
            student_count += 1
            students.append({
                'roll_no': roll_no,
                'name': info.get('name', ''),
                'email': info.get('email', ''),
                'image_url': image_url
            })
    limited = students[:5]

    # Teacher
    teacher_ref = db.reference("Teacher")
    teacher_data = teacher_ref.get('teacher_id')
    teacher_data_list = teacher_data[0]
    teachers = []
    teacher_count = 0
    # Iterate over each teacher info dictionary in the list
    for teacher_info in teacher_data_list:
        # Skip if teacher_info is None
        if teacher_info is None:
            continue
        teacher_count += 1
        # Extract teacher information from the dictionary
        teacher_id = teacher_info.get('teacher_id')
        teacher_name = teacher_info.get('name', '')
        # Extract other fields as needed

        # Process the teacher information (e.g., construct image URL, etc.)
        image_url = f"/serve_teacher_image/{teacher_id}"

        teachers.append({
            'teacher_id': teacher_id,
            'name': teacher_name,
            'image_url': image_url
        })
    teacher = teachers[:6]

    crim_ref = db.reference('Criminal/')
    criminals_snapshot = crim_ref.get()
    total_criminals = len(criminals_snapshot)
    return render(request, "customAdmin/dashboard.html",
        {'students': limited, 'teachers': teacher, 'stud_count': student_count, 'tech_count': teacher_count, 'crim_count': total_criminals})


def serve_teacher_image(request, teacher_id):
    try:
        # Initialize Firebase Storage client
        bucket = storage.bucket()
        # Get reference to the image file in Firebase Storage
        blob = bucket.blob(f'teacher_images/{teacher_id}.jpg')
        # Download the image data
        image_data = blob.download_as_string()
        # Set content type
        content_type = blob.content_type
        # Return image as HTTP response
        return HttpResponse(image_data, content_type=content_type)
    except Exception as e:
        # Handle exceptions
        print("Error serving image:", str(e))
        return HttpResponse(status=500)  # Return a 500 Internal Server Error


def serve_criminal_image(request, wanted_id, photo):
    try:
        # Initialize Firebase Storage client
        bucket = storage.bucket()
        # Get reference to the image file in Firebase Storage
        blob = bucket.blob(f'Criminal_img/{wanted_id}_{photo}')
        # Download the image data
        image_data = blob.download_as_string()
        # Set content type
        content_type = blob.content_type
        # Return image as HTTP response
        return HttpResponse(image_data, content_type=content_type)
    except Exception as e:
        # Handle exceptions
        print("Error serving image:", str(e))
        return HttpResponse(status=500)  # Return a 500 Internal Server Error


@AdminDeco
def admin_student(request):
    student = db.reference('Student/').get()
    return render(request, "customAdmin/admin_stud.html", {'students': student})


@AdminDeco
def update_student(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        ref = db.reference(f'Student/{roll_no}')
        data = ref.get()
        return render(request, "customAdmin/update_profile.html", {'student': data})
    return redirect('admin_student')


@AdminDeco
def update(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        name = request.POST.get('name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        batch = request.POST.get('batch')
        gender = request.POST.get('gender')

        ref = db.reference(f'Student')
        ref.child(roll_no).update({
            'name': name,
            'address': address,
            'gender': gender,
            'batch': batch,
            'email': email,
        })
    return redirect('admin_student')


@AdminDeco
def delete_student(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        stud_ref = db.reference('Student/')
        encoding_ref = db.reference("Encoding/")
        stud_data = stud_ref.child(roll_no).get()
        if stud_data:
            stud_ref.child(roll_no).delete()
            encoding_ref.child(roll_no).delete()
        data = db.reference('Teacher/').get()
        ref = db.reference('Attendance/')
        attendance_data = ref.get()
        teacher_ids = []

        for item in data:
            if isinstance(item, dict) and 'teacher_id' in item:
                teacher_ids.append(item['teacher_id'])
        for teacher_id in teacher_ids:
            if attendance_data is not None:
                # Check if attendance_data is a list
                if isinstance(attendance_data, list):
                    # Iterate through each dictionary in the list
                    for data_dict in attendance_data:
                        # Check if the data_dict is not empty and is a dictionary
                        if isinstance(data_dict, dict):
                            # Iterate through each roll number dictionary in the data_dict
                            for roll_number, data in data_dict.items():
                                # Check if the roll number matches the desired roll_no
                                if roll_number == roll_no:
                                    # Delete the attendance data for this roll number
                                    ref.child(teacher_id).child(roll_number).delete()
        # Get a reference to the storage bucket
        bucket = storage.bucket()

        # Path to the file you want to delete in Firebase Storage
        file_path = f"Images/{roll_no}.jpg"

        # Delete the file
        blob = bucket.blob(file_path)
        blob.delete()
    return redirect('admin_student')


@AdminDeco
def admin_teacher(request):
    ref = db.reference("Teacher").get()
    teacher_ids = [entry['teacher_id'] for entry in ref if entry is not None]
    data = {}
    report = {}
    for teacher_id in teacher_ids:
        data[teacher_id] = db.reference(f"Teacher/{teacher_id}").get()
        report_ref = db.reference(f"Reported-Attendance/Checked/{teacher_id}/").get()
        if report_ref:
            report[teacher_id] = True
        else:
            report[teacher_id] = False
    return render(request, "customAdmin/admin_teacher.html", {'data': data, 'report': report})


@AdminDeco
def delete_teacher(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('id')
        ref = db.reference("Teacher")
        if ref.child(teacher_id).get():
            ref.child(teacher_id).delete()
        att_ref = db.reference("Attendance")
        if att_ref.child(teacher_id).get():
            att_ref.child(teacher_id).delete()
        bucket = storage.bucket()
        # Path to the file you want to delete in Firebase Storage
        file_path = f"teacher_images/{teacher_id}.jpg"
        # Delete the file
        blob = bucket.blob(file_path)
        blob.delete()
    return redirect('admin_teacher')


@AdminDeco
def update_teacher(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('id')
        ref = db.reference(f'Teacher/{teacher_id}')
        data = ref.get()
        return render(request, "customAdmin/update_profile.html", {'teacher': data})
    return redirect('admin_teacher')


@AdminDeco
def update_teacher_profile(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        batch = request.POST.get('batch')
        gender = request.POST.get('gender')

        ref = db.reference(f'Teacher/')
        ref.child(teacher_id).update({
            'name': name,
            'gender': gender,
            'batch': batch,
            'email': email,
        })
        messages.success(request, "Profile Updated Successfully")
    return redirect('admin_teacher')


@AdminDeco
def view_request(request):
    id = request.POST.get('id')
    data = db.reference(f"Reported-Attendance/Checked/{id}").get()
    return render(request, "customAdmin/Request_Attend.html", {'data': data, 'id': id})


@AdminDeco
def update_Attend(request):
    if request.method == "POST":
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        roll = request.POST.get('roll_no')
        date = request.POST.get('date')
        status = request.POST.get('status')
        id = request.POST.get('id')
        ref = db.reference(f"Attendance/{id}/")
        child = ref.child(roll).get()
        ref_report = db.reference(f"Reported-Attendance/Checked/{id}/{date}/")
        if status == 'Present':
            if child:
                total = child['total_attendance'] + 1
                ref.child(roll).update(
                    {date: {'last_attendance_time': current_time,
                            'topics_covered': 'Admin'},
                     'total_attendance': total}
                )
                ref_report.child(roll).delete()
                messages.success(request, "Updated records")
            else:
                ref.update(
                    {roll: {date:
                                {'last_attendance_time': current_time,
                                 'topics_covered': 'Admin-Added'},
                            'total_attendance': 1}
                    }
                )
                ref_report.child(roll).delete()
                messages.success(request, "Created record Successfully")
        else:
            total = child['total_attendance']
            if total is not None:
                if total == 1:
                    ref.child(roll).delete()
                    ref_report.child(roll).delete()
                    messages.success(request, "Updated records")
                else:
                    ref.child(roll).child(date).delete()
                    ref.child(roll).update({'total_attendance': total - 1})
                    ref_report.child(roll).delete()
                    messages.success(request, "Updated records")
            else:
                messages.error(request, "No Record Present for this student")
    return redirect("admin_teacher")


@AdminDeco
def criminal(request):
    data = db.reference("Criminal/").get
    return render(request, "customAdmin/criminal.html", {'data': data})


@AdminDeco
def fetch_data(request):
    if request.method == 'POST':
        method = request.POST.get('method')

        if method == 'api':
            end_count = int(request.POST.get('end_count'))
            start_count = 529  # You can modify this to be dynamic if needed
            # Call the function to fetch and store data
            fetch_data_store(start_count, end_count)
            messages.success(request, "API Fetching Completed")
            return redirect('criminal')

        elif method == 'manual':
            return redirect('add_criminal')

    return redirect("criminal")


@AdminDeco
def start_identify(request):
    run_recognition()
    messages.success(request, "Success")
    return redirect("criminal")


@AdminDeco
def add_criminal(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        parentage = request.POST.get('parentage')
        aliases = request.POST.get('aliases')
        address = request.POST.get('address')
        photo = request.FILES['photo']
        wantedId = request.POST.get('wantedId')
        isDeleted = request.POST.get('isDeleted')

        image_data = photo.read()
        encodings = generate_face_encodings(image_data)

        if encodings:
            # Store encodings in Firebase Realtime Database
            ref = db.reference(f'Criminal/{wantedId}')
            if ref.get():
                messages.error(request, "Wanted_id Already Exists")
                return redirect('criminal')
            else:
                store_encodings(wantedId, encodings)
                original_name = photo.name  # Get the original filename
                save_criminal_image(photo, f"{wantedId}_{original_name}")
                save_criminal_data(
                    Name=name,
                    WantedId=wantedId,
                    Aliases=aliases,
                    Parentage=parentage,
                    Address=address,
                    IsDeleted=isDeleted,
                    Photo=original_name
                )
                messages.success(request, "Criminal Added Successfully")
        else:
            messages.error(request, 'Please provide a proper image.')

    return render(request, "customAdmin/Add_criminals_m.html")


def store_encodings(wanted_id, encodings):
    # Convert NumPy array to a JSON serializable format (list)
    reference = db.reference(f'/Criminal_encoding/{wanted_id}')

    # Convert encodings to lists
    encodings_lists = [encoding.tolist() for encoding in encodings]

    # Store the encodings in Firebase
    reference.set(encodings_lists)


def generate_face_encodings(image_data):
    # Convert image data to a file-like object
    image_stream = io.BytesIO(image_data)

    # Convert image stream to PIL Image
    image_pil = Image.open(image_stream)

    # Convert image to RGB (if not already in RGB format)
    image_rgb = image_pil.convert("RGB")

    # Convert PIL Image to numpy array
    image_np = np.array(image_rgb)

    # Find all face locations in the image
    face_locations = face_recognition.face_locations(image_np)

    # If no face found, return None
    if len(face_locations) == 0:
        return None

    # Generate face encodings
    face_encodings = face_recognition.face_encodings(image_np, face_locations)
    # print(face_encodings)
    return face_encodings


def save_criminal_image(image_data, image_name):
    bucket = storage.bucket()
    folder_path = 'Criminal_img/'

    content_type, _ = mimetypes.guess_type(image_name)
    blob = bucket.blob(folder_path + image_name)

    with image_data.open() as image:
        # Determine the MIME type of the image based on its file extension
        blob.upload_from_file(image, content_type=content_type)
    image_url = blob.public_url

    return image_url


@AdminDeco
def police(request):
    ref = db.reference("Police/")
    data = ref.get()
    return render(request, "customAdmin/police.html", {"data": data})


@AdminDeco
def add_police(request):
    if request.method == "POST":
        police_id = request.POST.get('police_id')
        name = request.POST.get('name')
        contact = request.POST.get('number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        image = request.FILES['photo']
        original_name = f'{police_id}_{image.name}'

        ref = db.reference("Police/")
        # Create a new child node with the student's roll number as the key
        police_ref = ref.child(str(police_id))

        # Set the student data in the Firebase Realtime Database
        police_ref.set({
            'name': name,
            'contact': contact,
            'address': address,
            'city': city,
            'Photo': original_name,
        })

        bucket = storage.bucket()
        folder_path = 'Police_img/'

        content_type, _ = mimetypes.guess_type(original_name)
        blob = bucket.blob(folder_path + original_name)
        image_data = image.read()

        blob.upload_from_string(image_data, content_type=content_type)
        messages.success(request, "Added Successfully")

    return render(request, "customAdmin/Add_Police.html")


@AdminDeco
def admin_logout(request):
    # Remove the 'roll_no' from the session if it exists
    if 'ID' in request.session:
        del request.session['ID']
    # Redirect the user to the login page or any other desired page
    return redirect('admin_login')
