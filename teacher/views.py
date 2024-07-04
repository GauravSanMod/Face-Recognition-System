from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .decorators import teacher_authenticate
from .main import run_face_recognition
from firebase_admin import db, storage


@teacher_authenticate
def teacher_index(request):
    return render(request, "teacher/index.html")


@teacher_authenticate
def teacher_logout(request):
    # Remove the 'teacher_id' from the session if it exists
    if 'teacher_id' in request.session:
        del request.session['teacher_id']
    # Redirect the user to the login page or any other desired page
    return redirect('Teacher_login')


@teacher_authenticate
def take_attendance(request):
    if request.method == 'POST':
        topic = request.POST.get('topics_covered')
        teacher_id = request.session['teacher_id']
        run_face_recognition(teacher_id, topic)
        messages.success(request, "Attendance Recorded Successfully")
        return redirect('take_attendance')
    return render(request, "teacher/instruction.html")


@teacher_authenticate
def teacher_about(request):
    return render(request, "teacher/about.html")


@teacher_authenticate
def teacher_view(request):
    try:
        teacher_id = request.session['teacher_id']
        # Reference to the teacher's attendance records
        teacher_ref = db.reference(f'Attendance/{teacher_id}/')

        # Get all student roll numbers under the teacher's ID
        student_roll_nos = teacher_ref.get()
        # print(student_roll_nos)
        # Dictionary to store latest attendance data for each student
        latest_attendance_data = {}

        # Iterate through each student's roll number

        for roll_no, attendance_info in student_roll_nos.items():
            if isinstance(attendance_info, dict) and 'total_attendance' in attendance_info:
                # Extract attendance data for the student
                total_attendance = attendance_info['total_attendance']

                student_ref = db.reference(f"Student/{roll_no}/").get()
                name = student_ref['name']

                # Serve image
                image_url = f"/serve_image/{roll_no}"

                # Find the most recent date with attendance records
                latest_date = max(key for key in attendance_info.keys() if key != 'total_attendance')
                # print(latest_date)
                # Extract attendance data for the most recent date
                attendance_data = attendance_info[latest_date]
                # print(attendance_data)

                # Store attendance data in latest_attendance_data dictionary
                latest_attendance_data[roll_no] = {
                    'total_attendance': total_attendance,
                    'date': latest_date,
                    'last_attendance_time': attendance_data.get('last_attendance_time', ''),
                    'topics_covered': attendance_data.get('topics_covered', ''),
                    'image_url': image_url,
                    'name': name
                }

        return render(request, "teacher/viewAttendance.html", {'students': latest_attendance_data})
    except Exception as e:
        # Handle exceptions
        print("Error fetching attendance:", str(e))
        # Return an error page or handle the error as required
        return render(request, "teacher/viewAttendance.html")


def serve_image(request, rollno):
    try:
        # Initialize Firebase Storage client
        bucket = storage.bucket()

        # Get reference to the image file in Firebase Storage
        blob = bucket.blob(f'Images/{rollno}.jpg')

        # Download the image data
        image_data = blob.download_as_string()

        # Set content type
        content_type = blob.content_type

        # Return image as HTTP response
        return HttpResponse(image_data, content_type=content_type)
    except Exception as e:
        print("Error serving image:", str(e))
        return HttpResponse(status=500)  # Return a 500 Internal Server Error


@teacher_authenticate
def teacher_service(request):
    return render(request, "teacher/service.html")


@teacher_authenticate
def teacher_contact(request):
    return render(request, "teacher/contact.html")


@teacher_authenticate
def student_reported(request):
    teacher_id = request.session['teacher_id']
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        action = request.POST.get('action')
        date = request.POST.get('date')
        status = request.POST.get('status')
        if action == 'approve':
            report = db.reference('Reported-Attendance/').child('Checked')
            report.child(teacher_id).child(date).child(roll_no).set({'status': status})
            report = db.reference('Reported-Attendance/').child('Unchecked')
            report.child(teacher_id).child(date).child(roll_no).delete()
            messages.success(request, "Approved Successfully")
        else:
            report = db.reference('Reported-Attendance/').child('Unchecked')
            report.child(teacher_id).child(date).child(roll_no).delete()
            messages.success(request, "Rejected Successfully")

    ref = db.reference(f'Reported-Attendance/Unchecked/{teacher_id}/').get()
    data = {}
    if ref is not None:
        for key, value in ref.items():
            roll_no = list(value.keys())[0]
            stud_data = db.reference(f'Student/{roll_no}/').get()
            status = value[roll_no]
            image_url = f"/serve_image/{roll_no}"
            data[roll_no] = {
                'date': key,
                'name': stud_data['name'],
                'status': status,
                'image_url': image_url
            }

    return render(request, "teacher/student_reported.html", {'data': data})


@teacher_authenticate
def teacher_instruction(request):
    return render(request, "teacher/instruction.html")


@teacher_authenticate
def teacher_add_missing(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        teacher_id = request.session['teacher_id']
        status = request.POST.get('status')
        date = request.POST.get('date')

        report_ref = db.reference('Reported-Attendance/').child('Checked')
        ref = report_ref.child(teacher_id)
        d_ref = ref.child(date)
        d_ref.child(student_id).set({'status': status})
        messages.success(request, "Report Added Successfully")

    return render(request, "teacher/AddMissingAttendance.html")


@teacher_authenticate
def transfer_url(request):
    return redirect('teacher_instruction')
