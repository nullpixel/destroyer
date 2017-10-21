from destroyer.util.bucket import Bucket

class Rule:
    # TODO: Document
    def __init__(self, name: str, count: int, interval: int):
        self.name = name
        self.count = count # amount to trip at
        self.interval = interval
        
        self.spam_key = 'spam:{}:{}:{}'.format(self.name, '{}', '{}')

    def get_bucket(redis, guild_id):
        bucket = getattr(self, f'_cached_{guild_id}_{self.name}_bucket')
        if not bucket:
            bucket = Bucket(redis, self.spam_key.format(guild_id, '{}'), self.count, self.interval * 1000)
            setattr(self, f'_cached_{guild_id}_{self.name}_bucket', bucket)
        return bucket

# TODO: Revise count & interval
messages = Rule('max_messages', 100, 10)
mentions = Rule('max_mentions', 100, 10)