import pandas as pd
from client.models import *
from django.contrib.gis.db.models.functions import Distance
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob


def calculate_super_score_all():
    reviews = Review.objects.all()

    for review in reviews:
        review_rating = round(review.rating)
        polarity_score = calculate_polarity_score(review)
        compound_score = calculate_compound_score(review)

        super_score = review_rating + polarity_score * compound_score

        SentimentAnalysis.objects.create(
            polarity_score=polarity_score,
            compound_score=compound_score,
            super_score=super_score,
            review_id=review.id
        )


def calculate_super_score(review):
    review_rating = round(review.rating)
    polarity_score = calculate_polarity_score(review)
    compound_score = calculate_compound_score(review)

    super_score = review_rating + polarity_score * compound_score

    SentimentAnalysis.objects.create(
        polarity_score=polarity_score,
        compound_score=compound_score,
        super_score=super_score,
        review_id=review.id
    )


def calculate_polarity_score(review):
    res = TextBlob(review.text)
    polarity_score = res.sentiment.polarity
    return round(polarity_score)


def calculate_compound_score(review):
    sia = SentimentIntensityAnalyzer()
    polarity_scores = sia.polarity_scores(review.text)
    compound_score = polarity_scores['compound']
    print(compound_score)
    return round(compound_score)


def get_recommended_restaurants(user_id):
    reviews = Review.objects.all().values()
    sentiments = SentimentAnalysis.objects.all().values()

    reviews_df = pd.DataFrame(reviews)[['id', 'author_id', 'restaurant_id']]
    sentiments_df = pd.DataFrame(sentiments)[['id', 'super_score']]

    ratings_df = reviews_df.merge(sentiments_df)

    # Create a User-Item matrix.
    # - The rows of the matrix are users (user_id), and the columns of the matrix are restaurants (restaurant_id).
    # - The value of the matrix is the super score of the restaurant's review if there is a review written by the user. Otherwise, it shows 'NaN'.
    user_item_matrix = ratings_df.pivot_table(
        index='author_id',
        columns='restaurant_id',
        values='super_score'
    )

    # Identify similar users.
    # - Calculate the user similarity matrix using Pearson correlation.
    # - T property is used to transpose index and columns of the dataframe first.
    # - Then, the corr() method is used to find the pairwise correlation of all columns in the dataframe (Pearson correlation).
    user_similarity = user_item_matrix.T.corr()

    # Remove current user id from the candidate list.
    user_similarity.drop(index=user_id, inplace=True)

    # Setting a user similarity threshold.
    # - As user-based collaborative filtering makes recommendations based on similar users, a positive threshold is needed to be set.
    # - Setting a 0.1 as the threshold means that a user must have a Pearson correlation coefficient of at least 0.1 to be considered as a similar user.
    user_similarity_threshold = 0.1

    # Retrieve similar users.
    # - Sort the user similarity values from the highest to the lowest.
    similar_users = user_similarity[user_similarity[user_id] >
                                    user_similarity_threshold][user_id].sort_values(ascending=False)

    # Keep the restaurants that the current user has reviewed.
    # - Keep only the row where the `user_id` matches the current user id in the User-Item matrix.
    # - Remove any restaurants that have missing values (no super score).
    user_id_reviewed = user_item_matrix[user_item_matrix.index == user_id].dropna(
        axis=1, how='all')

    # Keep only the similar users' restaurants.
    # - Keep the user ids that were in the similar user lists.
    # - Remove the restaurants with all missing values.
    # - All missing values for a restaurant means none of the similar users have reviewed the restaurant before.
    similar_user_restaurants = user_item_matrix[user_item_matrix.index.isin(
        similar_users.index)].dropna(axis=1, how='all')

    # Remove the reviewed restaurants from the restaurant list.
    similar_user_restaurants.drop(
        user_id_reviewed.columns, axis=1, inplace=True, errors='ignore')

    # Retrieve the final ranked item scores from the `calculate_ranked_item_score` method.
    ranked_item_score = calculate_ranked_item_score(
        similar_user_restaurants, similar_users)

    restaurant_ids = ranked_item_score['restaurant_id'].tolist()

    restaurants = Restaurant.objects.filter(id__in=restaurant_ids)

    return restaurants


def sort_restaurants_based_closest_location(restaurants, user_location):
    return restaurants.annotate(distance=Distance('location', user_location)).order_by('distance')


def calculate_ranked_item_score(similar_user_restaurants, similar_users):
    item_score = {}
    TOP = 10

    for restaurant in similar_user_restaurants.columns:
        total = 0
        count = 0

        restaurant_super_score = similar_user_restaurants[restaurant]

        for u in similar_users.index:
            # Check if the restaurant has a super score = if the user has reviewed it.
            if pd.isna(restaurant_super_score[u]) == False:
                # Score is the sum of the user similarity score multiply by the restaurant super score.
                score = similar_users[u] * restaurant_super_score[u]
                total += score
                count += 1
        # Get the average score for the item.
        item_score[restaurant] = total / count

    item_score = pd.DataFrame(item_score.items(), columns=[
        'restaurant_id', 'restaurant_score'])

    # Sort the restaurants by restaurants similarity score.
    ranked_item_score = item_score.sort_values(
        by='restaurant_score', ascending=False)

    return ranked_item_score.head(TOP)


def password_check(password):
    errors = []

    if type(password) is not str:
        return errors

    if len(password) < 6:
        errors.append('Password should be at least 6 characters.')

    if len(password) > 20:
        errors.append('Password should not be greater than 20 characters.')

    if not any(char.isdigit() for char in password):
        errors.append('Password should have at least one numeral.')

    if not any(char.isupper() for char in password):
        errors.append('Password should have at least one uppercase letter.')

    if not any(char.islower() for char in password):
        errors.append('Password should have at least one lowercase letter.')

    return errors
