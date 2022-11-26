import re
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from .functions import password_check
from .models import Customer, RestaurantOwner, Restaurant, Review, MenuItem, Order, OrderDetail, Payment


def index(request):
    data = {}

    restaurants = Restaurant.objects.all()
    data['restaurants'] = restaurants

    if 'uid' in request.session:
        uid = request.session['uid']

        if request.session['type'] == 'customer':
            customer = Customer.objects.get(id=uid)
            data['customer'] = customer
        else:
            owner = RestaurantOwner.objects.get(id=uid)
            restaurant = Restaurant.objects.filter(owner_id=uid).first()
            owner.restaurant = restaurant
            data['owner'] = owner

    return render(request, 'client/index.html', data)


def register(request):
    if 'uid' in request.session:
        return redirect('/')

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

        password_validation_errors = password_check(password)
        if len(password_validation_errors) > 0:
            errors['password_validation_errors'] = password_validation_errors

        if password != password_confirmation:
            errors['password_confirmation_error'] = 'Password and password confirmation do not match.'

        if Customer.objects.filter(email_address=email_address).exists() or RestaurantOwner.objects.filter(email_address=email_address):
            errors['existing_email_error'] = 'Email already exists. Please try another one.'

        if errors:
            data['errors'] = errors
            return render(request, 'client/register.html', data)

        Customer.objects.create(
            first_name=first_name, last_name=last_name, email_address=email_address, password=make_password(password))
        messages.success(request, 'You have successfully created an account.')
        return redirect('/login')

    return render(request, 'client/register.html')


def login(request):
    if 'uid' in request.session:
        return redirect('/')

    if request.method == 'POST':
        data = {}

        email_address = request.POST.get('email_address')
        password = request.POST.get('password')

        data['email_address'] = email_address

        try:
            customer = Customer.objects.get(email_address=email_address)

            is_matched = check_password(password, customer.password)
            if not is_matched:
                data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
                return render(request, 'client/login.html', data)
            else:
                uid = customer.id
                request.session['uid'] = uid
                request.session['type'] = 'customer'
                messages.success(
                    request, 'You have successfully logged into your account.')
                return redirect('/')
        except Customer.DoesNotExist:
            try:
                owner = RestaurantOwner.objects.get(
                    email_address=email_address)

                is_matched = check_password(
                    password, owner.password)
                if not is_matched:
                    data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
                    return render(request, 'client/login.html', data)
                else:
                    uid = owner.id
                    request.session['uid'] = uid
                    request.session['type'] = 'owner'
                    messages.success(
                        request, 'You have successfully logged into your account.')
                    return redirect('/')
            except RestaurantOwner.DoesNotExist:
                data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
                return render(request, 'client/login.html', data)

    return render(request, 'client/login.html')


def logout(request):
    del request.session['uid']
    del request.session['type']
    messages.success(
        request, 'You have successfully logged out of your account.')
    return redirect('/login')


