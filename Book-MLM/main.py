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
      if 'owned' not in readbooks_df.columns:
            readbooks_df['owned'] = False
      else:
            readbooks_df['owned'] = readbooks_df['owned'].fillna(False).astype(bool)
      if 'rating' not in readbooks_df.columns:
            readbooks_df['rating'] = None
else:
      readbooks_df = pd.DataFrame(columns=["authors", "genre", "title", 'owned', 'rating'])


def deduplicate_read_books():
    global readbooks_df
    if readbooks_df.empty:
        return

    readbooks_df = readbooks_df.copy()
    readbooks_df['title_key'] = readbooks_df['title'].fillna('').astype(str).str.strip().str.lower()
    readbooks_df = readbooks_df.drop_duplicates(subset=['title_key'], keep='last').drop(columns=['title_key'])
    readbooks_df.to_csv(Read_Books, index=False)


deduplicate_read_books()

# --- NEW: Read Later Persistence ---
Read_Later = "read_later.csv"
if os.path.exists(Read_Later):
      readlater_df = pd.read_csv(Read_Later)
else:
      readlater_df = pd.DataFrame(columns=["authors", "genre", "title"])


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

def show_read_books():
    deduplicate_read_books()
    if readbooks_df.empty:
        return pd.DataFrame(columns=["authors", "genre", "title", "owned", "rating"])
    return readbooks_df.reindex(columns=["authors", "genre", "title", "owned", "rating"])


def clear_saved_lists():
    global readbooks_df, readlater_df

    readbooks_df = pd.DataFrame(columns=["authors", "genre", "title", "owned", "rating"])
    readlater_df = pd.DataFrame(columns=["authors", "genre", "title"])

    readbooks_df.to_csv(Read_Books, index=False)
    readlater_df.to_csv(Read_Later, index=False)

    return show_read_books(), show_read_later()

# --- NEW: Helper Functions for Read Later ---
def show_read_later():
    global readlater_df
    if readlater_df.empty:
        return pd.DataFrame(columns=["authors", "genre", "title"])
    return readlater_df.reindex(columns=["authors", "genre", "title"])

def save_to_read_later(book_title):
    global readlater_df
    if not book_title or not str(book_title).strip():
        return show_read_later()
    
    # Check if it's already in the list
    if not readlater_df.empty and book_title.lower() in readlater_df['title'].str.lower().values:
        return show_read_later()
        
    # Fetch book info to get its metadata before saving
    book_info = search_single_book(book_title)
    if book_info:
        new_row = {
            'authors': book_info['authors'],
            'genre': book_info['genre'],
            'title': book_info['title']
        }
    else:
        new_row = {
            'authors': 'Unknown',
            'genre': 'Unknown',
            'title': book_title
        }
        
    readlater_df.loc[len(readlater_df)] = new_row
    readlater_df.to_csv(Read_Later, index=False)
    return show_read_later()


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

def run_dynamic_recommender(user_input, owned=False, book_rating=None):
    if not user_input or not str(user_input).strip():
        return pd.DataFrame({"Message": ["Please enter a book title to get recommendations."]})

    target_book = search_single_book(user_input)
    if not target_book:
        return pd.DataFrame({"Message": ["Couldn't find that book. Please try a different title."]})

    if 'rating' not in readbooks_df.columns:
        readbooks_df['rating'] = None

    title_matches = readbooks_df['title'].astype(str).str.lower() == str(target_book['title']).lower()
    if title_matches.any():
        existing_index = readbooks_df.index[title_matches][0]
        readbooks_df.at[existing_index, 'owned'] = owned
        readbooks_df.at[existing_index, 'rating'] = book_rating
        readbooks_df.at[existing_index, 'authors'] = target_book['authors']
        readbooks_df.at[existing_index, 'genre'] = target_book['genre']
    else:
        readbooks_df.loc[len(readbooks_df)] = {
            'authors': target_book['authors'],
            'genre': target_book['genre'],
            'title': target_book['title'],
            'owned': owned,
            'rating': book_rating,
        }

    readbooks_df.to_csv(Read_Books, index=False)

    deduplicate_read_books()

    candidate_pool = fetch_similar_category_books(target_book['category'])
    if not candidate_pool:
        return pd.DataFrame({"Message": ["Could not find other books in this category."]})

    candidate_pool.append({
        'title': target_book['title'],
        'description': target_book['description']
    })

    df = pd.DataFrame(candidate_pool).drop_duplicates(subset=['title'])
    if df.empty:
        return pd.DataFrame({"Message": ["No recommendations available at the moment."]})

    if len(df) >= 2:
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(df['description'].fillna(''))

        n_clusters = min(3, len(df))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        df['Cluster'] = kmeans.fit_predict(X)

        target_cluster = df[df['title'] == target_book['title']]['Cluster'].values[0]
        recommendations = df[(df['Cluster'] == target_cluster) & (df['title'] != target_book['title'])]
    else:
        recommendations = pd.DataFrame(columns=df.columns)

    if not recommendations.empty:
        return recommendations[['title' , 'description']].rename(columns={'title': 'Recommended Books'}).reset_index(drop=True)

    fallback = df[df['title'] != target_book['title']].head(3)
    if not fallback.empty:
        return fallback[['title' , 'description']].rename(columns={'title': 'Recommended Books (Fallback)'}).reset_index(drop=True)

    return pd.DataFrame({"Message": ["No recommendations available at the moment."]})