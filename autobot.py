import aiohttp
import asyncio
import random
import logging
import sys
import os
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gaia_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class GaiaBot:
    def __init__(self):
        """Инициализация бота."""
        # Получаем доменное имя: из переменной окружения или запрашиваем у пользователя
        self.domain = os.getenv("DOMAIN")
        if not self.domain:
            self.domain = input("Введите доменное имя (например, mydomain.gaia.domains): ").strip()
        if not self.domain:
            logger.error("Ошибка: доменное имя не задано!")
            sys.exit(1)
        
        # Получаем API ключ: из переменной окружения или запрашиваем у пользователя
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            self.api_key = input("Введите ваш API ключ: ").strip()
        if not self.api_key:
            logger.error("Ошибка: API ключ не задан!")
            sys.exit(1)
        
        # Формируем URL для отправки запроса, добавляя нужный путь
        self.url = f"https://{self.domain}/v1/chat/completions"
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Дополнительные настройки из переменных окружения
        self.retry_count = int(os.getenv("RETRY_COUNT", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "5"))
        self.timeout = int(os.getenv("TIMEOUT", "60"))
        
        # Инициализация списков для ролей и фраз, а также переменной для HTTP сессии
        self.roles: List[str] = []
        self.phrases: List[str] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Инициализация бота, загрузка данных из файлов."""
        try:
            self.roles = self.load_from_file("roles.txt")
            self.phrases = self.load_from_file("phrases.txt")
            self.session = aiohttp.ClientSession()
            logger.info("Бот успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            sys.exit(1)

    @staticmethod
    def load_from_file(file_name: str) -> List[str]:
        """Загрузка данных из файла с обработкой ошибок."""
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                data = [line.strip() for line in file if line.strip()]
                if not data:
                    raise ValueError(f"Файл {file_name} пуст")
                return data
        except FileNotFoundError:
            logger.error(f"Ошибка: файл {file_name} не найден!")
            sys.exit(1)

    def generate_message(self) -> List[Dict[str, str]]:
        """Генерация сообщений для отправки запроса."""
        # Формируем сообщение от пользователя
        user_message = {
            "role": "user",
            "content": random.choice(self.phrases)
        }
        # Выбираем случайную роль (отличную от "user", если такая есть)
        other_roles = [r for r in self.roles if r.lower() != "user"]
        other_message = {
            "role": random.choice(other_roles) if other_roles else "assistant",
            "content": random.choice(self.phrases)
        }
        return [user_message, other_message]

    async def send_request(self, messages: List[Dict[str, str]]) -> None:
        """Отправка API запроса с обработкой ошибок и повторными попытками."""
        for attempt in range(self.retry_count):
            try:
                async with self.session.post(
                    self.url,
                    json={"messages": messages},
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log_success(messages[0]["content"], result)
                        return
                    else:
                        logger.warning(f"Попытка {attempt + 1}/{self.retry_count}: статус {response.status}")
            except asyncio.TimeoutError:
                logger.warning(f"Попытка {attempt + 1}/{self.retry_count}: тайм-аут")
            except Exception as e:
                logger.error(f"Попытка {attempt + 1}/{self.retry_count}: ошибка: {e}")
            
            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)

    def log_success(self, question: str, result: Dict) -> None:
        """Логирование успешного ответа."""
        try:
            response = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка обработки ответа: {e}")
            response = "N/A"
        logger.info(f"Вопрос: {question}")
        logger.info(f"Ответ: {response}")
        logger.info("=" * 50)

    async def run(self) -> None:
        """Основной цикл работы бота."""
        await self.initialize()
        logger.info("Бот запущен и готов работать")
        
        try:
            while True:
                messages = self.generate_message()
                await self.send_request(messages)
                await asyncio.sleep(1)  # Небольшая задержка между запросами
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        finally:
            if self.session:
                await self.session.close()

if __name__ == "__main__":
    bot = GaiaBot()
    asyncio.run(bot.run())
