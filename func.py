import requests
from deep_translator import GoogleTranslator
import langid

translator_en = GoogleTranslator(source='ru', target='en')
translator_ru = GoogleTranslator(source='en', target='ru')

def auto_translate_resp(resp):
    if langid.classify(resp)[0] != "en":
        try:
            translated_text = translator_en.translate(resp)
            resp = translated_text
        except Exception as e:
            print(f"Translation error: {e}")
    return resp

api_key = "API KEY"
resp = input("Введите название фильма: ")
resp = auto_translate_resp(resp)
print(resp)
url = f'http://www.omdbapi.com/?s={resp}&apikey={api_key}'

response = requests.get(url)
data = response.json()

# Получить список всех фильмов
movies = data['Search']
print(movies)



def print_movie_details(movie_list, index):
    if index < len(movie_list):
        movie = movie_list[index]
        print(f"Title: {movie['Title']}")
        print(f"Year: {movie['Year']}")
        print(f"Type: {movie['Type']}")
        print(f"Poster: {movie['Poster']}")
        print(f"imdbID: {movie['imdbID']}")
    else:
        print("Index out of range.")

def search_movie_by_id(movie_id):
    movie_info = requests.get(f"http://www.omdbapi.com/?i={movie_id}&apikey={api_key}").json()
    if movie_info['Response'] == 'True':
        movie = movie_info

        movie_info_text = f"Название: {movie['Title']} ({translator_ru.translate(movie['Title'])})\n"
        movie_info_text += f"Год: {movie['Year']}\n"
        movie_info_text += f"Жанр: {movie['Genre']}\n"
        movie_info_text += f"Рейтинг:\n"
        movie_info_text += f"  IMDB: {movie['imdbRating']}\n"

        if 'Ratings' in movie:
            for rating in movie['Ratings']:
                if rating['Source'] == 'Rotten Tomatoes':
                    movie_info_text += f"  Rotten Tomatoes: {rating['Value']}\n"
                elif rating['Source'] == 'Metacritic':
                    movie_info_text += f"  Metacritic: {rating['Value']}\n"

        movie_info_text += f"Всего голосовало на IMDB: {movie['imdbVotes']}\n"
        movie_info_text += f"Длительность: {movie['Runtime']}\n"
        movie_info_text += f"Награды: {translator_ru.translate(movie['Awards'])}\n"
        movie_info_text += f"Описание: {movie['Plot']}\n"
        movie_info_text += f"Описание на русском: {translator_ru.translate(movie['Plot'])}\n"
        movie_info_text += f"Постер: {movie['Poster']}"

        print(movie_info_text)
    else:
        print("Фильм не найден")



for i in range(len(movies)):
    print_movie_details(movies, i)

movie_id = input("Введите ID фильма: ")
search_movie_by_id(movie_id)
