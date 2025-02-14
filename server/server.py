from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Ключи для OpenWeatherMap и Foursquare API
WEATHER_API_KEY = "c2546bcfca6507032268c80b8997fb3c"
FOURSQUARE_API_KEY = "fsq3883xRYaM2mu5DbJ0Eujas7ZQwwxhqZuuBkuk5i4Yiq0="


def get_location_by_ip():
    """Получает данные о местоположении клиента по его IP-адресу."""
    try:
        response = requests.get("http://ip-api.com/json")
        data = response.json()
        if data['status'] == 'success':
            return data['city'], data['lat'], data['lon']
        else:
            return None, None, None
    except Exception as e:
        print("Ошибка при получении данных по IP:", e)
        return None, None, None


@app.route('/get_weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    # Если город не указан, определяем местоположение по IP
    if not city:
        city, latitude, longitude = get_location_by_ip()
        if not city or not latitude or not longitude:
            return jsonify({"error": "Failed to determine location"}), 400
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
    else:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch weather data"}), 500
        weather_data = response.json()
        weather = {
            "city": weather_data.get('name', 'Unknown'),
            "temperature": weather_data['main'].get('temp', 'N/A'),
            "feels_like": weather_data['main'].get('feels_like', 'N/A'),
            "humidity": weather_data['main'].get('humidity', 'N/A'),
            "pressure": weather_data['main'].get('pressure', 'N/A'),
            "wind_speed": weather_data['wind'].get('speed', 'N/A'),
            "description": weather_data['weather'][0].get('description', 'N/A'),
            "country": weather_data['sys'].get('country', 'N/A')
        }
        return jsonify(weather)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/search_products', methods=['GET'])
def search_products():
    query = request.args.get('query')
    category = request.args.get('category', '')  # Добавляем параметр категории
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Поиск на Ozon
    ozon_url = f"https://www.ozon.ru/search/?text={query.replace(' ', '+')}"
    if category:
        ozon_url += f"&category={category}"

    # Поиск на Wildberries
    wildberries_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query.replace(' ', '+')}"
    if category:
        wildberries_url += f"&xsearch=1&subject={category}"

    return jsonify({
        "ozon_link": ozon_url,
        "wildberries_link": wildberries_url
    })


@app.route('/search_food', methods=['GET'])
def search_food():
    query = request.args.get('query')
    category = request.args.get('category', '')  # Добавляем параметр категории
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    # Поиск на Яндекс.Маркет
    yandex_market_url = f"https://market.yandex.ru/search?text={query.replace(' ', '+')}"
    if category:
        yandex_market_url += f"&how=aprice&local-offers-first=0&deliveryincluded=0&onstock=1&category={category}"

    # Поиск на Сбермаркет
    sbermarket_url = f"https://sbermarket.ru/search?query={query.replace(' ', '+')}"
    if category:
        sbermarket_url += f"&category={category}"

    return jsonify({
        "yandex_market_link": yandex_market_url,
        "sbermarket_link": sbermarket_url
    })


def format_address(address_parts):
    """Форматирует адрес, убирая лишние пробелы и запятые."""
    if not address_parts:
        return "Address not available"

    # Если адрес приходит как массив символов, объединяем его в строку
    if isinstance(address_parts, list):
        cleaned_address = "".join([part.strip() for part in address_parts if part.strip()])
    else:
        # Если адрес уже строка, просто очищаем её
        cleaned_address = address_parts.strip()

    # Разделяем адрес по запятым и снова соединяем для чистого форматирования
    cleaned_address = ", ".join([part.strip() for part in cleaned_address.split(",") if part.strip()])

    return cleaned_address


def generate_map_link(lat, lon, address=None, map_provider="google"):
    """Генерирует ссылку на Google Maps или Яндекс.Карты."""
    if lat and lon:
        if map_provider == "google":
            # Google Maps
            return f"https://www.google.com/maps?q={lat},{lon}"
        elif map_provider == "yandex":
            # Яндекс.Карты
            return f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map"
    elif address:
        if map_provider == "google":
            # Google Maps с адресом
            return f"https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}"
        elif map_provider == "yandex":
            # Яндекс.Карты с адресом
            return f"https://yandex.ru/maps/?text={address.replace(' ', '+')}"
    return None


@app.route('/find_restaurants', methods=['GET'])
def find_restaurants():
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    map_provider = request.args.get('map_provider', 'google')  # По умолчанию Google Maps

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    url = f"https://api.foursquare.com/v3/places/search"
    headers = {
        "Authorization": FOURSQUARE_API_KEY
    }
    params = {
        "ll": f"{latitude},{longitude}",
        "radius": 3000,
        "categories": "13065",  # Категория ресторанов
        "limit": 10
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch restaurant data"}), 500

        places_data = response.json()
        restaurants = []

        for place in places_data.get("results", []):
            address_parts = place.get("location", {}).get("formatted_address", [])
            address = format_address(address_parts)
            lat = place.get("geocodes", {}).get("main", {}).get("latitude")
            lon = place.get("geocodes", {}).get("main", {}).get("longitude")

            restaurant = {
                "name": place.get("name", "Unknown"),
                "address": address,
                "description": "Restaurant",
                "rating": place.get("rating", {}).get("score", "N/A"),
                "map_link": generate_map_link(lat, lon, address, map_provider)  # Передаем провайдера карт
            }
            restaurants.append(restaurant)

        return jsonify(restaurants)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/find_hotels', methods=['GET'])
def find_hotels():
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    map_provider = request.args.get('map_provider', 'google')  # По умолчанию Google Maps

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    url = f"https://api.foursquare.com/v3/places/search"
    headers = {
        "Authorization": FOURSQUARE_API_KEY
    }
    params = {
        "ll": f"{latitude},{longitude}",
        "radius": 3000,
        "categories": "19048",  # Категория отелей
        "limit": 10
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch hotel data"}), 500

        places_data = response.json()
        hotels = []

        for place in places_data.get("results", []):
            address_parts = place.get("location", {}).get("formatted_address", [])
            address = format_address(address_parts)
            lat = place.get("geocodes", {}).get("main", {}).get("latitude")
            lon = place.get("geocodes", {}).get("main", {}).get("longitude")

            hotel = {
                "name": place.get("name", "Unknown"),
                "address": address,
                "description": "Hotel",
                "rating": place.get("rating", {}).get("score", "N/A"),
                "map_link": generate_map_link(lat, lon, address, map_provider)  # Передаем провайдера карт
            }
            hotels.append(hotel)

        return jsonify(hotels)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_address', methods=['GET'])
def get_address():
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    map_provider = request.args.get('map_provider', 'google')  # По умолчанию Google Maps

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    url = f"https://api.foursquare.com/v3/places/search"
    headers = {
        "Authorization": FOURSQUARE_API_KEY
    }
    params = {
        "ll": f"{latitude},{longitude}",
        "radius": 100,
        "limit": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch address data"}), 500

        places_data = response.json()
        results = places_data.get("results", [])

        if not results:
            return jsonify({"address": "Address not available"})

        place = results[0]
        address_parts = place.get("location", {}).get("formatted_address", [])
        address = format_address(address_parts)
        lat = place.get("geocodes", {}).get("main", {}).get("latitude")
        lon = place.get("geocodes", {}).get("main", {}).get("longitude")

        return jsonify({
            "address": address,
            "map_link": generate_map_link(lat, lon, address, map_provider)  # Передаем провайдера карт
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
