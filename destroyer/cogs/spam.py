import logging
import time

from discord.ext import commands

from destroyer.util.bucket import Bucket
from destroyer.spam.rules import messages, mentions
from destroyer.spam.violation import Violation
from destroyer.cogs.cog import Cog

log = logging.getLogger(__name__)

class Spam(Cog):
    """ Anti-spam plugin """
    
    def check(message):
        def check_rule(rule, func):
            bucket = rule.get_bucket(self.bot.redis, message.guild.id)

            if not bucket.check(message.author.id, func(message) if callable(func) else func):
                raise Violation(rule, message)
        
        check_rule(messages, 1)
        check_rule(mentions, lambda message: len(message.mentions))

    def violate(self, violation):
        key = f'lv:{violation.member.guild.id}:{violation.member.id}'
        last_violation = int(await self.redis.get(key) or 0)
        await self.redis.setex(key, 60, int(time.time()))

        if not last_violation > time.time() - 10:
            await self.bot.global_ban(violation.member)

    # Event handlers
    async def on_message(self, message):
        if not message.guild:
            return

        try:
            check(message)
        except Violation as violation:
            

    async def on_member_ban(self, guild, user):
        # TODO: don't do this at all
        # only ban people when the bot _knows_ they are a spammer
        await self.bot.global_ban(user)

def setup(bot):
    bot.add_cog(Spam(bot))