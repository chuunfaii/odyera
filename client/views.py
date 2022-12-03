import pandas as pd
import numpy as np
from django.shortcuts import render
import re
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.shortcuts import render, redirect
from scipy import sparse
from .functions import *
from .models import Customer, RestaurantOwner, Restaurant, Review, MenuItem, Order, OrderDetail, Payment, SentimentAnalysis


def index(request):
    data = {}

    if request.method == 'POST':
        lat = float(request.POST.get('lat'))
        long = float(request.POST.get('long'))
        user_location = Point(long, lat, srid=4326)

        restaurants = Restaurant.objects.annotate(distance=Distance(
            'location', user_location)).order_by('distance')

        request.session['lat'] = lat
        request.session['long'] = long
    elif 'lat' in request.session and 'long' in request.session:
        lat = float(request.session['lat'])
        long = float(request.session['long'])
        user_location = Point(long, lat, srid=4326)

        restaurants = Restaurant.objects.annotate(distance=Distance(
            'location', user_location)).order_by('distance')
    else:
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


def test(request):
    # TODO: Beginning of testing 1
    # !: https://pub.towardsai.net/recommendation-system-in-depth-tutorial-with-python-for-netflix-using-collaborative-filtering-533ff8a0e444
    data = {}
    reviews = Review.objects.all().values()
    reviews_df = pd.DataFrame(reviews)
    sentiments = SentimentAnalysis.objects.all().values()
    sentiments_df = pd.DataFrame(sentiments)
    reviews_df = pd.merge(reviews_df, sentiments_df)

    restaurant_rating_df = reviews_df[[
        'restaurant_id', 'author_id', 'super_score']].copy()

    split_value = int(len(restaurant_rating_df) * 0.80)
    train_data = restaurant_rating_df[:split_value]
    test_data = restaurant_rating_df[split_value:]

    train_sparse_data = get_user_item_sparse_matrix(train_data)
    test_sparse_data = get_user_item_sparse_matrix(test_data)

    global_average_rating = train_sparse_data.sum() / train_sparse_data.count_nonzero()
    # print("Global Average Super Score: {}".format(global_average_rating))

    average_rating_user = get_average_rating(train_sparse_data, True)
    average_rating_restaurant = get_average_rating(train_sparse_data, False)
    # print("Average Rating User: {}".format(average_rating_user))
    # print("Average Rating Restaurant: {}".format(average_rating_restaurant))

    total_users = len(np.unique(restaurant_rating_df['author_id']))
    train_users = len(average_rating_user)
    uncommon_users = total_users - train_users

    # print("Total no. of Users = {}".format(total_users))
    # print("No. of Users in train data= {}".format(train_users))
    # print("No. of Users not present in train data = {}({}%)".format(
    #     uncommon_users, np.round((uncommon_users/total_users)*100), 2))

    total_restaurants = len(np.unique(restaurant_rating_df['restaurant_id']))
    train_restaurants = len(average_rating_restaurant)
    uncommon_restaurants = total_restaurants - train_restaurants

    # print("Total no. of Movies = {}".format(total_restaurants))
    # print("No. of Movies in train data= {}".format(train_restaurants))
    # print("No. of Movies not present in train data = {}({}%)".format(
    #     uncommon_restaurants, np.round((uncommon_restaurants/total_restaurants)*100), 2))

    compute_user_similarity(train_sparse_data, 3)

    data['reviews_df'] = restaurant_rating_df.to_html()
    return render(request, 'client/test.html', data)
    # TODO: End of testing 1


def test2(request):
    # TODO: Beginning of testing 2
    # !: https://www.youtube.com/watch?v=3ecNC-So0r4
    data = {}

    reviews = Review.objects.all().values()
    sentiments = SentimentAnalysis.objects.all().values()

    reviews_df = pd.DataFrame(reviews)[['id', 'author_id', 'restaurant_id']]
    reviews_df.rename(columns={'author_id': 'user_id'})

    sentiments_df = pd.DataFrame(
        sentiments)[['id', 'super_score', 'review_id']]

    ratings_df = reviews_df.merge(sentiments_df)

    ratings_df = ratings_df.pivot_table(
        index='author_id', columns='restaurant_id', values='super_score')

    ratings_df = ratings_df.fillna(0)

    ratings_std_df = ratings_df.apply(standardize)

    user_similarity = cosine_similarity(ratings_std_df)

    user_similarity_df = pd.DataFrame(
        user_similarity, index=ratings_df.index, columns=ratings_df.index)

    print(get_similar_users(user_similarity_df, 1))

    data['ratings_df'] = user_similarity_df.to_html()

    return render(request, 'client/test2.html', data)
    # TODO: End of testing 2


def test3(request):
    # TODO: Beginning of testing 3
    # !: https://colab.research.google.com/drive/1cN44RlIEaB28FTD30qFiHkN3rqcDgcng?usp=sharing#scrollTo=qJii6XAXNdUL
    data = {}

    reviews = Review.objects.all().values()
    sentiments = SentimentAnalysis.objects.all().values()

    reviews_df = pd.DataFrame(reviews)[['id', 'author_id', 'restaurant_id']]
    sentiments_df = pd.DataFrame(sentiments)[['id', 'super_score']]

    ratings_df = reviews_df.merge(sentiments_df)

    # create user-item matrix
    user_item_matrix = ratings_df.pivot_table(
        index='author_id', columns='restaurant_id', values='super_score')

    # data normalization
    user_item_matrix_norm = user_item_matrix.subtract(
        user_item_matrix.mean(axis=1), axis='rows')

    # identify similar users
    user_similarity = user_item_matrix_norm.T.corr()

    # pick a user id
    picked_user_id = 1

    # remove picked user id from the candidate list
    user_similarity.drop(index=picked_user_id, inplace=True)

    # number of similar users
    n = 1

    # user similarity threshold
    user_similarity_threshold = 0.3

    # get top n similar users
    similar_users = user_similarity[user_similarity[picked_user_id] >
                                    user_similarity_threshold][picked_user_id].sort_values(ascending=False)[:n]

    # print out top n similar users
    print(f'The similar users for user {picked_user_id} are', similar_users)

    data['test'] = user_similarity.to_html()

    return render(request, 'client/test3.html', data)
    # TODO: End of testing 3
