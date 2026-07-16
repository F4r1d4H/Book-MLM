import os
import time

import pandas as pd
import requests
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


def display(value):
    print(value)

Read_Books = "read_books.csv"
if os.path.exists(Read_Books):
      readbooks_df = pd.read_csv(Read_Books)
else:
      readbooks_df = pd.DataFrame(columns=["authors", "genre", "title"])

API_KEY = 'AIzaSyCeN559Baiped_ewrXn8a2P9rGfBsPj7Mo'
BASE_URL = 'https://www.googleapis.com/books/v1/volumes'

def search_single_book(title): # Search API to get book info
    if not title or not str(title).strip():
        return None

    cleaned_title = str(title).strip()
    queries = [
        cleaned_title,
        f'intitle:{cleaned_title}',
        f'intitle:"{cleaned_title}"',
    ]

    for query in queries:
        for attempt in range(3):
            params = {'q': query, 'key': API_KEY, 'maxResults': 5, 'langRestrict': 'en'}
            try:
                response = requests.get(BASE_URL, params=params, timeout=10)
                if response.status_code == 200:
                    items = response.json().get('items', [])
                    for item in items:
                        volume_info = item.get('volumeInfo', {})
                        title_value = volume_info.get('title')
                        if title_value and cleaned_title.lower() in title_value.lower():
                            authors_list = volume_info.get('authors', ['Unknown Author'])
                            book_genre = (volume_info.get('categories') or ['Fiction'])[0]
                            return {
                                'title': title_value,
                                'authors': authors_list[0] if authors_list else 'Unknown Author',
                                'genre': book_genre,
                                'category': book_genre,
                                'description': volume_info.get('description', ''),
                            }
                elif response.status_code in {429, 500, 503}:
                    time.sleep(1 + attempt)
                    continue
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

    return None

def fetch_similar_category_books(category): # Get Books with similar genre/topic
    if not category or not str(category).strip():
        category = 'fiction'

    original_category = str(category).strip()
    search_terms = [original_category]

    if ' ' in original_category:
        search_terms.extend([part for part in original_category.replace('-', ' ').split() if part])

    if search_terms[0] != 'fiction':
        search_terms.append('fiction')
    if search_terms[0] != 'nonfiction':
        search_terms.append('nonfiction')

    for term in search_terms:
        params = {
            'q': f'subject:"{term}"',
            'key': API_KEY,
            'maxResults': 10,
            'langRestrict': 'en'
        }
        books_list = []
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                items = response.json().get('items', [])
                for item in items:
                    info = item.get('volumeInfo', {})
                    if info.get('description'):
                        books_list.append({
                            'title': info.get('title'),
                            'description': info.get('description')
                        })
                if books_list:
                    return books_list
        except Exception as e:
            print(f"Error fetching category pool: {e}")

    broader_params = {
        'q': original_category,
        'key': API_KEY,
        'maxResults': 10,
        'langRestrict': 'en'
    }
    try:
        response = requests.get(BASE_URL, params=broader_params, timeout=10)
        if response.status_code == 200:
            items = response.json().get('items', [])
            books_list = []
            for item in items:
                info = item.get('volumeInfo', {})
                if info.get('description'):
                    books_list.append({
                        'title': info.get('title'),
                        'description': info.get('description')
                    })
            return books_list
    except Exception as e:
        print(f"Error fetching broader category pool: {e}")

    return []

def run_dynamic_recommender():
    user_input = input("Enter a book you recently read: ")

    # Get book details from the API
    target_book = search_single_book(user_input)
    if not target_book:
        print("Couldn't find that book. Try Again")
        return

    print(f"\nFound your book: '{target_book['title']}'")
    readbooks_df.loc[len(readbooks_df)] = [target_book['authors'], target_book['genre'], target_book['title']]
    print(f"Detected Category: {target_book['category']}")
    print("Finding similar books from the API...")

    # Get similar books in that genre
    candidate_pool = fetch_similar_category_books(target_book['category'])
    if not candidate_pool:
        print("Could not find other books in this category.")
        return

    # Append our target book to the list so we can include it in the math
    candidate_pool.append({
        'title': target_book['title'],
        'description': target_book['description']
    })

    # 3. Create our DataFrame
    df = pd.DataFrame(candidate_pool).drop_duplicates(subset=['title'])

    # 4. Cluster the dynamic pool
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df['description'])

    # Group into 3 sub-themes
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
    df['Cluster'] = kmeans.fit_predict(X)

    # User's cluster
    target_cluster = df[df['title'] == target_book['title']]['Cluster'].values[0]

    # 6. Recommend other books in that exact cluster!
    recommendations = df[(df['Cluster'] == target_cluster) & (df['title'] != target_book['title'])]

    print("\n=======================================================")
    print(f"🎯 RECOMMENDED FOR YOU {target_book['title']}")
    print("=======================================================")
    if not recommendations.empty:
        display(recommendations.head())
    else:
        # Fallback: recommend anything from the same category pool
        fallback = df[df['title'] != target_book['title']].head(3)
        display(fallback)


if __name__ == "__main__":
    run_dynamic_recommender()