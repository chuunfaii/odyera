from django.shortcuts import HttpResponse, render, redirect
from .functions import password_check
import pyrebase

config = {
    'apiKey': 'AIzaSyCWI61KjoayJaYBabohGqxZTBztuv-Nmc4',
    'authDomain': 'odyera-ee197.firebaseapp.com',
    'databaseURL': 'https://odyera-ee197-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'projectId': 'odyera-ee197',
    'storageBucket': 'odyera-ee197.appspot.com',
    'messagingSenderId': '97850537863',
    'appId': '1:97850537863:web:78aa399ca115cf6c3bc522',
    'measurementId': 'G-LQ14FN9B7'
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
database = firebase.database()


def index(request):
    return render(request, 'client/index.html')


def register(request):
    # If a user is already logged in, redirect back to homepage
    if 'uid' in request.session:
        return redirect('/')

    # Only goes through if the user is making a POST request via submitting the form
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email_address': email_address
        }
        errorsDict = {}

        # Validates password using custom regex checking function
        password_validation_errors = password_check(password)
        if len(password_validation_errors) != 0:
            errorsDict['password_validation_errors'] = password_validation_errors

        # Compares whether password and password confirmation match
        if password != password_confirmation:
            errorsDict['password_confirmation_error'] = 'Password and password confirmation do not match.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errorsDict:
            data['errors'] = errorsDict
            return render(request, 'client/register.html', data)

        # Try registering a new user account into Firebase Authentication
        try:
            user = auth.create_user_with_email_and_password(
                email_address, password)
            uid = user['localId']
            database.child('customers').child(uid).set(data)
            return redirect('/login')
        # Fails if the email entered already exists in the Firebase Authentication database
        except:
            errorsDict['existing_email_error'] = 'Email already exists. Please try another one.'
            data['errors'] = errorsDict
            return render(request, 'client/register.html', data)
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/register.html')


def login(request):
    # If a user is already logged in, redirect back to homepage
    if 'uid' in request.session:
        return redirect('/')

    # Only goes through if the user is making a POST request via submitting the form
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')
        data = {
            'email_address': email_address
        }

        # Try logging into the user account by comparing account details from Firebase Authentication
        try:
            user = auth.sign_in_with_email_and_password(
                email_address, password)
        # Fails if no email address and/or password match with the stored accounts in Firebase Authentication
        except:
            data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
            return render(request, 'client/login.html', data)
        # Stores logged in user account details into current session
        uid = user['localId']
        user = database.child('customers').child(uid).get().val()
        request.session['uid'] = str(uid)
        request.session['user'] = user
        return redirect('/')
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/login.html')


def logout(request):
    try:
        del request.session['uid']
        del request.session['user']
    except:
        pass
    return redirect('/login')


def account(request):
    # If a user is not logged in, redirect back to homepage
    if 'uid' not in request.session:
        return redirect('/')

    # Only goes through if the user is making a POST request via submitting the form
    if request.method == 'POST':
        uid = request.session['uid']
        old_email_address = request.session.user.email_address
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')
        errorsDict = {}

        # Compares whether password and password confirmation match
        if password != password_confirmation:
            errorsDict['password_confirmation_error'] = 'Password and password confirmation do not match.'

        try:
            user = auth.sign_in_with_email_and_password(
                old_email_address, password)
        except:
            errorsDict['invalid_credentials_error'] = 'Incorrect password. Please try again.'
            return render(request, 'client/account.html')
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/account.html')
