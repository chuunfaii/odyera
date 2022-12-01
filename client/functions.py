from textblob import TextBlob
from client.models import Review, SentimentAnalysis


def calculate_super_score_all():
    reviews = Review.objects.all()
    polarity_scores = []

    for review in reviews:
        polarity_score = calculate_polarity_score(review)
        polarity_scores.append(polarity_score)

    print(polarity_scores)


def calculate_polarity_score(review):
    res = TextBlob(review.text)
    polarity_score = res.sentiment.polarity
    return round(polarity_score)


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
