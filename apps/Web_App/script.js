const HMAC_KEY = "негр";
const SECRET_KEY = "негр";

let mode = 'auto';
let currentSearchType = '';

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.neon-btn');
    buttons.forEach(btn => {
        btn.style.opacity = '1';
        btn.style.visibility = 'visible';
    });

    setTimeout(() => {
        buttons.forEach((btn, i) => {
            btn.style.opacity = '0';
            btn.style.transform = 'translateY(20px)';
            btn.style.animation = `fadeInUp 0.5s ease-out ${i * 0.1}s forwards`;
        });
    }, 100);
});

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes dialogClose {
        to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
    }
`;
document.head.appendChild(style);

class VigenereCipher {
    constructor(key) {
        if (!key) throw new Error("Ключ не может быть пустым");
        this.key = key.toLowerCase().replace(/ /g, '');
        this.alphabet = 'абвгдежзийклмнопрстуфхцчшщъыьэюя0123456789.,- ';
        this.charMap = this.createCharMap();
    }

    createCharMap() {
        const map = {};
        for (let i = 0; i < this.alphabet.length; i++) {
            map[this.alphabet[i]] = i;
        }
        return map;
    }

    processText(text, encrypt = true) {
        let result = '';
        let keyIndex = 0;

        for (const char of text.toLowerCase()) {
            if (this.alphabet.includes(char)) {
                const keyChar = this.key[keyIndex % this.key.length];
                const shift = this.charMap[keyChar];

                let newIndex;
                if (encrypt) {
                    newIndex = (this.charMap[char] + shift) % this.alphabet.length;
                } else {
                    newIndex = (this.charMap[char] - shift + this.alphabet.length) % this.alphabet.length;
                }

                result += this.alphabet[newIndex];
                keyIndex++;
            } else {
                result += char;
            }
        }
        return result;
    }

    encrypt(text) {
        return this.processText(text, true);
    }

    decrypt(text) {
        return this.processText(text, false);
    }
}

class EncryptedClient {
    constructor() {
        this.cipher = new VigenereCipher("негр");
    }

    encryptRequest(params) {
        try {
            const encrypted = {};
            for (const [key, value] of Object.entries(params)) {
                encrypted[key] = this.cipher.encrypt(String(value));
            }
            return encrypted;
        } catch (e) {
            console.error("Encryption error:", e);
            return params;
        }
    }

    decryptResponse(data) {
        try {
            const decrypted = {};
            for (const [key, value] of Object.entries(data)) {
                decrypted[key] = this.cipher.decrypt(String(value));
            }
            return decrypted;
        } catch (e) {
            console.error("Decryption error:", e);
            return data;
        }
    }
}

const encryptedClient = new EncryptedClient();

function generateHmac(data) {
    return CryptoJS.HmacSHA256(JSON.stringify(data), HMAC_KEY).toString(CryptoJS.enc.Hex);
}

function closeAllDialogs() {
    const dialogs = document.querySelectorAll('.dialog:not(.hidden)');
    dialogs.forEach(dialog => {
        dialog.style.animation = 'dialogClose 0.3s forwards';
        setTimeout(() => {
            dialog.classList.add('hidden');
            dialog.style.animation = '';
        }, 300);
    });
}

function showWeatherDialog() {
    closeAllDialogs();
    const dialog = document.getElementById('weather-dialog');
    dialog.classList.remove('hidden');
    dialog.style.animation = 'fadeInUp 0.3s ease-out';

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
            showError("Введите название города.");
            return;
        }
        city = city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
    }

    try {
        const userInfo = await getUserInfo();
        const params = { q: city, ...userInfo };

        const encryptedParams = encryptedClient.encryptRequest(params);
        const hmacSignature = generateHmac(encryptedParams);

        const response = await fetch(`http://127.0.0.1:5000/get_weather?${new URLSearchParams(encryptedParams)}`, {
            headers: { 'X-HMAC-Signature': hmacSignature }
        });

        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const encryptedData = await response.json();
        const data = encryptedClient.decryptResponse(encryptedData);

        if (data.error) {
            showError(data.error);
        } else {
            resultArea.innerHTML = `
                <h3>Погода в ${data.city}, ${data.country}</h3>
                <p>🌡 Температура: ${data.temperature}°C</p>
                <p>🌬 Ощущается как: ${data.feels_like}°C</p>
                <p>💧 Влажность: ${data.humidity}%</p>
                <p>📊 Давление: ${data.pressure} hPa</p>
                <p>🌪 Скорость ветра: ${data.wind_speed} м/с</p>
                <p>🌈 Описание: ${data.description}</p>
            `;
        }
    } catch (error) {
        showError(error.message);
    }
}

function showError(message) {
    const errorBox = document.createElement('div');
    errorBox.className = 'error-message';
    errorBox.textContent = message;
    document.body.appendChild(errorBox);

    setTimeout(() => {
        errorBox.classList.add('fade-out');
        setTimeout(() => errorBox.remove(), 500);
    }, 3000);
}

