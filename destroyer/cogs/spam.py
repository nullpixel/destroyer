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

    async def check(self, message):
        async def check_rule(rule, func):
            bucket = rule.get_bucket(self.redis, message.guild.id)

            if not await bucket.check(message.author.id, func(message) if callable(func) else func):
                raise Violation(rule, message)

        await check_rule(messages, 1)
        await check_rule(mentions, lambda msg: len(msg.mentions))

    async def violate(self, violation):
        key = f'lv:{violation.guild.id}:{violation.user.id}'
        with await self.redis as conn:
            last_violation = int(await conn.get(key) or 0)
            await conn.setex(key, 60, int(time.time()))

        if not last_violation > time.time() - 10:
            await self.bot.global_ban(violation.user)

    # Event handlers
    async def on_message(self, message):
        if not message.guild:
            return

        try:
            await self.check(message)
        except Violation as violation:
            await self.violate(violation)

    async def on_member_ban(self, guild, user):
        # TODO: don't do this at all
        # only ban people when the bot _knows_ they are a spammer
        await self.bot.global_ban(user)


def setup(bot):
    bot.add_cog(Spam(bot))
