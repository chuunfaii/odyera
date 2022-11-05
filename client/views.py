from django.shortcuts import HttpResponse, render
import pyrebase

config = {
    "apiKey": "AIzaSyCWI61KjoayJaYBabohGqxZTBztuv-Nmc4",
    "authDomain": "odyera-ee197.firebaseapp.com",
    "databaseURL": "https://odyera-ee197-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "projectId": "odyera-ee197",
    "storageBucket": "odyera-ee197.appspot.com",
    "messagingSenderId": "97850537863",
    "appId": "1:97850537863:web:78aa399ca115cf6c3bc522",
    "measurementId": "G-LQ14FN9B7R"
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth()
database = firebase.database()


def index(request):
    return HttpResponse("Hello, world. You're at the client index.")


def register(request):
    firstName = database.child('customer1').child('firstName').get().val()
    lastName = database.child('customer1').child('lastName').get().val()
    return render(request, "client/register.html", {"first_name": firstName, "last_name": lastName})


def postRegister(request):
    firstName = request.POST.get('first_name')
    lastName = request.POST.get('last_name')
    return render(request, "client/test.html", {"first_name": firstName, "last_name": lastName})


def login(request):
    return HttpResponse('This is the login page.')
