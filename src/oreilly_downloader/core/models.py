class Video:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.m3u8_url = None
        self.transcript = None

class Lesson:
    def __init__(self, title, videos=None):
        self.title = title
        self.videos = videos or []

class Module:
    def __init__(self, title, lessons=None):
        self.title = title
        self.lessons = lessons or []

class Course:
    def __init__(self, title, modules=None, structure=None):
        self.title = title
        self.modules = modules or []
        self.structure = structure or {}
