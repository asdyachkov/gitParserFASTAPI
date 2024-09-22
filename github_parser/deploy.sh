# Настройки для базы данных
DB_HOST=""
DB_PORT=""
DB_USER=""
DB_PASSWORD=""
DB_NAME=""

# Название функции
FUNCTION_NAME=""
# ID Сервисного аккаунта с необходимым набором прав
SERVICE_ACCOUNT_ID=""

# Папка с исходным кодом
SOURCE_DIR="./"

# Создание временной папки для зависимостей и файлов
TEMP_DIR=$(mktemp -d)
echo "Создана временная папка для зависимостей: $TEMP_DIR"

# Упаковка функции и установка зависимостей в эту папку
echo "Упаковка функции..."
pip install -r requirements.txt -t "$TEMP_DIR" --quiet

# Копируем исходный код и requirements.txt в эту папку
cp index.py "$TEMP_DIR"
cp requirements.txt "$TEMP_DIR"

# Переходим в временную папку и создаем ZIP-архив
cd "$TEMP_DIR" || exit
zip -r function.zip index.py requirements.txt

# Перемещаем ZIP-архив в исходную директорию
mv function.zip "$SOURCE_DIR/function.zip"
echo "ZIP-архив создан: $SOURCE_DIR/function.zip"

# Проверка, установлен ли Yandex Cloud CLI
if ! command -v yc &> /dev/null
then
    echo "Yandex Cloud CLI не установлен. Установите его и выполните yc init."
    exit
fi

# Создание функции
echo "Создаем функцию в Яндекс.Облаке..."
yc serverless function create --name $FUNCTION_NAME

# Загрузка новой версии функции с переменными окружения
echo "Загружаем функцию..."
yc serverless function version create \
  --function-name $FUNCTION_NAME \
  --runtime python311 \
  --entrypoint index.handler \
  --memory 256m \
  --execution-timeout 60s \
  --environment DB_HOST=$DB_HOST,DB_PORT=$DB_PORT,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,DB_NAME=$DB_NAME \
  --source-path "$SOURCE_DIR/function.zip"

# Установка крон-триггера для периодического запуска каждый час
yc serverless trigger create timer \
  --name "${FUNCTION_NAME}-trigger" \
  --cron-expression "0 * ? * * *" \
  --invoke-function-name $FUNCTION_NAME \
  --invoke-function-service-account-id $SERVICE_ACCOUNT_ID

echo "Деплой завершен."

# Удаление временной папки
rm -rf "$TEMP_DIR"
echo "Временная папка удалена."
