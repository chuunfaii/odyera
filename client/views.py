import pandas as pd
import re
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.gis.geos import Point
from django.shortcuts import render, redirect
from .functions import *
from .models import *


def index(request):
    data = {}

    has_location = False

    if 'lat' in request.session and 'lng' in request.session:
        lat = float(request.session['lat'])
        lng = float(request.session['lng'])
        has_location = True
    elif request.method == 'POST':
        lat = float(request.POST.get('lat'))
        lng = float(request.POST.get('lng'))
        request.session['lat'] = lat
        request.session['lng'] = lng
        has_location = True

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

    restaurants = Restaurant.objects.all()

    if has_location:
        user_location = Point(lng, lat, srid=4326)

        if 'uid' in request.session and request.session['type'] == 'customer':
            try:
                restaurants = get_recommended_restaurants(uid)

                if restaurants.count() < 5:
                    restaurants = Restaurant.objects.all()
            except:
                pass

        restaurants = sort_restaurants_based_closest_location(
            restaurants, user_location)

    data['restaurants'] = restaurants[:5]

    return render(request, 'client/index.html', data)


def register(request):
    if 'uid' in request.session:
        return redirect('/')

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

    del request.session['uid']
    del request.session['type']
    messages.success(
        request, 'You have successfully logged out of your account.')
    return redirect('/login')


def profile(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
        reviews = Review.objects.filter(
            restaurant_id=id, author_id=customer.id
        )
        if reviews:
            messages.warning(
                request, 'You have already posted a review for this restaurant.'
            )
        else:
            review = request.POST.get('review')
            rating = request.POST.get('rating')
            Review.objects.create(rating=rating, text=review,
                                  author_id=customer.id, restaurant_id=id)
            review = Review.objects.latest('id')
            calculate_super_score(review)
            messages.success(
                request, 'You have posted your review for this restaurant.'
            )

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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
    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

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


def order_history(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

    data = {}

    uid = request.session['uid']
    customer = Customer.objects.get(id=uid)
    data['customer'] = customer

    orders = Order.objects.filter(customer_id=uid)

    restaurants = []
    order_details = []

    for order in orders:
        order_items = OrderDetail.objects.filter(order_id=order.id)
        items = []
        restaurant = None
        for order_item in order_items:
            item = MenuItem.objects.get(id=order_item.menu_item_id)
            items.append({
                'quantity': order_item.quantity,
                'subtotal': order_item.quantity * item.price,
                'item': item
            })
            restaurant = Restaurant.objects.get(id=item.restaurant_id)
        order_details.append(items)
        restaurants.append(restaurant)

    data['orders'] = zip(orders, order_details, restaurants)

    return render(request, 'client/order_history.html', data)


def malaysia_food_trend(request):
    if 'uid' not in request.session or request.session['type'] == 'customer':
        return redirect('/')

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

    data = {}

    uid = request.session['uid']
    owner = RestaurantOwner.objects.get(id=uid)
    restaurant = Restaurant.objects.filter(owner_id=uid).first()
    owner.restaurant = restaurant
    data['owner'] = owner

    if request.method == 'GET' and request.GET.get('m'):
        m = request.GET.get('m')

        if m == 'all':
            month = 'All Time'
        elif m == 'jan':
            month = 'January'
        elif m == 'feb':
            month = 'February'
        elif m == 'mar':
            month = 'March'
        elif m == 'apr':
            month = 'April'
        elif m == 'may':
            month = 'May'
        elif m == 'jun':
            month = 'June'
        elif m == 'jul':
            month = 'July'
        elif m == 'aug':
            month = 'August'
        elif m == 'sep':
            month = 'September'
        elif m == 'oct':
            month = 'October'
        elif m == 'nov':
            month = 'November'
        elif m == 'dec':
            month = 'December'

        data['m'] = m
        data['month'] = month

    return render(request, 'client/malaysia_food_trend.html', data)


def food_trend(request):
    if 'uid' not in request.session or request.session['type'] == 'customer':
        return redirect('/')

    if 'lat' in request.session and 'long' in request.session:
        del request.session['lat']
        del request.session['long']

    data = {}

    uid = request.session['uid']
    owner = RestaurantOwner.objects.get(id=uid)
    restaurant = Restaurant.objects.filter(owner_id=uid).first()
    owner.restaurant = restaurant
    data['owner'] = owner

    if request.method == 'GET' and request.GET.get('m'):
        m = request.GET.get('m')

        if m == 'all':
            month = 'All Time'
        elif m == 'jan':
            month = 'January'
        elif m == 'feb':
            month = 'February'
        elif m == 'mar':
            month = 'March'
        elif m == 'apr':
            month = 'April'
        elif m == 'may':
            month = 'May'
        elif m == 'jun':
            month = 'June'
        elif m == 'jul':
            month = 'July'
        elif m == 'aug':
            month = 'August'
        elif m == 'sep':
            month = 'September'
        elif m == 'oct':
            month = 'October'
        elif m == 'nov':
            month = 'November'
        elif m == 'dec':
            month = 'December'

        data['m'] = m
        data['month'] = month

    return render(request, 'client/food_trend.html', data)


def error_404(request, exception):
    return render(request, '404.html')
