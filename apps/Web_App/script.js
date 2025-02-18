let mode = 'auto';
let currentSearchType = '';

// Show weather dialog
function showWeatherDialog() {
    document.getElementById('weather-dialog').classList.remove('hidden');
}

// Hide any dialog
function hideDialog(dialogId) {
    document.getElementById(dialogId).classList.add('hidden');
}

// Toggle weather input mode (manual/auto)
function toggleMode() {
    const modeBtn = document.getElementById('toggle-mode-btn');
    const cityInput = document.getElementById('city-input');

    mode = mode === 'auto' ? 'manual' : 'auto';
    modeBtn.textContent = mode === 'auto' ? 'Ввести город вручную' : 'Автоматическое определение';
    cityInput.classList.toggle('hidden');
}

// Fetch weather data
async function getWeather() {
    const cityInput = document.getElementById('city-input');
    const resultArea = document.getElementById('weather-result');
    let city = null;

    if (mode === 'manual') {
        city = cityInput.value.trim();
        if (!city) {
            alert("Введите название города.");
            return;
        }
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/get_weather?city=${city}`);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            resultArea.textContent = `Ошибка: ${data.error}`;
        } else {
            const formattedWeather = `
                Погода в ${data.city}, ${data.country}:
                Температура: ${data.temperature}°C
                Ощущается как: ${data.feels_like}°C
                Влажность: ${data.humidity}%
                Давление: ${data.pressure} hPa
                Скорость ветра: ${data.wind_speed} м/с
                Описание: ${data.description}
            `;
            resultArea.innerHTML = formattedWeather.replace(/\n/g, '<br>');
        }
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
        resultArea.textContent = `Ошибка при получении данных: ${error.message}`;
    }
}

// Show search dialog
function showSearchDialog(type) {
    const searchTitle = document.getElementById('search-title');
    const dialog = document.getElementById('search-dialog');
    dialog.classList.remove('hidden');
    searchTitle.textContent = ["Поиск товаров", "Поиск продуктов", "Веб-поиск"][["products", "food", "web"].indexOf(type)];
    currentSearchType = type; // Store the current search type
}

// Perform search
async function doSearch() {
    const inputField = document.getElementById('search-input');
    const resultsArea = document.getElementById('search-results');
    const query = inputField.value.trim();

    if (!query) {
        alert("Запрос не может быть пустым.");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/search_${currentSearchType}?query=${encodeURIComponent(query)}`);

        // Проверка статуса ответа
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            resultsArea.textContent = `Ошибка: ${data.error}`;
        } else {
            const links = Object.entries(data).map(([key, value]) => `<p>${key}: <a href="${value}" target="_blank">${value}</a></p>`).join('');
            resultsArea.innerHTML = links || "Нет результатов.";
        }
    } catch (error) {
        console.error("Ошибка при выполнении поиска:", error);
        resultsArea.textContent = `Ошибка при выполнении поиска: ${error.message}`;
    }
}

// Handle places actions
async function handlePlaces(type) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/find_${type}`);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            displayResults(`Результаты поиска (${type})`, data);
        }
    } catch (error) {
        console.error("Ошибка при обработке мест:", error);
        alert(`Ошибка при обработке мест: ${error.message}`);
    }
}

// Get current address
async function handleAddress() {
    try {
        const response = await fetch('http://127.0.0.1:5000/get_address');
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            alert(data.error);
        } else {
            displayResults("Текущий адрес", { address: data.address, map_link: data.map_link });
        }
    } catch (error) {
        console.error("Ошибка при получении текущего адреса:", error);
        alert(`Ошибка при получении текущего адреса: ${error.message}`);
    }
}

// Show places search dialog
function showPlacesSearchDialog() {
    const dialog = document.getElementById('search-dialog');
    const searchTitle = document.getElementById('search-title');
    dialog.classList.remove('hidden');
    searchTitle.textContent = "Поиск мест";
    currentSearchType = 'places';
}

// Show exact search dialog
function showExactSearchDialog() {
    const dialog = document.getElementById('search-dialog');
    const searchTitle = document.getElementById('search-title');
    dialog.classList.remove('hidden');
    searchTitle.textContent = "Точный поиск";
    currentSearchType = 'exact';
}

// Display results in a dialog
function displayResults(title, data) {
    const resultDialog = document.getElementById('result-dialog');
    const resultTitle = document.getElementById('result-title');
    const resultContent = document.getElementById('result-content');

    resultTitle.textContent = title;

    if (Array.isArray(data)) {
        const itemsHtml = data.map(item => `
            <div>
                <strong>${item.name || 'Название не указано'}</strong><br>
                Адрес: ${item.address || 'Адрес не указан'}<br>
                Рейтинг: ${item.rating || 'Н/Д'}<br>
                <a href="${item.map_link || '#'}" target="_blank">Карта</a>
            </div>
        `).join('<hr>');
        resultContent.innerHTML = itemsHtml || "Нет результатов.";
    } else if (typeof data === 'object') {
        const entries = Object.entries(data).map(([key, value]) => `<p>${key}: ${value || 'Недоступно'}</p>`).join('');
        resultContent.innerHTML = entries || "Нет данных.";
    } else {
        resultContent.textContent = data || "Нет данных.";
    }

    resultDialog.classList.remove('hidden');
}

// Open external links
function openLink(url) {
    window.open(url, '_blank');
}