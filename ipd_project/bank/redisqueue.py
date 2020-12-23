import redis
class RedisQueue(object):
    """
        Redis Lists are an ordered list, First In First Out Queue
        Redis List pushing new elements on the head (on the left) of the list.
        The max length of a list is 4,294,967,295
    """
    def __init__(self, name, **redis_kwargs):
        """
            host='localhost', port=6379, db=0
        """
        self.key = name
        self.rq = redis.Redis(**redis_kwargs)

    def getInstance(self):
        return self.rq
