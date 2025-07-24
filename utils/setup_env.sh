#!/bin/bash

# Пример установки переменной окружения для Google Drive API

# Замените путь на ваш путь к файлу с ключом Service Account
export GOOGLE_APPLICATION_CREDENTIALS="/home/dukhanin/ai-hr/app/back/creds/googlecreadofmine.json"

echo "Переменная окружения GOOGLE_APPLICATION_CREDENTIALS установлена:"
echo $GOOGLE_APPLICATION_CREDENTIALS

# Проверяем что файл существует
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ Файл с ключом найден"
else
    echo "❌ Файл с ключом НЕ найден! Проверьте путь"
fi

echo ""
echo "Для постоянной установки добавьте эту строку в ~/.bashrc:"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$GOOGLE_APPLICATION_CREDENTIALS\"" 