from abc import ABC, abstractmethod
import json
from bs4 import BeautifulSoup

class BaseParser(ABC):
    @abstractmethod
    def parse(self, data):
        pass

class JSONParser(BaseParser):
    def parse(self, data):
        return json.loads(data)

class HTMLParser(BaseParser):
    def parse(self, data):
        soup = BeautifulSoup(data, 'html.parser')
        return {
            "title": soup.title.string if soup.title else None,
            "body": soup.body.text if soup.body else None
        }

# Exemple d'utilisation
if __name__ == "__main__":
    json_parser = JSONParser()
    html_parser = HTMLParser()

    # Exemple de parsing JSON
    json_data = '{"key": "value"}'
    print(json_parser.parse(json_data))

    # Exemple de parsing HTML
    html_data = "<html><head><title>Test</title></head><body>Content</body></html>"
    print(html_parser.parse(html_data))
