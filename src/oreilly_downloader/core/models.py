from typing import List, Optional, Dict, Any

class Video:
    def __init__(self, title: str, url: str):
        self.title: str = title
        self.url: str = url
        self.m3u8_url: Optional[str] = None
        self.transcript: Optional[str] = None

class Lesson:
    def __init__(self, title: str, videos: Optional[List['Video']] = None):
        self.title: str = title
        self.videos: List['Video'] = videos or []

class Module:
    def __init__(self, title: str, lessons: Optional[List['Lesson']] = None):
        self.title: str = title
        self.lessons: List['Lesson'] = lessons or []

class Course:
    def __init__(self, title: str, modules: Optional[List['Module']] = None, structure: Optional[Dict[str, Any]] = None):
        self.title: str = title
        self.modules: List['Module'] = modules or []
        self.structure: Dict[str, Any] = structure or {}
