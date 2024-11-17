import requests

movie_title = "The Shawshank Redemption"  # Название фильма, для которого хотите получить рекомендации

response = requests.get(f"https://api.criticker.com/api/v1/movie/{movie_title}/recommendations")

if response.status_code == 200:
    recommendations = response.json()["recommendations"]
    for movie in recommendations:
        print(movie["title"])