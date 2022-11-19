import re
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
        if Customer.objects.filter(email_address=email_address).exists():
            errors['existing_email_error'] = 'Email already exists. Please try another one.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errors:
            data['errors'] = errors
            return render(request, 'client/register.html', data)

        # Register a new customer account into the database
        Customer.objects.create(
            first_name=first_name, last_name=last_name, email_address=email_address, password=make_password(password))
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
            customer = Customer.objects.get(email_address=email_address)
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
        messages.success(
            request, 'You have successfully logged out of your account.')
    except:
        pass
    return redirect('/login')


def profile(request):
    # If a user is not logged in, redirect back to homepage
    if 'uid' not in request.session:
        return redirect('/')

    data = {}
    errors = {}

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    data['customer'] = customer

    # Only goes through if the user is making a POST request via submitting the form
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')

        # Copy a Customer instance
        tempCustomer = Customer.objects.get(id=uid)
        tempCustomer.first_name = first_name
        tempCustomer.last_name = last_name
        tempCustomer.email_address = email_address

        data['tempCustomer'] = tempCustomer

        # Compares whether password and password confirmation match
        if password != password_confirmation:
            errors['password_confirmation_error'] = 'Password and password confirmation do not match.'

        # Checks whether email address already exists in the database
        if Customer.objects.filter(email_address=email_address).exclude(id=uid).exists():
            errors['existing_email_error'] = 'Email already exists. Please try another one.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errors:
            data['errors'] = errors
            return render(request, 'client/profile.html', data)

        # Checks if the hashed password in the database matches the entered password
        is_matched = check_password(password, customer.password)
        if not is_matched:
            data['invalid_password_error'] = 'Invalid password. Please try again.'
            return render(request, 'client/profile.html', data)
        else:
            customer.first_name = first_name
            customer.last_name = last_name
            customer.email_address = email_address
            customer.save()
            messages.success(
                request, 'Changes have been made to your profile successfully.')
            return render(request, 'client/profile.html', data)
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/profile.html', data)


def password(request):
    # If a user is not logged in, redirect back to homepage
    if 'uid' not in request.session:
        return redirect('/')

    data = {}
    errors = {}

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    data['customer'] = customer

    # Only goes through if the user is making a POST request via submitting the form
    if request.method == 'POST':
        password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        password_confirmation = request.POST.get('password_confirmation')

        # Validates password using custom regex checking function
        password_validation_errors = password_check(new_password)
        if len(password_validation_errors) != 0:
            errors['password_validation_errors'] = password_validation_errors

        # Compares whether password and password confirmation match
        if new_password != password_confirmation:
            errors['password_confirmation_error'] = 'New password and password confirmation do not match.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errors:
            data['errors'] = errors
            return render(request, 'client/password.html', data)

        # Checks if the hashed password in the database matches the entered password
        is_matched = check_password(password, customer.password)
        if not is_matched:
            data['invalid_password_error'] = 'Invalid password. Please try again.'
            return render(request, 'client/password.html', data)
        else:
            customer.password = make_password(new_password)
            customer.save()
            messages.success(
                request, 'Your password has been updated successfully.')
            return render(request, 'client/password.html', data)
    # Everything else goes through here, which only renders the page and nothing else
    else:
        return render(request, 'client/password.html', data)


def restaurants(request):
    return render(request, 'client/restaurants.html')


def restaurant(request, id):
    return render(request, 'client/restaurant.html')


def menu(request, id):
    return render(request, 'client/menu.html')


def order(request, id):
    return render(request, 'client/order.html')


def payment(request):
    data = {}
    errors = {}

    if request.method == 'POST':
        card_no = request.POST.get('card_no')
        expiration_date = request.POST.get('expiration_date')
        cvv = request.POST.get('cvv')
        postal_code = request.POST.get('postal_code')

        data['card_no'] = card_no
        data['expiration_date'] = expiration_date
        data['cvv'] = cvv
        data['postal_code'] = postal_code

        # Regex patterns for credit card number, expiration date, CVV and Malaysia's postal code
        card_no_pattern = re.compile(r"^4[0-9]{12}(?:[0-9]{3})?$")
        expiration_date_pattern = re.compile(
            r"^(0[1-9]|1[0-2])\/?([0-9]{4}|[0-9]{2})$")
        cvv_pattern = re.compile(r"^[0-9]{3,4}$")
        postal_code_pattern = re.compile(r"^[0-9]{5}$")

        if not re.fullmatch(card_no_pattern, card_no):
            errors['invalid_card_error'] = 'Invalid credit card number.'

        if not re.fullmatch(expiration_date_pattern, expiration_date):
            errors['invalid_expiration_date_error'] = 'Invalid card expiration date.'

        if not re.fullmatch(cvv_pattern, cvv):
            errors['invalid_cvv_error'] = 'Invalid CVV.'

        if not re.fullmatch(postal_code_pattern, postal_code):
            errors['invalid_postal_error'] = 'Invalid postal code.'

        # If there are error messages, re-renders the page with the already filled in user account details and error messages
        if errors:
            data['errors'] = errors
            return render(request, 'client/payment.html', data)

        messages.success(request, 'Your order has been placed successfully.')
        return redirect('/')
    else:
        return render(request, 'client/payment.html')


def foodTrend_whole(request):
    return render(request, 'client/foodTrend_whole.html')


def foodTrend_particular(request):
    return render(request, 'client/foodTrend_particular.html')
