import pandas as pd
import numpy as np
import re
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.gis.geos import Point
from django.db.models import Count, Sum
from django.shortcuts import render, redirect
from pprint import pprint
from .functions import *
from .models import *
from client.functions import handle_uploaded_files
from datetime import datetime
from sklearn.cluster import KMeans


def index(request):
    if 'type' in request.session and request.session['type'] == 'owner':
        return redirect('/dashboard')

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
    featured_restaurants_dict = []
    featured_restaurants = []

    for restaurant in restaurants:
        reviews = Review.objects.filter(restaurant=restaurant)
        total_ratings = 0
        reviews_amount = 0

        for review in reviews:
            total_ratings += review.rating
            reviews_amount += 1

        average_rating = total_ratings / reviews_amount

        featured_restaurants_dict.append(
            {
                'id': restaurant.id,
                'rating': average_rating
            }
        )

    featured_restaurants_dict = sorted(
        featured_restaurants_dict,
        key=lambda x: x['rating'],
        reverse=True
    )

    for restaurant_dict in featured_restaurants_dict:
        featured_restaurant = Restaurant.objects.get(id=restaurant_dict['id'])
        featured_restaurants.append(featured_restaurant)

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

    restaurants = filter_restaurants(restaurants)

    if restaurants.count() < 5:
        restaurants = Restaurant.objects.order_by('?')

    data['featured_restaurants'] = featured_restaurants[:5]
    data['recommended_restaurants'] = restaurants[:5]

    return render(request, 'client/index.html', data)


def register(request):
    if 'uid' in request.session:
        return redirect('/')

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
                    return redirect('/dashboard')
            except RestaurantOwner.DoesNotExist:
                data['invalid_credentials_error'] = 'Invalid email or password. Please try again.'
                return render(request, 'client/login.html', data)

    return render(request, 'client/login.html')


def logout(request):
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

    del request.session['uid']
    del request.session['type']
    messages.success(
        request, 'You have successfully logged out of your account.')
    return redirect('/login')


def profile(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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
            total_price=data['total'],
            customer_id=data['customer'].id,
            restaurant_id=data['restaurant'].id
        )

        latest_order_id = Order.objects.latest('id').id

        Payment.objects.create(amount=data['total'], order_id=latest_order_id)

        menu_items = data['menu_items']

        for menu_item, quantity in menu_items:
            subtotal = menu_item.price * quantity
            OrderDetail.objects.create(order_id=latest_order_id, menu_item_id=menu_item.id,
                                       quantity=quantity, subtotal_price=subtotal)

        messages.success(request, 'Your order has been placed successfully.')
        return redirect('/')

    return render(request, 'client/payment.html', data)


