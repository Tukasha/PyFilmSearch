from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QStatusBar, QPushButton, QTextBrowser, QDialog, QScrollArea
from PyQt6.QtGui import QPixmap, QIntValidator, QFont
from PyQt6 import QtWidgets, QtCore
from PyQt6 import QtCore
from deep_translator import GoogleTranslator
from datetime import datetime
import requests
import langid
import random
import sys

class AlignDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/questions/54262868/how-to-center-the-text-in-the-list-of-the-qcombobox"""
    def displayText(self, text, locale):
        return text

    def paint(self, painter, option, index):
        option.displayAlignment = QtCore.Qt.AlignmentFlag.AlignCenter
        super().paint(painter, option, index)

class RandomButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.random_icons = [u"\u2680", u"\u2681", u"\u2682", u"\u2683", u"\u2684", u"\u2685"]
        self.rating_index = 0
        self.timer = None

    def enterEvent(self, event):
        self.timer = self.startTimer(50)

    def leaveEvent(self, event):
        if self.timer:
            self.killTimer(self.timer)

    def timerEvent(self, event):
        self.setText(self.random_icons[self.rating_index])
        self.rating_index = (self.rating_index + 1) % len(self.random_icons)

class MovieSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        global API_KEY

        self.api_key = API_KEY
        self.translator_en = GoogleTranslator(source='ru', target='en')
        self.translator_ru = GoogleTranslator(source='en', target='ru')

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create a horizontal layout for the search input and button
        search_layout = QHBoxLayout()
        self.layout.addLayout(search_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Название фильма")
        search_layout.addWidget(self.search_input)

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Год выпуска")
        self.year_input.setValidator(QIntValidator(1888, int(datetime.now().year)))  # Only allow 4-digit numbers
        self.year_input.setFixedWidth(45)
        self.year_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)  # Выровнять текст по центру
        search_layout.addWidget(self.year_input)

        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("Страница")
        self.page_input.setValidator(QIntValidator(1, 100))
        self.page_input.setFixedWidth(40)
        self.page_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)  # Выровнять текст по центру
        search_layout.addWidget(self.page_input)

        self.type_combo = QtWidgets.QComboBox()
        # https://stackoverflow.com/questions/23770287/how-to-center-text-in-qcombobox
        self.type_combo.setEditable(True)
        self.type_combo.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.type_combo.lineEdit().setReadOnly(True)
        self.type_combo.addItems(["all", "movie", "series", "episode"])
        self.type_combo.setFixedWidth(85)
        delegate = AlignDelegate(self.type_combo)
        self.type_combo.setItemDelegate(delegate)
        search_layout.addWidget(self.type_combo)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.search_movies)
        search_layout.addWidget(self.search_button)

        self.status_bar = QStatusBar()
        self.layout.addWidget(self.status_bar)

        self.random_button = RandomButton(random.choice([u"\u2680", u"\u2681", u"\u2682", u"\u2683", u"\u2684", u"\u2685"]), self)
        font = QFont("Arial", 20)
        self.random_button.setFont(font)
        self.random_button.setFixedWidth(25)
        self.random_button.setFixedHeight(30)
        self.random_button.clicked.connect(self.random_movie)
        search_layout.addWidget(self.random_button)

        self.movie_buttons = []
        self.scroll_area = QScrollArea()
        self.layout.addWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.search_input.returnPressed.connect(self.search_button.click)
    

    def auto_translate_resp(self, resp):
        if langid.classify(resp)[0] != "en":
            try:
                translated_text = self.translator_en.translate(resp)
                resp = translated_text
            except Exception as e:
                print(f"Translation error: {e}")
        return resp

    def search_movies(self):
        resp = self.search_input.text()
        resp = self.auto_translate_resp(resp)
        year_warning = ""
        year = None
        page_warning = ""
        page = None

        if self.year_input.hasAcceptableInput():
            year = self.year_input.text()
        elif self.year_input.text() == "":
            pass
        else:
            year_warning = "Некорректный год проигнорирован.\n"
            self.status_bar.showMessage("Некорректный год проигнорирован")

        if self.page_input.hasAcceptableInput():
            page = self.page_input.text()
        elif self.page_input.text() == "":
            pass
        else:
            page_warning = "Некорректная страница проигнорирована.\n"
            self.status_bar.showMessage("Некорректная страница проигнорирована.")
        

        type = self.type_combo.currentText()

        url = f'http://www.omdbapi.com/?s={resp}'
        if year:
            print("Year:", year )
            url += f'&y={year}'
        if type != "all":
            url += f'&type={type}'
        if page:
            print("Page:", page)
            url += f'&page={page}'
        url += f'&apikey={self.api_key}'
    

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            data = response.json()
        except Exception as e:
            self.status_bar.showMessage("Ошибка запроса к API")
            print("Error with request:", e)  # Debug logging
            return
            
        if 'Search' in data:
            movies = data['Search']
            self.status_bar.showMessage(year_warning + page_warning + f"Найдено {len(movies)} фильмов")
        else:
            self.status_bar.showMessage(year_warning + page_warning + "По вашему запросу ничего не найдено")
            return
        
        self.movie_buttons.clear()
        for button in self.layout.findChildren(QPushButton):
            if button is not None:
                button.deleteLater()
        self.movie_buttons = []
        
        container = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()
        container.setLayout(layout)
        
        max_text_width = 0
        for movie in movies:
            font_metrics = QPushButton().fontMetrics()
            text_rect = font_metrics.boundingRect(f"{movie['Title']} ({movie['Year']})")
            max_text_width = max(max_text_width, text_rect.width())
        
        for movie in movies:
            button = QPushButton()
            button.setFixedWidth(max_text_width + 20)
            button.setMinimumHeight(QPushButton().fontMetrics().height() + 20)
            layout_button = QVBoxLayout()
            layout_button_center = QHBoxLayout()
            layout_button.addLayout(layout_button_center)
            
            label = QLabel()
            label.setText(f"{movie['Title']} ({movie['Year']})")
            layout_button_center.addStretch()
            layout_button_center.addWidget(label)
            layout_button_center.addStretch()
            
            button.setLayout(layout_button)
            
            if movie['imdbID'] is not None:
                button.clicked.connect(lambda checked, movie_id=movie['imdbID']: self.show_movie_info(movie_id))
        
            layout.addWidget(button)
            if button is not None:
                self.movie_buttons.append(button)
        
        layout.addStretch()
        
        # Центрировать кнопки внутри scroll_area
        scroll_layout = QHBoxLayout()
        scroll_layout.addStretch()
        scroll_layout.addWidget(container)
        scroll_layout.addStretch()
        
        scroll_container = QWidget()
        scroll_container.setLayout(scroll_layout)
        self.scroll_area.setWidget(scroll_container)
        self.scroll_area.setFixedWidth(max_text_width + 40)  # добавить отступ
        self.scroll_area.setMinimumWidth(self.status_bar.width())
        self.scroll_area.setWidgetResizable(True)
    
    def random_movie(self):
        movie_id = "tt" + "".join(random.choice("0123456789") for _ in range(7))
        self.show_movie_info(movie_id, random=True)

    def show_movie_info(self, movie_id, random=False):
        dialog = QDialog()
        dialog.setWindowTitle("Информация о фильме")
        print("Movie ID:", movie_id)
        layout = QVBoxLayout()
        dialog.setLayout(layout)
    
        try:
            response = requests.get(f"http://www.omdbapi.com/?i={movie_id}&apikey={self.api_key}")
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            movie_info = response.json()
            print("Movie info:", movie_info)  # Debug logging
        except requests.exceptions.RequestException as e:
            print("Error:", e)  # Debug logging
            label = QLabel("Ошибка запроса к API")
            layout.addWidget(label)
            dialog.exec()
            return
    
        if 'Response' in movie_info and movie_info['Response'] == 'True':
            movie = movie_info
    
            # Скачать постер фильма
            poster_url = movie['Poster']
            try:
                if poster_url == "N/A":
                    label = QLabel("Постера нет")
                    layout.addWidget(label)
                else:
                    response = requests.get(poster_url)
                    response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                    image_data = response.content
        
                    # Создать QPixmap из изображения
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
        
                    # Создать QLabel для отображения постера
                    poster = QLabel()
                    # poster.setFixedSize(200, 150)
                    poster.setScaledContents(True)
                    poster.setPixmap(pixmap)
                    layout.addWidget(poster)
            except requests.exceptions.RequestException as e:
                label = QLabel("Ошибка скачивания постера")
                layout.addWidget(label)
                print(f"Ошибка скачивания постера: {e}")
    
            # Create a text browser to display the movie information
            text_browser = QTextBrowser()
            text_browser.setFixedHeight(text_browser.fontMetrics().height() * 4)
            layout.addWidget(text_browser)
    
            # Populate the text browser with the movie information
            movie_info_text = f"Название: {movie['Title']} ({self.translator_ru.translate(movie['Title'])})\n"
            movie_info_text += f"Год: {movie['Year']}\n"
            movie_info_text += f"Жанр: {movie['Genre']}\n"
            movie_info_text += f"Рейтинг:\n"
            movie_info_text += f"  IMDB: {movie['imdbRating']}\n"
            if 'Ratings' in movie:
                for rating in movie['Ratings']:
                    if rating['Source'] == 'RottenTomato':
                        movie_info_text += f"  RottenTomato: {rating['Value']}\n"
                    elif rating['Source'] == 'Metacritic':
                        movie_info_text += f"  Metacritic: {rating['Value']}\n"
            movie_info_text += f"Всего голосовало на IMDB: {movie['imdbVotes']}\n"
            movie_info_text += f"Длительность: {movie['Runtime']}\n"
            movie_info_text += f"Награды: {self.translator_ru.translate(movie['Awards'])}\n"
            movie_info_text += f"Описание: {movie['Plot']}\n"
            movie_info_text += f"Описание на русском: {self.translator_ru.translate(movie['Plot'])}\n"
    
            text_browser.setText(movie_info_text)

        else:
            label = QLabel("Фильм не найден")
            layout.addWidget(label)
            if random:
                self.random_movie()
                return
    
        dialog.exec()


if __name__ == "__main__":
    API_KEY = 'd58c5311'
    app = QApplication(sys.argv)
    window = MovieSearchApp()
    window.show()
    sys.exit(app.exec())