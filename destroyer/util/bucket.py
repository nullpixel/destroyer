from time import time

def ms_time():
    return int(time() * 1000)

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

        self._increment_script = None
        self._get_script = None

    async def _load_scripts(self):
        with await self.redis as conn:
            self._increment_script = await conn.script_load(INCREMENT_SCRIPT)
            self._get_script = await conn.script_load(GET_SCRIPT)

    async def incr(self, key, amount=1):
        if self._increment_script is None:
            await self._load_scripts()

        key = self.key_format.format(key)
        with await self.redis as conn:
            return int(
                await conn.evalsha(
                    self._increment_script,
                    keys=[key],
                    args=[
                        amount,
                        ms_time() - self.time_period,
                        ms_time(),
                        int(self.time_period * 2 / 1000),
                    ]
                )
            )
    
    async def check(self, key, amount=1):
        count = await self.incr(key, amount)
        if count >= self.max_actions:
            return False
        return True
    
    async def get(self, key):
        if self._get_script is None:
            await self._load_scripts()

        with await self.redis as conn:
            return int(await conn.evalsha(
                self._get_script,
                keys=[self.key_format.format(key)]
                )
            )

    async def clear(self, key):
        with await self.redis as conn:
            return await conn.zremrangebyscore(self.key_format.format(key), '-inf', '+inf')
    
    async def count(self, key):
        with await self.redis as conn:
            return await conn.zcount(self.key_format.format(key), '-inf', '+inf')

    async def size(self, key):
        with await self.redis as conn:
            res = map(int, await conn.zrangebyscore(self.key_format.format(key), '-inf', '+inf'))
            if len(res) <= 1:
                return 0
            return (res[-1] - res[0]) / 1000.0