def order_history(request):
    if 'uid' not in request.session or request.session['type'] == 'owner':
        return redirect('/')

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

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

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

    data = {}

    uid = request.session['uid']
    owner = RestaurantOwner.objects.get(id=uid)
    restaurant = Restaurant.objects.filter(owner_id=uid).first()
    #menu_items = MenuItem.objects.annotate(quantity_orders=Count('orderdetail__quantity')).order_by('-quantity_orders')
    owner.restaurant = restaurant
    data['owner'] = owner
    #data['menu_items'] = menu_items[:10]

    # create a temporary empty list
    temp = []
    item_qtts = []

    # get all menu_items and order_details
    menu_items = MenuItem.objects.all()
    order_details = OrderDetail.objects.all()

    # loop thru menu_items to get menu_items name and store in temp list
    for menu_item in menu_items:
        temp.append(menu_item.name)

    # use set() to eliminate duplicated names, and store in variable names
    names = set(temp)

    # loop thru names and put it in a dictinary (to keep track the qtt for each menu_items name)
    for item in names:
        item_dict = {
            'name': item,
            'qtt': 0
        }
        # store the item_dict in item_qtts list
        item_qtts.append(item_dict)

    # loop thru all the order details, and get all order_detail that matched with menu_item
    for order_detail in order_details:
        menu_item = MenuItem.objects.get(id=order_detail.menu_item_id)
        # loop thru item_qtts list, if the dict's name is matched with the menu_item.name then return index of that item
        index = next((i for i, item in enumerate(item_qtts)
                     if item["name"] == menu_item.name), None)
        # add the quantity of the items_qtts list
        item_qtts[index]['qtt'] += order_detail.quantity

    # return the item in item_qtts with the highest qtt
    sorted_list = sorted(item_qtts, key=lambda x: x['qtt'], reverse=True)

    # show top 10
    data['sorted_list'] = sorted_list[0:10]

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

    # K-Means Clustering Algorithm
    menu_items = MenuItem.objects.all().values()
    order_details = OrderDetail.objects.all().values()

    # reviews_df = pd.DataFrame(reviews)[['id', 'author_id', 'restaurant_id']]
    # sentiments_df = pd.DataFrame(sentiments)[['id', 'super_score']]

    menu_items_df = pd.DataFrame(menu_items)[
        ['id', 'name', 'description', 'price', 'image_url', 'cuisine_id', 'restaurant_id']]
    order_details_df = pd.DataFrame(order_details)[
        ['id', 'quantity', 'subtotal_price', 'menu_item_id', 'order_id']]
    menu_detail = pd.merge(menu_items_df, order_details_df,
                           how='left', left_on='id', right_on='menu_item_id')

    values = {'quantity': 0}
    menu_detail = menu_detail.fillna(value=values)

    # convert menu_detail quantity from float to int
    menu_detail['quantity'] = menu_detail['quantity'].apply(np.int64)

    # choose price and quantity column
    X = menu_detail.iloc[:, [3, 8]].values

    # store in menu_detail_df ,price and qtt columns
    menu_detail_df = pd.DataFrame(X, columns=['price', 'quantity'])

    # config the KMeans to 5 clusters
    kmeans = KMeans(n_clusters=5, init='k-means++', random_state=0)

    # return a label for each data point based on their cluster
    # show the result
    Y = kmeans.fit_predict(X)

    # convert the result into cluster_df
    cluster_df = pd.DataFrame(Y)

    cluster_df.rename(columns={0: 'Cluster'}, inplace=True)

    # print(cluster_df)

    # print(menu_detail_df.info())
    # print(cluster_df)

    result_df = pd.concat([menu_detail_df, cluster_df], axis=1)

    cluster0 = []
    cluster1 = []
    cluster2 = []
    cluster3 = []
    cluster4 = []

    for index in result_df.index:
        cluster = result_df['Cluster'][index]
        result_dict = {
            'id': index+1,
            'price': result_df['price'][index]
        }
        if cluster == 0:
            cluster0.append(result_dict)
        elif cluster == 1:
            cluster1.append(result_dict)
        elif cluster == 2:
            cluster2.append(result_dict)
        elif cluster == 3:
            cluster3.append(result_dict)
        elif cluster == 4:
            cluster4.append(result_dict)

    cluster_min_max = []
    cluster_quantity = [len(cluster0), len(cluster1), len(
        cluster2), len(cluster3), len(cluster4)]

    data['cluster_quantity'] = cluster_quantity
    # print(cluster_quantity)

    cluster0_dict = {
        'min_price':  min(cluster0, key=lambda x: x['price'])['price'],
        'max_price':  max(cluster0, key=lambda x: x['price'])['price']
    }
    cluster1_dict = {
        'min_price':  min(cluster1, key=lambda x: x['price'])['price'],
        'max_price':  max(cluster1, key=lambda x: x['price'])['price']
    }
    cluster2_dict = {
        'min_price':  min(cluster2, key=lambda x: x['price'])['price'],
        'max_price':  max(cluster2, key=lambda x: x['price'])['price']
    }
    cluster3_dict = {
        'min_price':  min(cluster3, key=lambda x: x['price'])['price'],
        'max_price':  max(cluster3, key=lambda x: x['price'])['price']
    }
    cluster4_dict = {
        'min_price':  min(cluster4, key=lambda x: x['price'])['price'],
        'max_price':  max(cluster4, key=lambda x: x['price'])['price']
    }

    cluster_min_max.append(cluster0_dict)
    cluster_min_max.append(cluster1_dict)
    cluster_min_max.append(cluster2_dict)
    cluster_min_max.append(cluster3_dict)
    cluster_min_max.append(cluster4_dict)

    data['cluster'] = zip(cluster_min_max, cluster_quantity)

    return render(request, 'client/malaysia_food_trend.html', data)


