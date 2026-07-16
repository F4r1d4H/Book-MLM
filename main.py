import requests
import numpy as np

# Define your API key and the base Google Books URL
API_KEY = 'AIzaSyCeN559Baiped_ewrXn8a2P9rGfBsPj7Mo'
BASE_URL = 'https://www.googleapis.com/books/v1/volumes'

BOLD = '\033[1m'
RESET = '\033[0m'



def search_book(title):
    # 1. Clean the user's input
    clean_title = title.strip()
    
    # 2. Set up the parameters dictionary. 
    # Python will automatically encode spaces and special characters safely!
    params = {
        'q': clean_title,
        'key': API_KEY,
        'maxResults': 1
    }
    
    # 3. Add headers to prevent Google from thinking you are a bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    try:
        # Make the GET request, passing BOTH params and headers
        response = requests.get(BASE_URL, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data:
                book_info = data['items'][0]['volumeInfo']
                
                # Extract key details
                book_data = {
                    'title': book_info.get('title', 'Unknown Title'),
                    'authors': book_info.get('authors', ['Unknown Author']),
                    'genres': book_info.get('categories', ['Uncategorized']),
                    'description': book_info.get('description', 'No description available.'),
                    'cover_image': book_info.get('imageLinks', {}).get('thumbnail', 'No cover image available')
                }
                return book_data
            else:
                print("No books found matching that title.")
                return None
        else:
            print(f"Error connecting to Google API: {response.status_code}")
            # If Google sends an error message, let's print it to see why!
            try:
                print(response.json())
            except:
                pass
            return None
            
    except Exception as e:
        print(f"An exception occurred: {e}")
        return None



# --- Test the function below, just need to test smth out
while True:
    if __name__ == "__main__":
        search_query_raw = input("Enter the book title to search for: ")
        search_query_cleaned = search_query_raw.strip()
        
        # Run the search
        result = search_book(search_query_cleaned)
        
    if result:
        print("\n====================================")
        print("✨ BOOK FOUND ✨")
        print("====================================")
        print(f"{BOLD}Title:{RESET} {result['title']}")
        print(f"{BOLD}Author(s):{RESET} {', '.join(result['authors'])}")
        print(f"{BOLD}Genres:{RESET} {', '.join(result['genres'])}")
        print(f"\n{BOLD}Description:{RESET}\n{result['description'][:200]}...") # Printing just the first 200 chars
        print("====================================")