def profile(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    data = {}
    errors = {}

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    data['customer'] = customer

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email_address')
        password = request.POST.get('password')
        password_confirmation = request.POST.get('password_confirmation')

        tempCustomer = Customer.objects.get(id=uid)
        tempCustomer.first_name = first_name
        tempCustomer.last_name = last_name
        tempCustomer.email_address = email_address

        data['tempCustomer'] = tempCustomer

        if password != password_confirmation:
            errors['password_confirmation_error'] = 'Password and password confirmation do not match.'

        if Customer.objects.filter(email_address=email_address).exclude(id=uid).exists():
            errors['existing_email_error'] = 'Email already exists. Please try another one.'

        if errors:
            data['errors'] = errors
            return render(request, 'client/profile.html', data)

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

    return render(request, 'client/profile.html', data)


def password(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    data = {}
    errors = {}

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    data['customer'] = customer

    if request.method == 'POST':
        password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        password_confirmation = request.POST.get('password_confirmation')

        password_validation_errors = password_check(new_password)
        if len(password_validation_errors) != 0:
            errors['password_validation_errors'] = password_validation_errors

        if new_password != password_confirmation:
            errors['password_confirmation_error'] = 'New password and password confirmation do not match.'

        if errors:
            data['errors'] = errors
            return render(request, 'client/password.html', data)

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

    return render(request, 'client/password.html', data)


def restaurants(request):
    data = {}

    restaurants = Restaurant.objects.order_by('?')
    details = []

    if request.method == 'GET' and request.GET.get('q'):
        query = request.GET.get('q')
        data['query'] = query
        restaurants = Restaurant.objects.filter(name__icontains=query)

    for restaurant in restaurants:
        reviews = Review.objects.filter(restaurant_id=restaurant.id)
        total_ratings = 0
        reviews_amount = 0

        for review in reviews:
            total_ratings += review.rating
            reviews_amount += 1

        average_rating = total_ratings / reviews_amount

        details.append(
            {
                'average_rating': average_rating,
                'reviews_amount': reviews_amount
            }
        )

    restaurant_extras = zip(restaurants, details)
    data['restaurant_extras'] = restaurant_extras

    if 'uid' in request.session:
        uid = request.session['uid']

        if request.session['type'] == 'customer':
            customer = Customer.objects.get(id=uid)
            data['customer'] = customer
        else:
            owner = RestaurantOwner.objects.get(id=uid)
            restaurant = Restaurant.objects.filter(owner_id=uid).first()
            owner.restaurant = restaurant
            data['owner'] = owner

    return render(request, 'client/restaurants.html', data)


def restaurant(request, id):
    data = {}

    if 'uid' in request.session:
        uid = request.session['uid']

        if request.session['type'] == 'customer':
            customer = Customer.objects.get(id=uid)
            data['customer'] = customer
        else:
            owner = RestaurantOwner.objects.get(id=uid)
            restaurant = Restaurant.objects.filter(owner_id=uid).first()
            owner.restaurant = restaurant
            data['owner'] = owner

    if request.method == 'POST':
        review = request.POST.get('review')
        rating = request.POST.get('rating')
        Review.objects.create(rating=rating, text=review,
                              author_id=customer.id, restaurant_id=id)
        messages.success(
            request, 'You have posted your review for this restaurant.')

    restaurant = Restaurant.objects.get(id=id)
    reviews = Review.objects.filter(restaurant_id=id)

    total_ratings = 0
    ratings_amount = 0

    for review in reviews:
        total_ratings += review.rating
        ratings_amount += 1

    data['restaurant'] = restaurant
    data['reviews'] = reviews
    data['average_rating'] = total_ratings / ratings_amount
    data['ratings_amount'] = ratings_amount

    return render(request, 'client/restaurant.html', data)


def menu(request, id):
    data = {}

    if 'uid' in request.session:
        uid = request.session['uid']

        if request.session['type'] == 'customer':
            customer = Customer.objects.get(id=uid)
            data['customer'] = customer
        else:
            owner = RestaurantOwner.objects.get(id=uid)
            restaurant = Restaurant.objects.filter(owner_id=uid).first()
            owner.restaurant = restaurant
            data['owner'] = owner

    restaurant = Restaurant.objects.get(id=id)
    reviews = Review.objects.filter(restaurant_id=id)
    menu_items = MenuItem.objects.filter(restaurant_id=id)

    total_ratings = 0
    ratings_amount = 0

    for review in reviews:
        total_ratings += review.rating
        ratings_amount += 1

    data['restaurant'] = restaurant
    data['menu_items'] = menu_items
    data['average_rating'] = total_ratings / ratings_amount

    return render(request, 'client/menu.html', data)


def order(request, id):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect(f'/restaurant/{id}/menu')

    if request.method == 'POST':
        data = {}

        uid = request.session['uid']
        customer = Customer.objects.get(id=uid)
        data['customer'] = customer

        restaurant = Restaurant.objects.get(id=id)
        reviews = Review.objects.filter(restaurant_id=id)

        total_ratings = 0
        ratings_amount = 0

        for review in reviews:
            total_ratings += review.rating
            ratings_amount += 1

        menu_items = []
        quantities = []
        indiv_subtotals = []
        subtotal = 0

        for key, value in request.POST.items():
            if key != 'csrfmiddlewaretoken':
                quantity = int(value)
                menu_item = MenuItem.objects.get(id=int(key))
                indiv_subtotal = menu_item.price * quantity
                subtotal += float(indiv_subtotal)
                if quantity > 0:
                    menu_items.append(menu_item)
                    quantities.append(quantity)
                    indiv_subtotals.append(indiv_subtotal)

        tax = subtotal * 0.06
        total = subtotal + tax

        data['restaurant'] = restaurant
        data['average_rating'] = total_ratings / ratings_amount
        data['menu_items'] = zip(menu_items, quantities, indiv_subtotals)
        data['subtotal'] = subtotal
        data['tax'] = tax
        data['total'] = total

        return render(request, 'client/order.html', data)

    return redirect(f'/restaurant/{id}/menu')


def payment(request, id):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect(f'/restaurant/{id}menu')

    data = {}
    errors = {}

    menu_items = []
    quantities = []

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    restaurant = Restaurant.objects.get(id=id)

    for key, value in request.POST.items():
        if key.isnumeric():
            quantity = int(value)
            menu_item = MenuItem.objects.get(id=int(key))

            quantities.append(quantity)
            menu_items.append(menu_item)

    data['customer'] = customer
    data['restaurant'] = restaurant
    data['menu_items'] = zip(menu_items, quantities)
    data['total'] = request.POST.get('total')

    if request.method == 'POST' and request.META.get('HTTP_REFERER').endswith('payment'):
        card_no = request.POST.get('card_no')
        expiration_date = request.POST.get('expiration_date')
        cvv = request.POST.get('cvv')
        postal_code = request.POST.get('postal_code')

        data['card_no'] = card_no
        data['expiration_date'] = expiration_date
        data['cvv'] = cvv
        data['postal_code'] = postal_code

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

        if errors:
            data['errors'] = errors
            return render(request, 'client/payment.html', data)

        Order.objects.create(
            total_price=data['total'], customer_id=data['customer'].id)

        latest_order_id = Order.objects.latest('id').id

        Payment.objects.create(amount=data['total'], order_id=latest_order_id)

        menu_items = data['menu_items']

        for menu_item, quantity in menu_items:
            print('inside for loop')
            print(menu_item)
            print(quantity)
            subtotal = menu_item.price * quantity
            OrderDetail.objects.create(order_id=latest_order_id, menu_item_id=menu_item.id,
                                       quantity=quantity, subtotal_price=subtotal)

        messages.success(request, 'Your order has been placed successfully.')
        return redirect('/')

    return render(request, 'client/payment.html', data)


def foodTrend_whole(request):
    return render(request, 'client/foodTrend_whole.html')


def foodTrend_particular(request):
    return render(request, 'client/foodTrend_particular.html')


def order_history(request):
    return render(request, 'client/order_history.html')


def report_whole(request):
    return render(request, 'client/report_whole.html')


def report_particular(request):
    return render(request, 'client/report_particular.html')
