import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"

INPUT_QUERY, GET_LOCATION = range(2)


class TelegramBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self._register_handlers()

    def _main_keyboard(self):
        """Клавиатура главного меню"""
        return ReplyKeyboardMarkup([
            ["🌤 Погода", "🛍 Товары"],
            ["🍔 Еда", "🍴 Рестораны"],
            ["🏨 Отели", "📍 Адрес"],
            ["🌐 Веб-поиск", "🔍 Места"],
            ["🎯 Точный поиск"]
        ], resize_keyboard=True)

    def _cancel_keyboard(self):
        """Клавиатура для отмены действия"""
        return ReplyKeyboardMarkup([["🚫 Отмена"]], resize_keyboard=True)

    def _register_handlers(self):
        """Регистрация обработчиков"""
        conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_main_menu)],
            states={
                INPUT_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_input)],
                GET_LOCATION: [
                    MessageHandler(filters.LOCATION, self._handle_location),
                    MessageHandler(filters.TEXT, self._handle_location_text)
                ]
            },
            fallbacks=[CommandHandler("cancel", self._cancel)],
        )

        self.application.add_handler(conv_handler)
        self.application.add_error_handler(self._error_handler)

    async def _handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик главного меню"""
        text = update.message.text
        context.user_data.clear()

        if text == "🌤 Погода":
            await update.message.reply_text(
                "Отправьте местоположение или введите город:",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("📍 Отправить местоположение", request_location=True)],
                    ["🚫 Отмена"]
                ], resize_keyboard=True)
            )
            return GET_LOCATION

        elif text == "🛍 Товары":
            await update.message.reply_text("Введите название товара:", reply_markup=self._cancel_keyboard())
            context.user_data["action"] = "products"
            return INPUT_QUERY

        elif text == "🍔 Еда":
            await update.message.reply_text("Что ищем из еды?", reply_markup=self._cancel_keyboard())
            context.user_data["action"] = "food"
            return INPUT_QUERY

        elif text == "🍴 Рестораны":
            await update.message.reply_text(
                "Отправьте ваше местоположение для поиска ресторанов:",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("📍 Отправить местоположение", request_location=True)],
                    ["🚫 Отмена"]
                ], resize_keyboard=True)
            )
            context.user_data["action"] = "restaurants"
            return GET_LOCATION

        elif text == "🏨 Отели":
            await update.message.reply_text(
                "Отправьте ваше местоположение для поиска отелей:",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("📍 Отправить местоположение", request_location=True)],
                    ["🚫 Отмена"]
                ], resize_keyboard=True)
            )
            context.user_data["action"] = "hotels"
            return GET_LOCATION

        elif text == "📍 Адрес":
            await update.message.reply_text(
                "Отправьте ваше местоположение:",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("📍 Отправить местоположение", request_location=True)],
                    ["🚫 Отмена"]
                ], resize_keyboard=True)
            )
            context.user_data["action"] = "address"
            return GET_LOCATION

        elif text == "🌐 Веб-поиск":
            await update.message.reply_text("Введите поисковый запрос:", reply_markup=self._cancel_keyboard())
            context.user_data["action"] = "web"
            return INPUT_QUERY

        elif text == "🔍 Места":
            await update.message.reply_text(
                "Что ищем? (например: аптека, банкомат)",
                reply_markup=self._cancel_keyboard()
            )
            context.user_data["action"] = "places"
            return INPUT_QUERY

        elif text == "🎯 Точный поиск":
            await update.message.reply_text("Введите точное название места:", reply_markup=self._cancel_keyboard())
            context.user_data["action"] = "exact"
            return INPUT_QUERY

        await update.message.reply_text("Используйте кнопки меню:", reply_markup=self._main_keyboard())
        return ConversationHandler.END

    async def _handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода"""
        text = update.message.text

        if text == "🚫 Отмена":
            return await self._cancel(update, context)

        action = context.user_data.get("action")
        query = text

        if action == "products":
            response = requests.get(f"{BASE_URL}/search_products", params={"query": query})
            if response.status_code == 200:
                data = response.json()
                message = f"Результаты поиска товаров:\n\n🔗 Ozon: {data['ozon_link']}\n🔗 Wildberries: {data['wildberries_link']}"

        elif action == "food":
            response = requests.get(f"{BASE_URL}/search_food", params={"query": query})
            if response.status_code == 200:
                data = response.json()
                message = f"Результаты поиска еды:\n\n🔗 Яндекс.Маркет: {data['yandex_market_link']}\n🔗 СберМаркет: {data['sbermarket_link']}"

        elif action == "web":
            response = requests.get(f"{BASE_URL}/search_web", params={"query": query})
            if response.status_code == 200:
                data = response.json()
                message = f"Результаты поиска:\n\n🔍 Google: {data['google_link']}\n🔍 Яндекс: {data['yandex_link']}"

        elif action == "places":
            context.user_data["query"] = query
            await update.message.reply_text(
                "Отправьте ваше местоположение:",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("📍 Отправить местоположение", request_location=True)],
                    ["🚫 Отмена"]
                ], resize_keyboard=True)
            )
            return GET_LOCATION

        elif action == "exact":
            response = requests.get(f"{BASE_URL}/search_exact", params={"query": query})
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    message = "❌ " + data["error"]
                else:
                    message = (
                        f"📍 {data['name']}\n"
                        f"Адрес: {data['address']}\n"
                        f"Рейтинг: {data.get('rating', 'Н/Д')}\n"
                        f"Ссылка на карту: {data['map_link']}"
                    )

        if response.status_code != 200:
            message = "⚠️ Ошибка при выполнении запроса"

        await update.message.reply_text(message, disable_web_page_preview=True)
        return await self._return_to_main(update)

    async def _handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка геолокации"""
        location = update.message.location
        lat = location.latitude
        lon = location.longitude
        action = context.user_data.get("action")

        try:
            if action == "weather":
                response = requests.get(f"{BASE_URL}/get_weather", params={"lat": lat, "lon": lon})
                if response.status_code == 200:
                    data = response.json()
                    message = (
                        f"🌤 Погода в {data['city']}:\n"
                        f"🌡 Температура: {data['temperature']}°C\n"
                        f"💨 Ощущается как: {data['feels_like']}°C\n"
                        f"💧 Влажность: {data['humidity']}%\n"
                        f"🌀 Давление: {data['pressure']} hPa\n"
                        f"🌪 Ветер: {data['wind_speed']} м/с\n"
                        f"📝 Описание: {data['description']}"
                    )

            elif action == "restaurants":
                response = requests.get(f"{BASE_URL}/find_restaurants", params={"lat": lat, "lon": lon})
                message = self._format_places(response, "Рестораны")

            elif action == "hotels":
                response = requests.get(f"{BASE_URL}/find_hotels", params={"lat": lat, "lon": lon})
                message = self._format_places(response, "Отели")

            elif action == "address":
                response = requests.get(f"{BASE_URL}/get_address", params={"lat": lat, "lon": lon})
                if response.status_code == 200:
                    data = response.json()
                    message = f"📍 Текущий адрес:\n{data.get('address', 'Не определен')}\nСсылка на карту: {data.get('map_link', '')}"

            elif action == "places":
                query = context.user_data.get("query")
                response = requests.get(f"{BASE_URL}/find_places", params={
                    "lat": lat,
                    "lon": lon,
                    "query": query
                })
                message = self._format_places(response, "Результаты поиска")

            if response.status_code != 200:
                message = "⚠️ Ошибка при выполнении запроса"

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            message = "⚠️ Произошла внутренняя ошибка"

        await update.message.reply_text(message, disable_web_page_preview=True)
        return await self._return_to_main(update)

    async def _handle_location_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода города для погоды"""
        text = update.message.text

        if text == "🚫 Отмена":
            return await self._cancel(update, context)

        city = text
        response = requests.get(f"{BASE_URL}/get_weather", params={"q": city})

        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                message = "❌ " + data["error"]
            else:
                message = (
                    f"🌤 Погода в {data['city']}:\n"
                    f"🌡 Температура: {data['temperature']}°C\n"
                    f"💨 Ощущается как: {data['feels_like']}°C\n"
                    f"💧 Влажность: {data['humidity']}%\n"
                    f"🌀 Давление: {data['pressure']} hPa\n"
                    f"🌪 Ветер: {data['wind_speed']} м/с\n"
                    f"📝 Описание: {data['description']}"
                )
        else:
            message = "⚠️ Ошибка при получении данных"

        await update.message.reply_text(message)
        return await self._return_to_main(update)

    def _format_places(self, response, title):
        """Форматирование списка мест"""
        if response.status_code == 200:
            places = response.json()
            if not places:
                return "❌ Ничего не найдено"

            message = [f"🏷 {title}:"]
            for place in places[:5]:
                message.append(
                    f"\n📍 {place.get('name', 'Без названия')}\n"
                    f"Адрес: {place.get('address', 'Не указан')}\n"
                    f"Рейтинг: {place.get('rating', 'Н/Д')}\n"
                    f"Ссылка: {place.get('map_link', 'Нет ссылки')}\n"
                )
            return "\n".join(message)
        return "⚠️ Ошибка при получении данных"

    async def _return_to_main(self, update: Update):
        """Возврат в главное меню"""
        await update.message.reply_text("Выберите действие:", reply_markup=self._main_keyboard())
        return ConversationHandler.END

    async def _cancel(self, update: Update):
        """Отмена действия"""
        await update.message.reply_text("Действие отменено", reply_markup=self._main_keyboard())
        return ConversationHandler.END

    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error("Ошибка: %s", context.error, exc_info=True)
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.", reply_markup=self._main_keyboard())

    def run(self):
        """Запуск бота"""
        self.application.run_polling()


if __name__ == "__main__":
    bot = TelegramBot("7828093872:AAGp7KAHGfnINWO2H27NXX8fvlh4XxZrWAU")
    bot.run()
