import sys
import requests
import hmac
import hashlib
import socket
import threading
import time
import platform
import psutil
import uuid
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QMessageBox, QDialog, QVBoxLayout, QLineEdit, QTextBrowser,
    QLabel, QGraphicsDropShadowEffect, QScrollArea, QFrame, QProgressBar, QSplashScreen
)
from PyQt5.QtGui import (
    QColor, QFont, QIcon, QPalette
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint,
    QParallelAnimationGroup, QSequentialAnimationGroup
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('client.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ==================== CRYPTO MODULE ====================
class VigenereCipher:
    def __init__(self, key: str):
        if not key:
            raise ValueError("Ключ не может быть пустым")
        self.key = key.lower().replace(' ', '')
        self.alphabet = 'абвгдежзийклмнопрстуфхцчшщъыьэюя0123456789.,- '
        self.char_to_index = {char: i for i, char in enumerate(self.alphabet)}

    def encrypt(self, text: str) -> str:
        encrypted = []
        key_index = 0
        for char in text.lower():
            if char in self.alphabet:
                shift = self.char_to_index[self.key[key_index % len(self.key)]]
                encrypted_char = self.alphabet[(self.char_to_index[char] + shift) % len(self.alphabet)]
                encrypted.append(encrypted_char)
                key_index += 1
            else:
                encrypted.append(char)
        return ''.join(encrypted)

    def decrypt(self, text: str) -> str:
        decrypted = []
        key_index = 0
        for char in text.lower():
            if char in self.alphabet:
                shift = self.char_to_index[self.key[key_index % len(self.key)]]
                decrypted_char = self.alphabet[(self.char_to_index[char] - shift) % len(self.alphabet)]
                decrypted.append(decrypted_char)
                key_index += 1
            else:
                decrypted.append(char)
        return ''.join(decrypted)


class EncryptedClient:
    def __init__(self):
        self.cipher = VigenereCipher("негр")

    def encrypt_request(self, params):
        try:
            return {k: self.cipher.encrypt(str(v)) for k, v in params.items()}
        except Exception as e:
            logger.error(f"Ошибка шифрования: {e}")
            return params

    def decrypt_response(self, data):
        try:
            if isinstance(data, dict):
                return {k: self.cipher.decrypt(v) for k, v in data.items()}
            return data
        except Exception as e:
            logger.error(f"Ошибка дешифровки: {e}")
            return data

    def generate_hmac(self, data):
        return hmac.new("негр".encode(), str(data).encode(), hashlib.sha256).hexdigest()


# ==================== SYSTEM MODULE ====================
class DeviceInfo:
    @staticmethod
    def get_device_info():
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            system_info = platform.uname()
            return {
                "hostname": hostname,
                "ip_address": ip_address,
                "system": system_info.system,
                "node_name": system_info.node,
                "release": system_info.release,
                "version": system_info.version,
                "machine": system_info.machine,
                "processor": system_info.processor,
                "cpu_count": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": psutil.disk_usage('/').percent,
                "boot_time": psutil.boot_time(),
                "mac_address": ':'.join(
                    ['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1])
            }
        except Exception as e:
            print(f"Ошибка получения информации об устройстве: {e}")
            return {}


# ==================== NETWORK MODULES ====================
class BaseClient:
    BASE_URL = "http://127.0.0.1:5000"

    def __init__(self):
        self.encryption_handler = EncryptedClient()

    def _get(self, endpoint, params=None):
        try:
            if params is None:
                params = {}

            logger.debug(f"Исходные параметры: {params}")

            device_info = DeviceInfo.get_device_info()
            combined_params = {**params, **device_info}
            encrypted_params = self.encryption_handler.encrypt_request(combined_params)
            logger.debug(f"Зашифрованные параметры: {encrypted_params}")

            hmac_signature = self.encryption_handler.generate_hmac(encrypted_params)
            headers = {"X-HMAC-Signature": hmac_signature}

            response = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params=encrypted_params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            encrypted_data = response.json()
            decrypted_data = self.encryption_handler.decrypt_response(encrypted_data)
            logger.debug(f"Расшифрованный ответ: {decrypted_data}")

            return decrypted_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {str(e)}")
            return {"error": f"Ошибка сети: {str(e)}"}
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {str(e)}", exc_info=True)
            return {"error": "Внутренняя ошибка клиента"}


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
            logger.error(f"Ошибка определения геопозиции: {e}")
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
        super().__init__()
        self.geolocation = GeolocationClient()
        self.map_provider = MapProviderClient()

    def handle_action(self, action_type, query=None):
        try:
            coords = self._get_coordinates()
            if not coords:
                return {"error": "Не удалось определить местоположение"}

            logger.debug(f"Получены координаты: {coords}")

            encrypted_coords = self.encryption_handler.encrypt_request({
                'lat': str(coords[0]),
                'lon': str(coords[1])
            })

            params = {
                'lat': encrypted_coords['lat'],
                'lon': encrypted_coords['lon'],
                'map_provider': 'google'
            }
            if query:
                params['query'] = query

            logger.debug(f"Параметры запроса: {params}")
            return self._get(self.ENDPOINTS[action_type], params)

        except Exception as e:
            logger.error(f"Ошибка в handle_action: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _get_coordinates(self):
        return self.geolocation.get_coordinates()


# ==================== UI STYLES ====================
STYLESHEET = """
/* Main Styles */
QMainWindow, QDialog {
    background-color: #121212;
    color: #e0e0e0;
    border: 1px solid #00ff9d;
    border-radius: 12px;
}

/* Buttons */
QPushButton {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x1:1, y1:0,
        stop:0 #1e1e1e, stop:1 #2a2a2a);
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    font-family: 'Segoe UI';
    min-width: 160px;
    min-height: 40px;
    margin: 5px;
}

QPushButton:hover {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x1:1, y1:0,
        stop:0 #2a2a2a, stop:1 #363636);
    border: 2px solid #00ffcc;
    color: #00ffcc;
}

QPushButton:pressed {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x1:1, y1:0,
        stop:0 #363636, stop:1 #424242);
    border: 2px solid #00ffff;
    color: #00ffff;
}

/* Input Fields */
QLineEdit {
    background-color: #252525;
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 8px;
    padding: 8px;
    font-size: 14px;
    font-family: 'Consolas';
    selection-background-color: #00ff9d50;
}

QLineEdit:focus {
    border: 2px solid #00ffcc;
    background-color: #2a2a2a;
}

/* Text Display */
QTextEdit, QTextBrowser {
    background-color: #252525;
    color: #00ff9d;
    border: 2px solid #00ff9d;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas';
    font-size: 14px;
    selection-background-color: #00ff9d50;
}

QTextEdit:focus, QTextBrowser:focus {
    border: 2px solid #00ffcc;
    background-color: #2a2a2a;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: none;
    background: #1a1a1a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #00ff9d;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Labels */
QLabel {
    color: #00ff9d;
    font-family: 'Segoe UI';
    font-size: 14px;
}

/* Special Labels */
#title {
    font-size: 24px;
    font-weight: bold;
    color: #00ffcc;
    padding: 15px;
    background-color: rgba(30, 30, 30, 150);
    border-radius: 8px;
    border: 1px solid #00ff9d;
}

/* Cards */
QFrame#card {
    background-color: #252525;
    border-radius: 10px;
    border: 1px solid #00ff9d;
    padding: 10px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #00ff9d;
    border-radius: 5px;
    text-align: center;
    background-color: #1a1a1a;
}

QProgressBar::chunk {
    background-color: #00ff9d;
    width: 10px;
}

/* Message Box */
QMessageBox {
    background-color: #1a1a1a;
}

QMessageBox QLabel {
    color: #00ff9d;
    font-size: 14px;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


# ==================== UI COMPONENTS ====================
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(500)
        self._animation.setEasingCurve(QEasingCurve.OutBack)

        self._hover_animation = QPropertyAnimation(self, b"iconSize")
        self._hover_animation.setDuration(200)

        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setBlurRadius(15)
        self._shadow.setColor(QColor(0, 255, 156, 150))
        self._shadow.setOffset(3, 3)
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self.iconSize())
        self._hover_animation.setEndValue(self.iconSize() * 1.1)
        self._hover_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self.iconSize())
        self._hover_animation.setEndValue(self.iconSize() / 1.1)
        self._hover_animation.start()
        super().leaveEvent(event)


class ResultCard(QFrame):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout()
        self.setLayout(layout)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #00ffcc;
            font-size: 16px;
            font-weight: bold;
            border-bottom: 1px solid #00ff9d;
            padding-bottom: 5px;
        """)

        content_label = QLabel(content)
        content_label.setStyleSheet("color: #00ff9d;")
        content_label.setWordWrap(True)
        content_label.setOpenExternalLinks(True)

        layout.addWidget(title_label)
        layout.addWidget(content_label)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 255, 156, 100))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

        self._setup_animation()

    def _setup_animation(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self.setWindowIcon(QIcon(':/icons/app.png'))
        self.setGeometry(100, 100, 1024, 768)
        self.setStyleSheet(STYLESHEET)

        font = QFont('Segoe UI', 10)
        QApplication.setFont(font)

        self.weather_client = WeatherClient()
        self.search_client = SearchClient()
        self.places_client = PlacesClient()

        self.device_info = {}
        self.init_ui()
        self.start_device_info_thread()
        self.setup_animations()

    def setup_animations(self):
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(1000)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QGridLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        central_widget.setLayout(layout)

        title = QLabel("AI ASSISTANT")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 3)

        buttons = [
            ("🌤 Погода", self.show_weather_dialog),
            ("🛒 Товары", lambda: self.show_search_dialog('products')),
            ("🍔 Еда", lambda: self.show_search_dialog('food')),
            ("🍽 Рестораны", lambda: self.handle_places('restaurants')),
            ("🏨 Отели", lambda: self.handle_places('hotels')),
            ("📍 Адрес", self.handle_address),
            ("🌐 Веб", lambda: self.show_search_dialog('web')),
            ("🔎 Места", lambda: self.show_places_search_dialog()),
            ("🎯 Точный поиск", self.show_exact_search_dialog),
            ("⏻ Выход", self.close)
        ]

        positions = [(i // 3 + 1, i % 3) for i in range(9)] + [(4, 1)]
        for (text, handler), pos in zip(buttons, positions):
            btn = AnimatedButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn, *pos)

    def start_device_info_thread(self):
        def get_device_info():
            self.device_info = DeviceInfo.get_device_info()
            logger.debug(f"Информация об устройстве: {self.device_info}")

        thread = threading.Thread(target=get_device_info)
        thread.daemon = True
        thread.start()

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Ошибка")
        msg.setInformativeText(message)
        msg.setWindowTitle("Ошибка")
        msg.exec_()

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


# ==================== DIALOGS ====================
class WeatherDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Погодный сканер")
        self.setWindowIcon(QIcon(':/icons/weather.png'))
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(800)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        title = QLabel("ПОГОДНЫЙ СКАНЕР")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.mode_btn = AnimatedButton("Автоматическое определение")
        self.mode_btn.clicked.connect(self.toggle_mode)
        layout.addWidget(self.mode_btn)

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Введите город")
        self.city_input.hide()
        layout.addWidget(self.city_input)

        self.search_btn = AnimatedButton("Получить погоду")
        self.search_btn.clicked.connect(self.get_weather)
        layout.addWidget(self.search_btn)

        self.result_display = QTextBrowser()
        self.result_display.setOpenExternalLinks(True)
        layout.addWidget(self.result_display)

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

        html_content = f"""
        <html>
        <body style="color:#00ff9d; font-family: 'Consolas';">
            <h2 style="color:#00ffcc;">Погода в {data['city']}, {data['country']}</h2>
            <p>Температура: {data['temperature']}°C</p>
            <p>Ощущается как: {data['feels_like']}°C</p>
            <p>Влажность: {data['humidity']}%</p>
            <p>Давление: {data['pressure']} hPa</p>
            <p>Скорость ветра: {data['wind_speed']} м/с</p>
            <p>Описание: {data['description']}</p>
        </body>
        </html>
        """
        self.result_display.setHtml(html_content)


class SearchDialog(QDialog):
    def __init__(self, search_type, parent):
        super().__init__(parent)
        self.parent = parent
        self.search_type = search_type
        self.setWindowTitle(
            ["Поиск товаров", "Поиск продуктов", "Веб-поиск"][["products", "food", "web"].index(search_type)])
        self.setWindowIcon(QIcon(f':/icons/{search_type}.png'))
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.animation_group = QParallelAnimationGroup()

        pos_anim = QPropertyAnimation(self, b"pos")
        pos_anim.setDuration(500)
        pos_anim.setEasingCurve(QEasingCurve.OutBack)
        pos_anim.setStartValue(QPoint(self.x(), self.y() - 50))
        pos_anim.setEndValue(QPoint(self.x(), self.y()))

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(500)
        opacity_anim.setStartValue(0)
        opacity_anim.setEndValue(1)

        self.animation_group.addAnimation(pos_anim)
        self.animation_group.addAnimation(opacity_anim)
        self.animation_group.start()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        title = QLabel(
            ["ПОИСК ТОВАРОВ", "ПОИСК ПРОДУКТОВ", "ВЕБ-ПОИСК"][["products", "food", "web"].index(self.search_type)])
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите запрос")
        layout.addWidget(self.input_field)

        self.search_btn = AnimatedButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

        self.result_display = QTextBrowser()
        self.result_display.setOpenExternalLinks(True)
        layout.addWidget(self.result_display)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.search_client.search(self.search_type, query)
        if "error" in data:
            self.parent.show_error(data["error"])
            return

        html_content = []
        for key, label in self.parent.search_client.SERVICES[self.search_type]['results'].items():
            url = data.get(key)
            if url:
                html_content.append(
                    f'<p style="margin: 10px 0;"><b>{label}:</b> '
                    f'<a href="{url}" style="color:#00ff9d;text-decoration:none;">{url}</a></p>'
                )
            else:
                html_content.append(f'<p style="color:#ff5555;">{label}: Ссылка недоступна</p>')

        self.result_display.setHtml("".join(html_content))


class ResultDialog(QDialog):
    def __init__(self, title, data, parent):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(':/icons/results.png'))
        self.setMinimumSize(700, 600)
        self.data = data
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.animation = QSequentialAnimationGroup()

        scale_anim = QPropertyAnimation(self, b"geometry")
        scale_anim.setDuration(300)
        scale_anim.setEasingCurve(QEasingCurve.OutBack)
        scale_anim.setStartValue(self.geometry().adjusted(20, 20, -20, -20))
        scale_anim.setEndValue(self.geometry())

        self.animation.addAnimation(scale_anim)
        self.animation.start()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        title_label = QLabel(self.windowTitle())
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.info_display = QTextBrowser()
        layout.addWidget(self.info_display)

        if isinstance(self.data, list):
            for item in self.data:
                card = ResultCard(
                    item.get('name', 'Название не указано'),
                    self._format_item(item)
                )
                content_layout.addWidget(card)
            self.info_display.setHtml(f"<p style='color:#00ff9d;'>Найдено объектов: {len(self.data)}</p>")
        elif isinstance(self.data, dict):
            card = ResultCard(
                "Результат",
                self._format_dict(self.data)
            )
            content_layout.addWidget(card)
            self.info_display.setHtml("<p style='color:#00ff9d;'>Детальная информация:</p>")

    def _format_item(self, item):
        return f"""
            <p style="margin: 5px 0; color: #00ff9d;">📍 Адрес: {item.get('address', 'Н/Д')}</p>
            <p style="margin: 5px 0; color: {self._get_rating_color(item)};">★ Рейтинг: {item.get('rating', 'Н/Д')}</p>
            <p style="margin: 5px 0; color: #00ff9d;">🌐 <a href="{item.get('map_link', '')}" style="color: #00ff9d; text-decoration: none;">{item.get('map_link', 'Ссылка отсутствует')}</a></p>
        """

    def _format_dict(self, data):
        if "address" in data:
            return f"""
                <p style="margin: 5px 0; color: #00ff9d;">📍 Адрес: {data['address']}</p>
                <p style="margin: 5px 0; color: #00ff9d;">🌐 <a href="{data.get('map_link', '')}" style="color: #00ff9d; text-decoration: none;">{data.get('map_link', 'Ссылка отсутствует')}</a></p>
            """
        return str(data)

    def _get_rating_color(self, item):
        rating = item.get('rating', 'Н/Д')
        try:
            rating_val = float(rating)
            if rating_val > 4.5: return "#00ff00"
            if rating_val > 3.5: return "#aaff00"
            if rating_val > 2.5: return "#ffff00"
            return "#ff0000"
        except ValueError:
            return "#888888"


class PlacesSearchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Поиск мест")
        self.setWindowIcon(QIcon(':/icons/places.png'))
        self.setMinimumSize(500, 300)
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        title = QLabel("ПОИСК МЕСТ")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите запрос (например, 'аптека', 'магазин')")
        layout.addWidget(self.input_field)

        self.search_btn = AnimatedButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

        self.result_display = QTextBrowser()
        layout.addWidget(self.result_display)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.places_client.handle_action('places', query)
        if "error" in data:
            self.parent.show_error(data["error"])
            return

        if isinstance(data, list):
            results = []
            for item in data:
                results.append(f"""
                    <div style="margin-bottom: 15px; border-bottom: 1px solid #00ff9d; padding-bottom: 10px;">
                        <h3 style="color: #00ffcc; margin: 5px 0;">{item.get('name', 'Без названия')}</h3>
                        <p style="color: #00ff9d; margin: 3px 0;">📍 {item.get('address', 'Адрес не указан')}</p>
                        <p style="color: {self._get_rating_color(item)}; margin: 3px 0;">★ Рейтинг: {item.get('rating', 'Н/Д')}</p>
                    </div>
                """)
            self.result_display.setHtml("".join(results))
        else:
            self.result_display.setPlainText(str(data))

    def _get_rating_color(self, item):
        rating = item.get('rating', 'Н/Д')
        try:
            rating_val = float(rating)
            if rating_val > 4.5: return "#00ff00"
            if rating_val > 3.5: return "#aaff00"
            if rating_val > 2.5: return "#ffff00"
            return "#ff0000"
        except ValueError:
            return "#888888"


class ExactSearchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Точный поиск")
        self.setWindowIcon(QIcon(':/icons/exact.png'))
        self.setMinimumSize(500, 300)
        self.init_ui()
        self.setup_animations()

    def setup_animations(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutBack)
        self.animation.setStartValue(self.geometry().adjusted(50, 50, -50, -50))
        self.animation.setEndValue(self.geometry())
        self.animation.start()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        title = QLabel("ТОЧНЫЙ ПОИСК")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите адрес или название заведения")
        layout.addWidget(self.input_field)

        self.search_btn = AnimatedButton("Поиск")
        self.search_btn.clicked.connect(self.do_search)
        layout.addWidget(self.search_btn)

        self.result_display = QTextBrowser()
        layout.addWidget(self.result_display)

    def do_search(self):
        query = self.input_field.text()
        if not query:
            self.parent.show_error("Запрос не может быть пустым")
            return

        data = self.parent.places_client.handle_action('exact', query)
        if "error" in data:
            self.parent.show_error(data["error"])
            return

        if isinstance(data, dict):
            html_content = f"""
            <html>
            <body style="color:#00ff9d; font-family: 'Consolas';">
                <h2 style="color:#00ffcc;">Результаты поиска</h2>
                <p><b>Название:</b> {data.get('name', 'Не указано')}</p>
                <p><b>Адрес:</b> {data.get('address', 'Не указан')}</p>
                <p><b>Рейтинг:</b> <span style="color:{self._get_rating_color(data)};">{data.get('rating', 'Н/Д')}</span></p>
                <p><b>Ссылка на карты:</b> <a href="{data.get('map_link', '')}" style="color:#00ff9d;">{data.get('map_link', 'Нет ссылки')}</a></p>
            </body>
            </html>
            """
            self.result_display.setHtml(html_content)
        else:
            self.result_display.setPlainText(str(data))

    def _get_rating_color(self, data):
        rating = data.get('rating', 'Н/Д')
        try:
            rating_val = float(rating)
            if rating_val > 4.5: return "#00ff00"
            if rating_val > 3.5: return "#aaff00"
            if rating_val > 2.5: return "#ffff00"
            return "#ff0000"
        except ValueError:
            return "#888888"


# ==================== APPLICATION ENTRY ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(25, 25, 25))
    palette.setColor(QPalette.WindowText, QColor(0, 255, 157))
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.Text, QColor(0, 255, 157))
    palette.setColor(QPalette.Button, QColor(30, 30, 30))
    palette.setColor(QPalette.ButtonText, QColor(0, 255, 157))
    palette.setColor(QPalette.Highlight, QColor(0, 255, 157))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    splash = QSplashScreen()
    splash.setStyleSheet("""
        background-color: #121212;
        color: #00ff9d;
        border: 2px solid #00ff9d;
    """)

    splash_layout = QVBoxLayout()
    splash.setLayout(splash_layout)

    title = QLabel("AI ASSISTANT")
    title.setStyleSheet("""
        QLabel {
            color: #00ff9d;
            font-size: 32px;
            font-weight: bold;
            font-family: 'Segoe UI';
        }
    """)
    title.setAlignment(Qt.AlignCenter)
    splash_layout.addWidget(title)

    progress = QProgressBar()
    progress.setStyleSheet("""
        QProgressBar {
            border: 2px solid #00ff9d;
            border-radius: 5px;
            text-align: center;
            background-color: #1a1a1a;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(
                spread:pad, x1:0, y1:0, x1:1, y1:0,
                stop:0 #00ff9d, stop:1 #00ffcc
            );
        }
    """)
    progress.setRange(0, 100)
    progress.setTextVisible(False)
    splash_layout.addWidget(progress)

    status = QLabel("Инициализация системы...")
    status.setStyleSheet("""
        QLabel {
            color: #00ff9d;
            font-size: 14px;
            font-family: 'Consolas';
        }
    """)
    status.setAlignment(Qt.AlignCenter)
    splash_layout.addWidget(status)

    splash.show()

    for i in range(1, 101):
        progress.setValue(i)
        status.setText(f"Загрузка модулей... {i}%")
        app.processEvents()
        time.sleep(0.03)

        if i < 30:
            status.setText(f"Инициализация крипто-модуля... {i}%")
        elif i < 60:
            status.setText(f"Загрузка сетевого стека... {i}%")
        elif i < 90:
            status.setText(f"Настройка интерфейса... {i}%")
        else:
            status.setText(f"Запуск системы... {i}%")

    window = MainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec_())
