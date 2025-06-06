document.addEventListener('DOMContentLoaded', () => {
    const fromCurrency = document.getElementById('fromCurrency');
    const toCurrency = document.getElementById('toCurrency');
    const fromAmount = document.getElementById('fromAmount');
    const toAmount = document.getElementById('toAmount');
    const swapButton = document.getElementById('swapButton');
    const rateElement = document.getElementById('rate');

    // 貨幣列表
    const currencies = [
        'AED', 'ARS', 'AUD', 'BGN', 'BRL', 'BSD', 'CAD', 'CHF', 'CLP', 'CNY',
        'COP', 'CZK', 'DKK', 'DOP', 'EGP', 'EUR', 'FJD', 'GBP', 'GTQ', 'HKD',
        'HRK', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'JPY', 'KRW', 'KZT', 'MXN',
        'MYR', 'NOK', 'NZD', 'PAB', 'PEN', 'PHP', 'PKR', 'PLN', 'PYG', 'RON',
        'RUB', 'SAR', 'SEK', 'SGD', 'THB', 'TRY', 'TWD', 'UAH', 'USD', 'UYU',
        'VND', 'ZAR'
    ];

    // 初始化貨幣選項
    function initializeCurrencies() {
        currencies.forEach(currency => {
            const fromOption = document.createElement('option');
            const toOption = document.createElement('option');
            
            fromOption.value = currency;
            fromOption.textContent = currency;
            
            toOption.value = currency;
            toOption.textContent = currency;
            
            fromCurrency.appendChild(fromOption);
            toCurrency.appendChild(toOption);
        });

        // 設定預設值
        fromCurrency.value = 'USD';
        toCurrency.value = 'TWD';
    }

    // 獲取匯率
    async function getExchangeRate(from, to) {
        try {
            const response = await fetch(`https://api.exchangerate-api.com/v4/latest/${from}`);
            const data = await response.json();
            return data.rates[to];
        } catch (error) {
            console.error('Error fetching exchange rate:', error);
            return 1;
        }
    }

    // 更新匯率和金額
    async function updateExchange() {
        const from = fromCurrency.value;
        const to = toCurrency.value;
        const amount = fromAmount.value;

        const rate = await getExchangeRate(from, to);
        const convertedAmount = (amount * rate).toFixed(2);

        toAmount.value = convertedAmount;
        rateElement.textContent = `1 ${from} = ${rate.toFixed(4)} ${to}`;
    }

    // 交換貨幣
    function swapCurrencies() {
        const tempCurrency = fromCurrency.value;
        fromCurrency.value = toCurrency.value;
        toCurrency.value = tempCurrency;
        updateExchange();
    }

    // 事件監聽器
    fromCurrency.addEventListener('change', updateExchange);
    toCurrency.addEventListener('change', updateExchange);
    fromAmount.addEventListener('input', updateExchange);
    swapButton.addEventListener('click', swapCurrencies);

    // 初始化
    initializeCurrencies();
    updateExchange();
}); 