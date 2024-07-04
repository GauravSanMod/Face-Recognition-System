from django.shortcuts import render
from firebase_admin import db


def index(request):
    ref = db.reference("Feedback/")
    data = ref.get()
    data_list = []
    for name, details in data.items():
        rating = int(details['rating'])
        filled_stars = ['filled' for _ in range(rating)]
        empty_stars = ['empty' for _ in range(5 - rating)]
        stars = filled_stars + empty_stars
        data_list.append({'name': name, 'description': details['description'], 'stars': stars})
    return render(request, "home/index.html", {'data': data_list})


def about(request):
    return render(request, "home/about.html")


def contact(request):
    return render(request, "home/contact.html")


def services(request):
    return render(request, "home/services.html")
