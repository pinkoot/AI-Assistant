import requests


def get_weather(city=None):
    url = "http://127.0.0.1:5000/get_weather"
    params = {}
    if city:
        params["city"] = city
    response = requests.get(url, params=params)
    if response.status_code == 200:
        weather = response.json()
        print(f"Погода в {weather['city']}, {weather['country']}:")
        print(f"- Температура: {weather['temperature']}°C")
        print(f"- Ощущается как: {weather['feels_like']}°C")
        print(f"- Влажность: {weather['humidity']}%")
        print(f"- Давление: {weather['pressure']} hPa")
        print(f"- Скорость ветра: {weather['wind_speed']} м/с")
        print(f"- Описание: {weather['description']}")
    else:
        print("Ошибка при получении погоды:", response.json())


def search_products():
    query = input("Введите название товара для поиска: ")
    if not query:
        print("Название товара не может быть пустым.")
        return

    print("\nВыберите категорию:")
    print("1. Электроника")
    print("2. Одежда")
    print("3. Бытовая техника")
    print("4. Без категории")
    category_choice = input("Введите номер категории: ")

    category_map = {
        "1": "electronics",
        "2": "clothing",
        "3": "appliances",
        "4": ""
    }
    category = category_map.get(category_choice, "")

    url = "http://127.0.0.1:5000/search_products"
    params = {"query": query, "category": category}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Результаты поиска для '{query}':")
        print(f"1. Ozon: {data['ozon_link']}")
        print(f"2. Wildberries: {data['wildberries_link']}")
    else:
        print("Ошибка при поиске товаров:", response.json())


def search_food():
    query = input("Введите название продукта для поиска: ")
    if not query:
        print("Название продукта не может быть пустым.")
        return

    print("\nВыберите категорию:")
    print("1. Молочные продукты")
    print("2. Овощи и фрукты")
    print("3. Мясо и рыба")
    print("4. Без категории")
    category_choice = input("Введите номер категории: ")

    category_map = {
        "1": "dairy",
        "2": "fruits_vegetables",
        "3": "meat_fish",
        "4": ""
    }
    category = category_map.get(category_choice, "")

    url = "http://127.0.0.1:5000/search_food"
    params = {"query": query, "category": category}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Результаты поиска для '{query}':")
        print(f"1. Яндекс.Маркет: {data['yandex_market_link']}")
        print(f"2. Сбермаркет: {data['sbermarket_link']}")
    else:
        print("Ошибка при поиске продуктов:", response.json())


def get_geolocation():
    try:
        response = requests.get("http://ip-api.com/json")
        data = response.json()
        if data['status'] == 'success':
            return data['lat'], data['lon']
        else:
            return None, None
    except Exception as e:
        print("Ошибка при получении геопозиции:", e)
        return None, None


def choose_map_provider():
    print("\nВыберите карту:")
    print("1. Google Maps")
    print("2. Яндекс.Карты")
    choice = input("Введите номер: ")
    if choice == "1":
        return "google"
    elif choice == "2":
        return "yandex"
    else:
        print("Неверный выбор. Используется Google Maps по умолчанию.")
        return "google"


def find_restaurants(lat=None, lon=None):
    map_provider = choose_map_provider()  # Выбор карты
    if lat is None or lon is None:
        lat, lon = get_geolocation()
        if lat is None or lon is None:
            print("Не удалось определить вашу геопозицию.")
            return

    url = "http://127.0.0.1:5000/find_restaurants"
    params = {"lat": lat, "lon": lon, "map_provider": map_provider}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        restaurants = response.json()
        if not restaurants:
            print("Рестораны не найдены.")
        else:
            print("Ближайшие рестораны:")
            for i, restaurant in enumerate(restaurants, start=1):
                print(f"{i}. Название: {restaurant['name']}")
                print(f"   Адрес: {restaurant['address']}")
                print(f"   Рейтинг: {restaurant['rating']}")
                print(f"   Ссылка на карты: {restaurant['map_link']}\n")
    else:
        print("Ошибка при поиске ресторанов:", response.json())


def find_hotels(lat=None, lon=None):
    map_provider = choose_map_provider()  # Выбор карты
    if lat is None or lon is None:
        lat, lon = get_geolocation()
        if lat is None or lon is None:
            print("Не удалось определить вашу геопозицию.")
            return

    url = "http://127.0.0.1:5000/find_hotels"
    params = {"lat": lat, "lon": lon, "map_provider": map_provider}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        hotels = response.json()
        if not hotels:
            print("Отели не найдены.")
        else:
            print("Ближайшие отели:")
            for i, hotel in enumerate(hotels, start=1):
                print(f"{i}. Название: {hotel['name']}")
                print(f"   Адрес: {hotel['address']}")
                print(f"   Рейтинг: {hotel['rating']}")
                print(f"   Ссылка на карты: {hotel['map_link']}\n")
    else:
        print("Ошибка при поиске отелей:", response.json())


def get_client_address(lat=None, lon=None):
    map_provider = choose_map_provider()  # Выбор карты
    if lat is None or lon is None:
        lat, lon = get_geolocation()
        if lat is None or lon is None:
            print("Не удалось определить вашу геопозицию.")
            return

    url = "http://127.0.0.1:5000/get_address"
    params = {"lat": lat, "lon": lon, "map_provider": map_provider}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        address_data = response.json()
        address = address_data.get("address", "Address not available")
        map_link = address_data.get("map_link", "Map link not available")
        print(f"Ваш текущий адрес:\n{address}")
        print(f"Ссылка на карты: {map_link}")
    else:
        print("Ошибка при получении адреса:", response.json())


if __name__ == "__main__":
    while True:
        print("\nВыберите действие:")
        print("1. Получить погоду")
        print("2. Поиск товаров (Ozon, Wildberries)")
        print("3. Поиск продовольственных товаров (Яндекс.Маркет, Сбермаркет)")
        print("4. Найти рестораны")
        print("5. Найти отели")
        print("6. Узнать свой адрес")
        print("7. Выход")
        choice = input("Введите номер действия: ")

        if choice == "1":
            mode = input("Получить погоду по (1)городу или (2)автоматически? ")
            if mode == "1":
                city = input("Введите название города: ")
                get_weather(city=city)
            elif mode == "2":
                get_weather()  # Автоматическое определение местоположения
            else:
                print("Неверный выбор.")

        elif choice == "2":
            search_products()

        elif choice == "3":
            search_food()

        elif choice == "4":
            find_restaurants()

        elif choice == "5":
            find_hotels()

        elif choice == "6":
            get_client_address()

        elif choice == "7":
            print("До свидания!")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")
