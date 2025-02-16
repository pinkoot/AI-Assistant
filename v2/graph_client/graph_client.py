import sys
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
                             QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
                             QStackedWidget, QButtonGroup, QHBoxLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPainter, QPalette


# Исходные классы клиента (без изменений)
class BaseClient:
    BASE_URL = "http://127.0.0.1:5000"

    def _get(self, endpoint, params=None):
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params)
        return response.json() if response.ok else {"error": response.text}


class WeatherClient(BaseClient):
    WEATHER_LABELS = {
        'temperature': 'Температура',
        'feels_like': 'Ощущается как',
        'humidity': 'Влажность',
        'pressure': 'Давление',
        'wind_speed': 'Скорость ветра',
        'description': 'Описание'
    }

    def get_weather(self, city=None):
        data = self._get("get_weather", {"city": city} if city else {})
        return data

    def format_weather(self, data):
        if "error" in data:
            return data["error"]
        formatted = [f"Погода в {data['city']}, {data['country']}:"]
        for key, label in self.WEATHER_LABELS.items():
            formatted.append(f"{label}: {data[key]}{self._get_unit(key)}")
        return "\n".join(formatted)

    @staticmethod
    def _get_unit(key):
        units = {
            'temperature': '°C',
            'feels_like': '°C',
            'humidity': '%',
            'pressure': ' hPa',
            'wind_speed': ' м/с'
        }
        return units.get(key, '')


class SearchClient(BaseClient):
    SERVICES = {
        'products': {
            'endpoint': 'search_products',
            'results': {
                'ozon_link': 'Ozon',
                'wildberries_link': 'Wildberries'
            }
        },
        'food': {
            'endpoint': 'search_food',
            'results': {
                'yandex_market_link': 'Яндекс Маркет',
                'sbermarket_link': 'Сбермаркет'
            }
        },
        'web': {
            'endpoint': 'search_web',
            'results': {
                'google_link': 'Google',
                'yandex_link': 'Яндекс'
            }
        }
    }

    def search(self, search_type, query):
        config = self.SERVICES[search_type]
        data = self._get(config['endpoint'], {"query": query})
        return data


class GeolocationClient:
    @staticmethod
    def get_coordinates():
        try:
            response = requests.get("http://ip-api.com/json")
            if response.ok:
                data = response.json()
                return (data['lat'], data['lon']) if data['status'] == 'success' else (None, None)
            return None, None
        except Exception as e:
            print(f"Ошибка определения геопозиции: {e}")
            return None, None


class MapProviderClient:
    PROVIDERS = {
        '1': ('google', 'Google Maps'),
        '2': ('yandex', 'Яндекс.Карты')
    }


class PlacesClient(BaseClient):
    ENDPOINTS = {
        'restaurants': 'find_restaurants',
        'hotels': 'find_hotels',
        'address': 'get_address',
        'places': 'find_places',
        'exact': 'search_exact'
    }

    def __init__(self):
        self.geolocation = GeolocationClient()
        self.map_provider = MapProviderClient()

    def handle_action(self, action_type, query=None):
        coords = self._get_coordinates()
        if not coords:
            return {"error": "Не удалось определить местоположение"}

        params = {
            'lat': coords[0],
            'lon': coords[1],
            'map_provider': 'google'
        }
        if query:
            params['query'] = query

        data = self._get(self.ENDPOINTS[action_type], params)
        return data

    def _get_coordinates(self):
        return self.geolocation.get_coordinates()


