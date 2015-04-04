class Event(object):
    def __init__(self):
        self.__handlers = set()

    def subscribe(self, handler: callable):
        if handler not in self.__handlers:
            self.__handlers.add(handler)

    def unsubscribe(self, handler: callable):
        if handler in self.__handlers:
            self.__handlers.remove(handler)

    def raise_event(self, *args, **kwargs):
        for handler in self.__handlers:
            handler(*args, **kwargs)