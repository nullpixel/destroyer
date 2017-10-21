from time import time

def ms_time():
    return int(time * 1000)

# thanks b1nzy, for leakybucket https://github.com/b1naryth1ef/rowboat/blob/95e568324cd5edef8e97f59873f59de98ddd1376/rowboat/util/leakybucket.py
INCREMENT_SCRIPT = '''
local key = KEYS[1]
-- Clear out expired water drops
redis.call("ZREMRANGEBYSCORE", KEYS[1], "-inf", ARGV[2])
-- Add our keys
for i=1,ARGV[1] do
  redis.call("ZADD", KEYS[1], ARGV[3], ARGV[3] + i)
end
redis.call("EXPIRE", KEYS[1], ARGV[4])
return redis.call("ZCOUNT", KEYS[1], "-inf", "+inf")
'''

GET_SCRIPT = '''
local key = KEYS[1]
-- Clear out expired water drops
redis.call("ZREMRANGEBYSCORE", KEYS[1], "-inf", ARGV[1])
return redis.call("ZCOUNT", KEYS[1], "-inf", "+inf")
'''

class Bucket:
    def __init__(self, redis, key_format, max_actions, time_period):
        self.redis = redis
        self.key_format = key_format
        self.max_actions = max_actions
        self.time_period = time_period
    
        self._increment_script = self.redis.script_load(INCREMENT_SCRIPT)
        self._get_script = self.redis.script_load(GET_SCRIPT)
    
    async def incr(self, key, amount=1):
        key = self.key_format.format(key)
        return int(
            await self._increment_script(
                keys=[key],
                args=[
                    amount,
                    ms_time() - self.time_period,
                    ms_time(),
                    (self.time_period * 2) / 1000,
                ]
            )
        )
    
    def check(self, key, amount=1):
        count = await self.incr(key, amount)
        if count >= self.max_actions:
            return False
        return True
    
    async def get(self, key):
        return int(await self._get_script(self.key_format.format(key)))

    async def clear(self, key):
        return await self.redis.zremrangebyscore(self.key_format.format(key), '-inf', '+inf')
    
    async def count(self, key):
        return await self.redis.zcount(self.key_fmt.format(key), '-inf', '+inf')

    def size(self, key):
        res = map(int, await self.redis.zrangebyscore(self.key_format.format(key), '-inf', '+inf'))
        if len(res) <= 1:
            return 0
        return (res[-1] - res[0]) / 1000.0