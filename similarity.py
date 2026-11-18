from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(new_project, old_projects):

    if len(old_projects) == 0:
        return 0.0

    documents = [new_project]

    documents.extend(old_projects)

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf[0:1], tfidf[1:])

    highest = similarity.max()

    return round(highest * 100, 2)