async function getUserInfo() {
    try {
        const ipResponse = await fetch('https://api.ipify.org?format=json');
        const ipData = await ipResponse.json();

        return {
            ip: ipData.ip,
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cookiesEnabled: navigator.cookieEnabled,
            online: navigator.onLine,
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
        };
    } catch (error) {
        console.error("Ошибка получения информации о пользователе:", error);
        return {};
    }
}

function showSearchDialog(type) {
    closeAllDialogs();
    const dialog = document.getElementById('search-dialog');
    dialog.classList.remove('hidden');
    dialog.style.animation = 'fadeInUp 0.3s ease-out';

    document.getElementById('search-input').value = '';
    document.getElementById('search-results').innerHTML = '';

    const titles = {
        products: 'Поиск товаров',
        food: 'Поиск продуктов',
        web: 'Веб-поиск',
        places: 'Поиск мест',
        exact: 'Точный поиск'
    };
    document.getElementById('search-title').textContent = titles[type];
    currentSearchType = type;
}

async function doSearch() {
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    const query = input.value.trim();

    if (!query) {
        showError("Введите поисковый запрос");
        return;
    }

    try {
        const userInfo = await getUserInfo();
        let params = {};
        let endpoint = '';

        if (currentSearchType === 'places' || currentSearchType === 'exact') {
            params = {
                query: query,
                exact: true,
                ...userInfo
            };
            endpoint = 'search_exact';
        } else {
            params = { query: query, ...userInfo };
            endpoint = `search_${currentSearchType}`;
        }

        console.log('Sending params:', params);

        const encryptedParams = encryptedClient.encryptRequest(params);
        const hmacSignature = generateHmac(encryptedParams);

        const response = await fetch(
            `http://127.0.0.1:5000/${endpoint}?${new URLSearchParams(encryptedParams)}`,
            {
                headers: { 'X-HMAC-Signature': hmacSignature }
            }
        );

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`${response.status}: ${errorText}`);
        }

        const encryptedData = await response.json();
        const data = encryptedClient.decryptResponse(encryptedData);

        console.log('Decrypted data:', data);

        if (data.error) {
            showError(data.error);
        } else {
            if (currentSearchType === 'exact') {
                displayExactResult(data);
            } else if (currentSearchType === 'places') {
                displayResults('Найденные места', data.results || data);
            } else {
                results.innerHTML = Object.entries(data).map(([key, val]) =>
                    `<p><a href="${val}" target="_blank" class="result-link">${key}: ${val}</a></p>`
                ).join('');
            }
        }
    } catch (error) {
        console.error('Search error:', error);
        showError(error.message);
    }
}

async function handlePlaces(type) {
    closeAllDialogs();
    try {
        const coords = await getCurrentLocation();
        const userInfo = await getUserInfo();
        const params = { lat: coords.latitude, lon: coords.longitude, ...userInfo };

        const encryptedParams = encryptedClient.encryptRequest(params);
        const hmacSignature = generateHmac(encryptedParams);

        const response = await fetch(`http://127.0.0.1:5000/find_${type}?${new URLSearchParams(encryptedParams)}`, {
            headers: { 'X-HMAC-Signature': hmacSignature }
        });

        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const encryptedData = await response.json();
        const data = encryptedClient.decryptResponse(encryptedData);

        if (data.error) {
            showError(data.error);
        } else {
            displayResults(type === 'restaurants' ? 'Рестораны' : 'Отели', data);
        }
    } catch (error) {
        showError(error.message);
    }
}

