import re
class SanityUtils:
    @staticmethod
    def sanitize_filename(name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*]', '-', name)
        name = name.replace('\n', ' ').replace('\r', '')
        return " ".join(name.split()).strip()
