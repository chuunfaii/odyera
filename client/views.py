from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from .functions import password_check
from .models import Customer


def index(request):
    data = {}

    # If a customer is already logged in, retrieve the customer details
    if 'uid' in request.session:
        uid = request.session['uid']
        customer = Customer.objects.get(id=uid)
        data['customer'] = customer
        return render(request, 'client/index.html', data)

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
        errors = {}

        # Validates password using custom regex checking function
        password_validation_errors = password_check(password)
        if len(password_validation_errors) != 0:
            errors['password_validation_errors'] = password_validation_errors

        # Compares whether password and password confirmation match
        if password != password_confirmation:
            errors['password_confirmation_error'] = 'Password and password confirmation do not match.'

        # Checks whether email address already exists in the database
        if Customer.objects.filter(email=email_address).exists():
            errors['existing_email_error'] = 'Email already exists. Please try another one.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errors:
            data['errors'] = errors
            return render(request, 'client/register.html', data)

        # Register a new customer account into the database
        hashed_password = make_password(password)
        Customer.objects.create(
            first_name=first_name, last_name=last_name, email=email_address, password=hashed_password)
        messages.success(request, 'You have successfully created an account.')
        return redirect('/login')
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

        try:
            customer = Customer.objects.get(email=email_address)
            # Checks if the hashed password in the database matches the entered password
            is_matched = check_password(password, customer.password)
            if not is_matched:
                data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
                return render(request, 'client/login.html', data)
            else:
                uid = customer.id
                request.session['uid'] = uid
                messages.success(
                    request, 'You have successfully logged into your account.')
                return redirect('/')
        except Customer.DoesNotExist:
            data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
            return render(request, 'client/login.html', data)
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/login.html')


def logout(request):
    try:
        del request.session['uid']
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
        errors = {}

        # Compares whether password and password confirmation match
        if password != password_confirmation:
            errors['password_confirmation_error'] = 'Password and password confirmation do not match.'

        try:
            user = auth.sign_in_with_email_and_password(
                old_email_address, password)
        except:
            errors['invalid_credentials_error'] = 'Incorrect password. Please try again.'
            return render(request, 'client/account.html')
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/account.html')


def restaurant_list(request):
    return render(request, 'client/restaurant_list.html')