async function handleExactSearch(query) {
    try {
        const userInfo = await getUserInfo();
        const params = {
            query: query,
            exact: true,
            ...userInfo
        };

        console.log("Params before encryption:", params);

        const encryptedParams = encryptedClient.encryptRequest(params);
        console.log("Encrypted params:", encryptedParams);

        const hmacSignature = generateHmac(encryptedParams);

        const response = await fetch(`http://127.0.0.1:5000/search_exact?${new URLSearchParams(encryptedParams)}`, {
            headers: { 'X-HMAC-Signature': hmacSignature }
        });

        console.log("Response status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const encryptedData = await response.json();
        console.log("Encrypted response:", encryptedData);

        const decryptedData = encryptedClient.decryptResponse(encryptedData);
        console.log("Decrypted data:", decryptedData);

        if (!decryptedData || typeof decryptedData !== 'object') {
            throw new Error("Invalid server response format");
        }

        if (!decryptedData.name && !decryptedData.address) {
            throw new Error("Server returned incomplete data");
        }

        const cleanData = {
            name: decryptedData.name ? decryptedData.name.trim() : "Название не указано",
            address: decryptedData.address ? decryptedData.address.trim() : "Адрес не указан",
            rating: decryptedData.rating || "н/д",
            map_link: decryptedData.map_link || "",
            description: decryptedData.description || ""
        };

        displayExactResult(cleanData);

    } catch (error) {
        console.error("Exact search failed:", error);
        showError(`Ошибка поиска: ${error.message}`);
    }
}

async function handleAddress() {
    closeAllDialogs();
    try {
        const coords = await getCurrentLocation();
        const userInfo = await getUserInfo();
        const params = { lat: coords.latitude, lon: coords.longitude, ...userInfo };

        const encryptedParams = encryptedClient.encryptRequest(params);
        const hmacSignature = generateHmac(encryptedParams);

        const response = await fetch(`http://127.0.0.1:5000/get_address?${new URLSearchParams(encryptedParams)}`, {
            headers: { 'X-HMAC-Signature': hmacSignature }
        });

        if (!response.ok) throw new Error(`Ошибка HTTP: ${response.status}`);

        const encryptedData = await response.json();
        const data = encryptedClient.decryptResponse(encryptedData);

        if (data.error) {
            showError(data.error);
        } else {
            displayResults('Текущий адрес', {
                '📍 Адрес': data.address || 'Не определен',
                '🌐 Карта': data.map_link ? `<a href="${data.map_link}" target="_blank">Открыть карту</a>` : 'Нет данных'
            });
        }
    } catch (error) {
        showError(error.message);
    }
}

function showPlacesSearchDialog() {
    showSearchDialog('places');
}

function showExactSearchDialog() {
    showSearchDialog('exact');
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
                <h3>${item.name || 'Без названия'}</h3>
                <p>📍 ${item.address || 'Адрес не указан'}</p>
                ${item.rating ? `<p>★ Рейтинг: ${item.rating}</p>` : ''}
                ${item.map_link ? `<a href="${item.map_link}" target="_blank" class="map-link">🌐 Открыть на карте</a>` : ''}
            </div>
        `).join('');
    } else if (typeof data === 'object') {
        content.innerHTML = `
            <div class="result-item">
                <h3>${data.name || 'Без названия'}</h3>
                <p>📍 ${data.address || 'Адрес не указан'}</p>
                ${data.rating ? `<p>★ Рейтинг: ${data.rating}</p>` : ''}
                ${data.map_link ? `<a href="${data.map_link}" target="_blank" class="map-link">🌐 Открыть на карте</a>` : ''}
            </div>
        `;
    } else {
        content.innerHTML = `<p>${data}</p>`;
    }

    dialog.classList.remove('hidden');
    dialog.style.animation = 'fadeInUp 0.3s ease-out';
}

function displayExactResult(data) {
    const dialog = document.getElementById('result-dialog');
    const content = document.getElementById('result-content');

    let html = `
        <div class="exact-result">
            <h3>${escapeHtml(data.name)}</h3>
            <div class="info-item">
                <span class="label">📍 Адрес:</span>
                <span class="value">${escapeHtml(data.address)}</span>
            </div>
    `;

    if (data.rating && data.rating !== "н/д") {
        html += `
            <div class="info-item">
                <span class="label">★ Рейтинг:</span>
                <span class="value">${escapeHtml(data.rating)}</span>
            </div>
        `;
    }

    if (data.map_link) {
        html += `
            <div class="info-item">
                <span class="label">🌐 Карта:</span>
                <a href="${escapeHtml(data.map_link)}" target="_blank" class="value">
                    Открыть на карте
                </a>
            </div>
        `;
    }

    if (data.description) {
        html += `
            <div class="info-item">
                <span class="label">📝 Описание:</span>
                <span class="value">${escapeHtml(data.description)}</span>
            </div>
        `;
    }

    html += `</div>`;
    content.innerHTML = html;
    document.getElementById('result-title').textContent = "Результат поиска";

    dialog.classList.remove('hidden');
    dialog.style.animation = 'fadeInUp 0.3s ease-out';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Геолокация не поддерживается"));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            position => resolve({
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            }),
            error => {
                console.error('Geolocation error:', error);
                reject(new Error("Разрешите доступ к геолокации"));
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    });
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.dialog') && !e.target.closest('.neon-btn')) {
        closeAllDialogs();
    }
});

const errorStyle = document.createElement('style');
errorStyle.textContent = `
    .error-message {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 50, 50, 0.9);
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
        z-index: 2000;
        animation: fadeIn 0.3s ease-out;
    }

    .error-message.fade-out {
        animation: fadeOut 0.5s ease-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translate(-50%, -20px); }
        to { opacity: 1; transform: translate(-50%, 0); }
    }

    @keyframes fadeOut {
        from { opacity: 1; transform: translate(-50%, 0); }
        to { opacity: 0; transform: translate(-50%, -20px); }
    }

    .result-link {
        color: #00ff9d;
        text-decoration: none;
        transition: all 0.3s;
    }

    .result-link:hover {
        color: #00ffcc;
        text-shadow: 0 0 5px #00ff9d;
    }

    .map-link {
        display: inline-block;
        margin-top: 10px;
        color: #00ff9d;
        text-decoration: none;
        transition: all 0.3s;
    }

    .map-link:hover {
        color: #00ffcc;
        text-shadow: 0 0 5px #00ff9d;
    }
`;
document.head.appendChild(errorStyle);
