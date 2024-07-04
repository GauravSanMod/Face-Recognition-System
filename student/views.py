from django.contrib import messages
from django.shortcuts import render, redirect
from .decorators import student_authenticated
from firebase_admin import db


@student_authenticated
def track_attend(request):
    if request.method == 'POST':
        stud_id = request.session['roll_no']
        teacher_id = request.POST.get('teacher_id')
        teacher_ref = db.reference(f'Attendance/{teacher_id}/')
        if teacher_ref.get() is not None:
            att_ref = db.reference(f'Attendance/{teacher_id}/{stud_id}/')
            data = att_ref.get()
            stu_ref = db.reference(f'Student/{stud_id}/')
            stu_data = stu_ref.get()
            tea_ref = db.reference(f'Teacher/{teacher_id}/')
            t_data = tea_ref.get()
            t_name = t_data['name']
            name = stu_data['name']
            total = data['total_attendance']
            att_data = []
            if data:
                for key, info in data.items():
                    if key != 'total_attendance':
                        last = info['last_attendance_time']
                        topic = info['topics_covered']
                        att_data.append({'date': key, 'last': last, 'topic': topic})
                # print(att_data)
                return render(request, "student/track_att.html",
                              {'data': att_data, 'total': total, 'name': name, 't_name': t_name})

            else:
                messages.error(request, 'No Attendance Record Found')
                return render(request, "student/track_att.html")

        else:
            messages.error(request, 'Please provide correct Teacher ID')
            return render(request, "student/track_att.html")

    return render(request, "student/track_att.html")


@student_authenticated
def report_attend(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        date = request.POST.get('date')
        ref = db.reference(f'Teacher/{teacher_id}').get()
        if ref is not None:
            stud_id = request.session['roll_no']
            report = db.reference('Reported-Attendance/').child('Unchecked')
            report.child(teacher_id).child(date).child(stud_id).set("Present")
            messages.success(request, "Reported Successfully")
            return render(request, "student/report.html")
        else:
            messages.error(request, "Enter Proper Teacher ID")
            return render(request, "student/report.html")
    return render(request, "student/report.html")


@student_authenticated
def stud_index(request):
    return render(request, "student/index.html")


@student_authenticated
def stud_about(request):
    return render(request, "student/about.html")


@student_authenticated
def stud_service(request):
    return render(request, "student/service.html")


@student_authenticated
def stud_contact(request):
    return render(request, "student/contact.html")


@student_authenticated
def feedback(request):
    if request.method == 'POST':
        roll = request.session['roll_no']
        desc = request.POST.get('description')
        rating = request.POST.get('rating')
        ref = db.reference("Feedback/")
        name = db.reference(f"Student/{roll}/name").get()
        ref.set({
            name: {
                'description': desc,
                'rating': rating
            }
        })

    return render(request, "student/feedback.html")


@student_authenticated
def student_logout(request):
    # Remove the 'roll_no' from the session if it exists
    if 'roll_no' in request.session:
        del request.session['roll_no']
    # Redirect the user to the login page or any other desired page
    return redirect('Student_login')