# Стилизация
STYLESHEET = """
QMainWindow {
    background-color: #1a1a1a;
}

QPushButton {
    background-color: #2d2d2d;
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 10px;
    padding: 15px;
    font-size: 14px;
    min-width: 150px;
}

QPushButton:hover {
    background-color: #3d3d3d;
}

QPushButton:pressed {
    background-color: #4d4d4d;
}

QLineEdit {
    background-color: #2d2d2d;
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 5px;
    padding: 5px;
    font-size: 14px;
}

QLabel {
    color: #00ff9d;
    font-size: 14px;
}

QTextEdit {
    background-color: #2d2d2d;
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 5px;
    padding: 5px;
    font-size: 14px;
}

QMessageBox {
    background-color: #1a1a1a;
}

QDialog {
    background-color: #1a1a1a;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Future Client")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(STYLESHEET)

        self.weather_client = WeatherClient()
        self.search_client = SearchClient()
        self.places_client = PlacesClient()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        central_widget.setLayout(layout)

        buttons = [
            ("Погода", self.show_weather_dialog),
            ("Поиск товаров", lambda: self.show_search_dialog('products')),
            ("Поиск продуктов", lambda: self.show_search_dialog('food')),
            ("Рестораны", lambda: self.handle_places('restaurants')),
            ("Отели", lambda: self.handle_places('hotels')),
            ("Текущий адрес", self.handle_address),
            ("Веб-поиск", lambda: self.show_search_dialog('web')),
            ("Поиск мест", lambda: self.show_places_search_dialog()),
            ("Точный поиск", self.show_exact_search_dialog),
            ("Выход", self.close)
        ]

        positions = [(i // 3, i % 3) for i in range(9)] + [(3, 1)]
        for (text, handler), pos in zip(buttons, positions):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn, *pos)

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def show_weather_dialog(self):
        dialog = WeatherDialog(self)
        dialog.exec_()

    def show_search_dialog(self, search_type):
        dialog = SearchDialog(search_type, self)
        dialog.exec_()

    def handle_places(self, action_type):
        data = self.places_client.handle_action(action_type)
        self.show_places_result(data, action_type)

    def show_places_result(self, data, entity_name):
        if "error" in data:
            self.show_error(data["error"])
            return

        dialog = ResultDialog(f"Результаты поиска ({entity_name})", data, self)
        dialog.exec_()

    def handle_address(self):
        data = self.places_client.handle_action('address')
        self.show_address_result(data)

    def show_address_result(self, data):
        if "error" in data:
            self.show_error(data["error"])
            return

        dialog = ResultDialog("Текущий адрес", data, self)
        dialog.exec_()

    def show_places_search_dialog(self):
        dialog = PlacesSearchDialog(self)
        dialog.exec_()

    def show_exact_search_dialog(self):
        dialog = ExactSearchDialog(self)
        dialog.exec_()


class WeatherDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Погода")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.mode_btn = QPushButton("Автоматическое определение")
        self.mode_btn.clicked.connect(self.toggle_mode)
        layout.addWidget(self.mode_btn)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Введите город")
        self.city_input.hide()
        layout.addWidget(self.city_input)

        self.search_btn = QPushButton("Получить погоду")
        self.search_btn.clicked.connect(self.get_weather)
        layout.addWidget(self.search_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.mode = 'auto'

    def toggle_mode(self):
        self.mode = 'manual' if self.mode == 'auto' else 'auto'
        self.mode_btn.setText("Ввести город вручную" if self.mode == 'auto' else "Автоматическое определение")
        self.city_input.setVisible(self.mode == 'manual')

    def get_weather(self):
        city = self.city_input.text() if self.mode == 'manual' else None
        data = self.parent.weather_client.get_weather(city)

        if "error" in data:
            self.parent.show_error(data["error"])
            return

        self.result_area.setText(self.parent.weather_client.format_weather(data))


class SearchDialog(QDialog):
    def __init__(self, search_type, parent):
        super().__init__(parent)
        self.parent = parent
        self.search_type = search_type
        self.setWindowTitle(
            ["Поиск товаров", "Поиск продуктов", "Веб-поиск"][["products", "food", "web"].index(search_type)])
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите запрос")
        layout.addWidget(self.input_field)

        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.search_client.search(self.search_type, query)
        if "error" in data:
            self.parent.show_error(data["error"])
            return

        results = []
        for key, label in self.parent.search_client.SERVICES[self.search_type]['results'].items():
            results.append(f"{label}: {data.get(key, 'Н/Д')}")

        self.result_area.setText("\n".join(results))


class ResultDialog(QDialog):
    def __init__(self, title, data, parent):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.data = data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(str(self.data))
        layout.addWidget(text)


class PlacesSearchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Поиск мест")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите запрос (например, 'аптека', 'магазин')")
        layout.addWidget(self.input_field)

        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.places_client.handle_action('places', query)
        self.parent.show_places_result(data, 'places')


class ExactSearchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Точный поиск")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите адрес или название заведения")
        layout.addWidget(self.input_field)

        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.places_client.handle_action('exact', query)
        self.parent.show_places_result(data, 'exact')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())