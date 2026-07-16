import os
import time

import pandas as pd
import requests
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

Read_Books = "read_books.csv"
if os.path.exists(Read_Books):
      readbooks_df = pd.read_csv(Read_Books)
else:
      readbooks_df = pd.DataFrame(columns=["Author", "Genre", "Title", "Description"])

API_KEY = 'AIzaSyCeN559Baiped_ewrXn8a2P9rGfBsPj7Mo'
BASE_URL = 'https://www.googleapis.com/books/v1/volumes'

def search_single_book(title):  # Search API to get book info
    if not title or not str(title).strip():
        return None

    cleaned_title = str(title).strip()
    queries = [
        cleaned_title,
        f'intitle:"{cleaned_title}"',
        f'"{cleaned_title}"',
    ]

    for query in queries:
        for attempt in range(3):
            try:
                response = requests.get(
                    BASE_URL,
                    params={'q': query, 'key': API_KEY, 'maxResults': 5},
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0'},
                )
                if response.status_code == 200:
                    items = response.json().get('items', [])
                    if items:
                        volume_info = items[0].get('volumeInfo', {})
                        title_value = volume_info.get('title')
                        if title_value:
                            return {
                                'title': title_value,
                                'category': (volume_info.get('categories') or ['Fiction'])[0],
                                'description': volume_info.get('description', ''),
                            }
                elif response.status_code in {429, 500, 503}:
                    time.sleep(1)
                    continue
            except Exception as e:
                print(f"Search error: {e}")
                time.sleep(1)

    return None

def fetch_similar_category_books(category): # Get Books with similar genre/topic
    # We query by subject (genre) and fetch up to 10 candidates
    params = {
        'q': f'subject:"{category}"',
        'key': API_KEY,
        'maxResults': 10
    }
    books_list = [] # list of similar books
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            for item in items:
                info = item['volumeInfo']
                if info.get('description'): # We need descriptions to cluster!
                    books_list.append({
                        'Title': info.get('title'),
                        'Description': info.get('description')
                    })
    except Exception as e:
        print(f"Error fetching category pool: {e}")
    return books_list

def run_dynamic_recommender():
    user_input = input("Enter a book you recently read: ")
    
    # Get book details from the API
    target_book = search_single_book(user_input)
    if not target_book:
        print("Couldn't find that book. Try Again")
        return
        
    print(f"\nFound your book: '{target_book['title']}'")
    print(f"Detected Category: {target_book['category']}")
    print("Finding similar books from the API...")
    
    # Get similar books in that genre
    candidate_pool = fetch_similar_category_books(target_book['category'])
    if not candidate_pool:
        print("Could not find other books in this category.")
        return
        
    # Append our target book to the list so we can include it in the math
    candidate_pool.append({
        'Title': target_book['title'],
        'Description': target_book['description']
    })
    
    # 3. Create our DataFrame
    df = pd.DataFrame(candidate_pool).drop_duplicates(subset=['Title'])
    
    # 4. Cluster the dynamic pool
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df['Description'])
    
    # Group into 3 sub-themes
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
    df['Cluster'] = kmeans.fit_predict(X)
    
    # User's cluster
    target_cluster = df[df['Title'] == target_book['title']]['Cluster'].values[0]
    
    # 6. Recommend other books in that exact cluster!
    recommendations = df[(df['Cluster'] == target_cluster) & (df['Title'] != target_book['title'])]
    
    print("\n=======================================================")
    print(f"🎯 RECOMMENDED FOR YOU {target_book['title']}")
    print("=======================================================")
    if not recommendations.empty:
        print(recommendations.head().to_string(index=False))
    else:
        # Fallback: recommend anything from the same category pool
        fallback = df[df['Title'] != target_book['title']].head(3)
        print(fallback.to_string(index=False))


if __name__ == "__main__":
    run_dynamic_recommender()