def food_trend(request):
    if 'uid' not in request.session or request.session['type'] == 'customer':
        return redirect('/')

    if 'lat' in request.session and 'lng' in request.session:
        del request.session['lat']
        del request.session['lng']

    data = {}

    uid = request.session['uid']
    owner = RestaurantOwner.objects.get(id=uid)
    restaurant = Restaurant.objects.filter(owner_id=uid).first()
    restaurants = Restaurant.objects.all()
    order_details = OrderDetail.objects.all()

    # print(restaurant)

    owner.restaurant = restaurant
    data['owner'] = owner

    # create a temporary empty list
    temp = []
    food_list = []

    # get only menu_items that matched current restaurant
    menu_items = MenuItem.objects.filter(restaurant_id=restaurant.id)
    for menu in menu_items:
        food_list.append(menu.name)

    foodList = set(food_list)

    for item in foodList:
        item_dict = {
            'name': item,
            'qtt': 0
        }
        temp.append(item_dict)

     # loop thru all the order details
    for order_detail in order_details:
        menu_item = MenuItem.objects.get(id=order_detail.menu_item_id)
        index = next((i for i, item in enumerate(temp)
                     if item["name"] == menu_item.name), None)
        if index is not None:
            temp[index]['qtt'] += order_detail.quantity

    sorted_list = sorted(temp, key=lambda x: x['qtt'], reverse=True)
    # pprint(sorted_list)

    data['sorted_list'] = sorted_list

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


def dashboard(request):
    if 'uid' not in request.session or request.session['type'] == 'customer':
        return redirect('/')

    data = {}

    uid = request.session['uid']
    owner = RestaurantOwner.objects.get(id=uid)
    restaurant = Restaurant.objects.filter(owner_id=uid).first()
    hidden = request.POST.get('action')
    #test = MenuItem.objects.exclude(deleted_at__isnull = False)
    print("HHIH")
    menu_items = MenuItem.objects.filter(
        restaurant_id=restaurant.id).filter(deleted_at__isnull=True)

    owner.restaurant = restaurant
    data['owner'] = owner
    data['menu_items'] = menu_items

    orders = Order.objects.filter(restaurant_id=restaurant.id)
    total_sales = orders.aggregate(total_sales=Sum('total_price'))
    total_orders = orders.aggregate(total_orders=Count('id'))

    data['total_sales'] = total_sales['total_sales']
    data['total_orders'] = total_orders['total_orders']

    recommended_price_range = get_recommended_price_range()
    data['recommended_price_range'] = recommended_price_range

    top_restaurant_items = get_top_restaurant_items(restaurant.id)
    data['top_restaurant_items'] = top_restaurant_items

    restaurant_first_menu_item = MenuItem.objects.filter(
        restaurant_id=restaurant.id).first()
    cuisine = Cuisine.objects.get(id=restaurant_first_menu_item.cuisine_id)
    top_cuisine_items = get_top_cuisine_items(cuisine.id)

    # add menu item function
    if request.method == 'POST' and request.POST.get('action') == 'add':
        food_name = request.POST.get('food_name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        food_image = MenuItem(request.POST, request.FILES)

        if len(request.FILES) != 0:
            food_image = request.FILES['food_image']

        MenuItem.objects.create(
            name=food_name, description=description, price=price, image_url=food_image, cuisine_id=cuisine.id, restaurant_id=restaurant.id
        )
        messages.success(request, 'Add menu item success.')
        return redirect('/dashboard')

    # delete function
    if request.method == 'POST':  # and request.POST.get('action') == 'delete':
        menu_item = MenuItem.objects.get(id=hidden)
        currentdatetime = datetime.now()
        menu_item.deleted_at = currentdatetime

        menu_item.save()
        #MenuItem.objects.values(MenuItem_id = hidden)

    data['cuisine'] = cuisine.name
    data['top_cuisine_items'] = top_cuisine_items

    return render(request, 'client/dashboard.html', data)
