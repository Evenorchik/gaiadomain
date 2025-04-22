import aiohttp
import asyncio
import random
import logging
import sys
import os
from typing import List, Dict, Optional

# Logging setup
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
        """Bot initialization."""
        # Get domain name
        self.domain = os.getenv("DOMAIN")
        if not self.domain:
            self.domain = input("Enter domain name (e.g., mydomain.gaia.domains): ").strip()
        if not self.domain:
            logger.error("Error: domain name not specified!")
            sys.exit(1)

        # Get api key
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            self.api_key = input("Enter your API key: ").strip()
        if not self.api_key:
            logger.error("Error: API key not specified!")
            sys.exit(1)

        # Creating URL
        self.url = f"https://{self.domain}/v1/chat/completions"
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Setup from env
        self.retry_count = int(os.getenv("RETRY_COUNT", "3"))
        self.retry_delay = int(os.getenv("RETRY_DELAY", "5"))
        self.timeout = int(os.getenv("TIMEOUT", "60"))

        # Init lists
        self.roles: List[str] = []
        self.phrases: List[str] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Bot initialization, loading data from files."""
        try:
            self.roles = self.load_from_file("roles.txt")
            self.phrases = self.load_from_file("phrases.txt")
            self.session = aiohttp.ClientSession()
            logger.info("Bot successfully initialized")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            sys.exit(1)

    @staticmethod
    def load_from_file(file_name: str) -> List[str]:
        """Load data from file with error handling."""
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                data = [line.strip() for line in file if line.strip()]
                if not data:
                    raise ValueError(f"File {file_name} is empty")
                return data
        except FileNotFoundError:
            logger.error(f"Error: file {file_name} not found!")
            sys.exit(1)

    def generate_message(self) -> List[Dict[str, str]]:
        """Generate messages to send a request."""
        # Creating msg
        user_message = {
            "role": "user",
            "content": random.choice(self.phrases)
        }
        # Choosing role
        other_roles = [r for r in self.roles if r.lower() != "user"]
        other_message = {
            "role": random.choice(other_roles) if other_roles else "assistant",
            "content": random.choice(self.phrases)
        }
        return [user_message, other_message]

    async def send_request(self, messages: List[Dict[str, str]]) -> None:
        """Send API request with error handling and retries."""
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
                        logger.warning(f"Attempt {attempt + 1}/{self.retry_count}: status {response.status}")
            except asyncio.TimeoutError:
                logger.warning(f"Attempt {attempt + 1}/{self.retry_count}: timeout")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.retry_count}: error: {e}")

            if attempt < self.retry_count - 1:
                await asyncio.sleep(self.retry_delay)

    def log_success(self, question: str, result: Dict) -> None:
        """Log successful response."""
        try:
            response = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Response handling error: {e}")
            response = "N/A"
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {response}")
        logger.info("=" * 50)

    async def run(self) -> None:
        """Main bot loop."""
        await self.initialize()
        logger.info("Bot started and ready to work")

        try:
            while True:
                messages = self.generate_message()
                await self.send_request(messages)
                await asyncio.sleep(1)  # Small delay between requests
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            if self.session:
                await self.session.close()

if __name__ == "__main__":
    bot = GaiaBot()
    asyncio.run(bot.run())
