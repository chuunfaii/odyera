from client.models import Review, SentimentAnalysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
from textblob import TextBlob
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity


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


def get_user_item_sparse_matrix(df):
    sparse_data = sparse.csr_matrix(
        (df.super_score, (df.author_id, df.restaurant_id)))
    return sparse_data


def get_average_rating(sparse_matrix, is_user):
    ax = 1 if is_user else 0
    sum_of_ratings = sparse_matrix.sum(axis=ax).A1
    no_of_ratings = (sparse_matrix != 0).sum(axis=ax).A1
    rows, cols = sparse_matrix.shape
    average_ratings = {i: sum_of_ratings[i] / no_of_ratings[i]
                       for i in range(rows if is_user else cols) if no_of_ratings[i] != 0}
    return average_ratings


def compute_user_similarity(sparse_matrix, limit=100):
    row_index, col_index = sparse_matrix.nonzero()
    rows = np.unique(row_index)
    similar_arr = np.zeros(61700).reshape(617, 100)

    for row in rows[:limit]:
        sim = cosine_similarity(
            sparse_matrix.getrow(row), sparse_matrix).ravel()
        similar_indices = sim.argsort()[-limit:]
        similar = sim[similar_indices]
        similar_arr[row] = similar

    return similar_arr


def standardize(row):
    new_row = (row - row.mean()) / (row.max() - row.min())
    return new_row


def get_similar_users(user_similarity_df, user_id):
    similar_score = user_similarity_df[user_id]
    similar_score = similar_score.sort_values(ascending=False)
    return similar_score


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
