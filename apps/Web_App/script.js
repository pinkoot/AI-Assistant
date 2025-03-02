let mode = 'auto';
let currentSearchType = '';

function closeAllDialogs() {
    document.querySelectorAll('.dialog').forEach(dialog => {
        dialog.classList.add('hidden');
    });
}

function showWeatherDialog() {
    closeAllDialogs();
    const dialog = document.getElementById('weather-dialog');
    dialog.classList.remove('hidden');

    mode = 'auto';
    document.getElementById('city-input').value = '';
    document.getElementById('weather-result').textContent = '';
    document.getElementById('toggle-mode-btn').textContent = 'Автоматическое определение';
    document.getElementById('city-input').classList.add('hidden');
}

function toggleMode() {
    const modeBtn = document.getElementById('toggle-mode-btn');
    const cityInput = document.getElementById('city-input');

    mode = mode === 'auto' ? 'manual' : 'auto';
    modeBtn.textContent = mode === 'auto' ? 'Ввести город вручную' : 'Автоматическое определение';
    cityInput.classList.toggle('hidden');
}

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
        const userInfo = await getUserInfo();
        const response = await fetch(`http://127.0.0.1:5000/get_weather?city=${city}&${new URLSearchParams(userInfo)}`);
        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

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
        resultArea.textContent = `Ошибка: ${error.message}`;
    }
}

async function getUserInfo() {
    try {
        const ipResponse = await fetch('https://api.ipify.org?format=json');
        const ipData = await ipResponse.json();

        const browserInfo = {
            ip: ipData.ip,
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            isJavaScriptEnabled: true,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cookiesEnabled: navigator.cookieEnabled,
            online: navigator.onLine,
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
        };

        return browserInfo;
    } catch (error) {
        console.error("Ошибка получения информации о пользователе:", error);
        return {};
    }
}

function showSearchDialog(type) {
    closeAllDialogs();
    const dialog = document.getElementById('search-dialog');
    dialog.classList.remove('hidden');

    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '';

    const titles = {
        products: 'Поиск товаров',
        food: 'Поиск продуктов',
        web: 'Веб-поиск'
    };
    document.getElementById('search-title').textContent = titles[type];
    currentSearchType = type;
}

async function doSearch() {
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    const query = input.value.trim();

    if (!query) {
        alert("Введите поисковый запрос");
        return;
    }

    try {
        const userInfo = await getUserInfo();
        const endpoint = currentSearchType === 'places'
            ? `search_places?query=${query}&${new URLSearchParams(userInfo)}`
            : `search_${currentSearchType}?query=${query}&${new URLSearchParams(userInfo)}`;

        const response = await fetch(`http://127.0.0.1:5000/${endpoint}`);
        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const data = await response.json();
        results.innerHTML = data.error
            ? `Ошибка: ${data.error}`
            : Object.entries(data).map(([key, val]) => `<p>${key}: <a href="${val}" target="_blank">${val}</a></p>`).join('');
    } catch (error) {
        results.textContent = `Ошибка: ${error.message}`;
    }
}

async function handlePlaces(type) {
    closeAllDialogs();
    try {
        const coords = await getCurrentLocation();
        const userInfo = await getUserInfo();
        const response = await fetch(`http://127.0.0.1:5000/find_${type}?lat=${coords.latitude}&lon=${coords.longitude}&${new URLSearchParams(userInfo)}`);
        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const data = await response.json();
        data.error ? alert(data.error) : displayResults(type === 'restaurants' ? 'Рестораны' : 'Отели', data);
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

async function handleAddress() {
    closeAllDialogs();
    try {
        const coords = await getCurrentLocation();
        const userInfo = await getUserInfo();
        const response = await fetch(`http://127.0.0.1:5000/get_address?lat=${coords.latitude}&lon=${coords.longitude}&${new URLSearchParams(userInfo)}`);
        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const data = await response.json();
        data.error
            ? alert(data.error)
            : displayResults('Адрес', {Адрес: data.address, Карта: data.map_link});
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

function showPlacesSearchDialog() {
    closeAllDialogs();
    const dialog = document.getElementById('search-dialog');

    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '';

    dialog.classList.remove('hidden');
    document.getElementById('search-title').textContent = 'Поиск мест';
    currentSearchType = 'places';
}

function showExactSearchDialog() {
    closeAllDialogs();
    const dialog = document.getElementById('search-dialog');

    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '';

    dialog.classList.remove('hidden');
    document.getElementById('search-title').textContent = 'Точный поиск';
    currentSearchType = 'exact';
}

function displayResults(title, data) {
    closeAllDialogs();
    const dialog = document.getElementById('result-dialog');
    const content = document.getElementById('result-content');

    document.getElementById('result-title').textContent = title;
    content.innerHTML = '';

    if (Array.isArray(data)) {
        content.innerHTML = data.map(item => `
            <div class="result-item">
                <strong>${item.name || 'Без названия'}</strong>
                <p>Адрес: ${item.address || 'Нет данных'}</p>
                <p>Рейтинг: ${item.rating || 'Н/Д'}</p>
                <a href="${item.map_link}" target="_blank">Посмотреть на карте</a>
            </div>
        `).join('<hr>');
    } else {
        content.innerHTML = Object.entries(data).map(([key, val]) => `
            <p><strong>${key}:</strong> ${val || 'Нет данных'}</p>
        `).join('');
    }

    dialog.classList.remove('hidden');
}

async function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Геолокация не поддерживается вашим браузером"));
        } else {
            navigator.geolocation.getCurrentPosition(
                position => resolve(position.coords),
                error => reject(new Error("Не удалось определить местоположение"))
            );
        }
    });
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.dialog') && !e.target.closest('button')) {
        closeAllDialogs();
    }
});
