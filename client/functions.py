from client.models import Review, SentimentAnalysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
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
