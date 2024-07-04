"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from accounts.views import *
from home.views import *
from student.views import *
from teacher.views import *
from customAdmin.views import serve_teacher_image, serve_criminal_image
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", include('customAdmin.urls')),
    path("default-admin/", admin.site.urls),
    path("", index, name="index"),
    path("contact", contact, name="contact"),
    path("about", about, name="about"),
    path("services", services, name="services"),
    path("Student_login", Student_login, name="Student_login"),
    path("student_logout", student_logout, name="student_logout"),
    path("Student_register", Student_register, name="Student_register"),
    path("Teacher_login", Teacher_login, name="Teacher_login"),
    path("teacher_logout", teacher_logout, name="teacher_logout"),
    path("Teacher_register", Teacher_register, name="Teacher_register"),
    path("stud_index", stud_index, name="stud_index"),
    path("stud_about", stud_about, name="stud_about"),
    path("feedback", feedback, name="feedback"),
    path("stud_contact", stud_contact, name="stud_contact"),
    path("stud_service", stud_service, name="stud_service"),
    path("track_attend", track_attend, name="track_attend"),
    path("report_attend", report_attend, name="report_attend"),
    path('serve_image/<int:rollno>/', serve_image, name='serve_image'),
    path('serve_teacher_image/<int:teacher_id>/', serve_teacher_image, name='serve_teacher_image'),
    path('serve_criminal_image/<int:wanted_id>/<str:photo>/', serve_criminal_image, name='serve_criminal_image'),
    path("teacher_index", teacher_index, name="teacher_index"),
    path("teacher_about", teacher_about, name="teacher_about"),
    path("teacher_contact", teacher_contact, name="teacher_contact"),
    path("teacher_service", teacher_service, name="teacher_service"),
    path("instruction", teacher_instruction, name="teacher_instruction"),
    path("teacher_add_missing", teacher_add_missing, name="teacher_add_missing"),
    path("student_reported", student_reported, name="student_reported"),
    path("take_attendance", take_attendance, name="take_attendance"),
    path("teacher_view", teacher_view, name="teacher_view"),
    path("transfer_url", transfer_url, name="transfer_url"),
]
