from django.urls import path
from .views import *

urlpatterns = [
    path("", admin_login, name="admin_login"),
    path("admin_logout/", admin_logout, name="admin_logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/admin_student/", admin_student, name="admin_student"),
    path("dashboard/admin_student/update_student/", update_student, name="update_student"),
    path("dashboard/admin_student/update_student/update", update, name="update"),
    path("dashboard/admin_student/delete_student/", delete_student, name="delete_student"),
    path("dashboard/admin_teacher", admin_teacher, name="admin_teacher"),
    path("dashboard/admin_teacher/update_teacher/update_teacher_profile", update_teacher_profile, name="update_teacher_profile"),
    path("dashboard/admin_teacher/update_teacher/", update_teacher, name="update_teacher"),
    path("dashboard/admin_teacher/delete_teacher/", delete_teacher, name="delete_teacher"),
    path("dashboard/admin_teacher/view_request/", view_request, name="view_request"),
    path("dashboard/admin_teacher/view_request/update_Attend/", update_Attend, name="update_Attend"),
    path("dashboard/criminal", criminal, name="criminal"),
    path("dashboard/criminal/fetch_data", fetch_data, name="fetch_data"),
    path("dashboard/criminal/add_criminal", add_criminal, name="add_criminal"),
    path("dashboard/criminal/start_identify", start_identify, name="start_identify"),
    path("dashboard/police", police, name="police"),
    path("dashboard/police/add_police", add_police, name="add_police"),
]
