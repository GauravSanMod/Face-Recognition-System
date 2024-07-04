import mimetypes
import re
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from firebase_admin import db, storage
import face_recognition
from PIL import Image
import io
import numpy as np
import datetime


# Create your views here.
def Student_login(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')

        # Retrieve student's data from Firebase Realtime Database
        student_ref = db.reference(f'Student/{roll_no}')
        # print(f"Firebase reference path: Students/{roll_no}")
        student_data = student_ref.get()
        # print("Retrieved student data:", student_data)

        if student_data is not None and 'password' in student_data:
            student_password = student_data['password']

            if student_password == password:
                # Authentication successful, store student's roll number in session
                request.session['roll_no'] = roll_no
                messages.success(request, 'Login successful!')
                return redirect('stud_index')

        # No matching student found or incorrect credentials
        messages.error(request, 'Invalid roll number or password.')

    return render(request, "accounts/Student-login.html")


def Student_register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        roll_no = request.POST.get('roll-no')
        batch = request.POST.get('batch')
        gender = request.POST.get('gender')
        address = request.POST.get('address')

        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,18}$'

        # Check if the password matches the regex pattern
        if not re.search(pattern, password):
            raise ValidationError(
                "The password must contain at least one lowercase letter, one uppercase letter, "
                "one digit, one special character, and be at least 8-18 characters long."
            )

        # Save image to Firebase Storage
        image = request.FILES['image']
        image_data = image.read()
        original_name = image.name  # Get the original filename
        extension = original_name.split('.')[-1]  # Extract the extension
        image_name = f"{roll_no}.{extension}"  # Append the extension to roll number

        # Generate encodings from image data
        encodings = generate_face_encodings(image_data)

        if encodings:
            # Store encodings in Firebase Realtime Database
            store_encodings(roll_no, encodings)
        else:
            messages.error(request, 'Please provide a proper image.')
            return render(request, 'accounts/Student-register.html')

        save_image_to_firebase(image, image_name)
        # Save data to Firebase RealTime Database
        if save_student_to_firebase(name, email, password, roll_no, batch, address, gender):
            messages.success(request, 'Registration successful!')
            return redirect('Student_login')  # Redirect to student login page
        else:
            messages.error(request, 'Student with this roll no already exists.')
            return render(request, 'accounts/Student-register.html')

    return render(request, 'accounts/Student-register.html')


def save_image_to_firebase(image_field, image_name):
    # Reference to Firebase Storage bucket
    bucket = storage.bucket()
    # Specify the folder path within Firebase Storage
    folder_path = 'Images/'

    content_type, _ = mimetypes.guess_type(image_name)

    # Upload image to Firebase Storage
    blob = bucket.blob(folder_path + image_name)
    with image_field.open() as image:
        # Determine the MIME type of the image based on its file extension
        blob.upload_from_file(image, content_type=content_type)

    # Get public URL of uploaded image
    image_url = blob.public_url

    return image_url


def save_student_to_firebase(name, email, password, roll_no, batch, address, gender):
    # Reference to the Firebase Realtime Database
    ref = db.reference('Student')

    # Check if student with the same roll number already exists
    # existing_student = ref.order_by_child('roll_no').equal_to(str(roll_no)).get()
    # if existing_student:
    #     # Student with the same roll number already exists, return False or raise an exception
    #     return False

    # Create a new child node with the student's roll number as the key
    student_ref = ref.child(str(roll_no))

    # Set the student data in the Firebase Realtime Database
    student_ref.set({
        'name': name,
        'email': email,
        'password': password,
        'roll_no': roll_no,
        'batch': batch,
        'address': address,
        'gender': gender,
    })

    return True


def Teacher_register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        teacher_id = request.POST.get('id')
        batch = request.POST.get('batch')
        gender = request.POST.get('gender')

        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,18}$'

        # Check if the password matches the regex pattern
        if not re.search(pattern, password):
            raise ValidationError(
                "The password must contain at least one lowercase letter, one uppercase letter, "
                "one digit, one special character, and be at least 8-18 characters long."
            )

        # Save image to Firebase Storage
        image = request.FILES['image']
        original_name = image.name  # Get the original filename
        extension = original_name.split('.')[-1]  # Extract the extension
        image_name = f"{teacher_id}.{extension}"  # Create unique filename
        save_teacher_image_to_firebase(image, image_name)

        # Save data to Firebase RealTime Database
        if save_teacher_to_firebase(name, email, password, teacher_id, batch, gender):
            return redirect('Teacher_login')  # Redirect to teacher login page
        else:
            messages.error(request, 'Teacher with this roll no already exists.')
            return render(request, 'accounts/Teacher-register.html')

    return render(request, "accounts/Teacher-register.html")


def save_teacher_image_to_firebase(image_field, image_name):
    # Reference to Firebase Storage bucket
    bucket = storage.bucket()
    # Specify the folder path within Firebase Storage
    folder_path = 'teacher_images/'

    content_type, _ = mimetypes.guess_type(image_name)

    # Upload image to Firebase Storage
    blob = bucket.blob(folder_path + image_name)
    with image_field.open() as image:
        # Determine the MIME type of the image based on its file extension
        blob.upload_from_file(image, content_type=content_type)

    # Get public URL of uploaded image
    image_url = blob.public_url

    return image_url


def save_teacher_to_firebase(name, email, password, teacher_id, batch, gender):
    # Reference to the Firebase Realtime Database
    ref = db.reference('Teacher')

    # Check if student with the same roll number already exists
    # existing_teacher = ref.order_by_child('teacher_id').equal_to(str(teacher_id)).get()
    # if existing_teacher:
    #     # Student with the same roll number already exists, return False or raise an exception
    #     return False

    # Create a new child node with the student's roll number as the key
    teacher_ref = ref.child(str(teacher_id))

    # Set the student data in the Firebase Realtime Database
    teacher_ref.set({
        'name': name,
        'email': email,
        'password': password,
        'teacher_id': teacher_id,
        'batch': batch,
        'gender': gender,
    })
    return True


def Teacher_login(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('id')
        password = request.POST.get('password')

        # Retrieve student's data from Firebase Realtime Database
        teacher_ref = db.reference(f'Teacher/{teacher_id}')
        teacher_data = teacher_ref.get()

        if teacher_data is not None and 'password' in teacher_data:
            teacher_password = teacher_data['password']

            if teacher_password == password:
                # Authentication successful, store student's roll number in session
                request.session['teacher_id'] = teacher_id
                messages.success(request, 'Login successful!')
                return redirect('teacher_index')

        # No matching student found or incorrect credentials
        messages.error(request, 'Invalid id number or password.')
    return render(request, "accounts/Teacher-login.html")


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


# Function to store encodings in Firebase database
def store_encodings(student_id, encodings):
    # Convert NumPy array to a JSON serializable format (list)
    reference = db.reference(f'/Encoding/{student_id}')

    # Convert encodings to lists
    encodings_lists = [encoding.tolist() for encoding in encodings]

    # Store the encodings in Firebase
    reference.set(encodings_lists)
