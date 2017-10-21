import logging
import sys

import discord
from discord.ext.commands import Bot as DiscordBot
from motor.motor_asyncio import AsyncIOMotorClient
import aioredis

from destroyer.context import Context

log = logging.getLogger(__name__)
DESCRIPTION = "An anti-raid, and cross server ban bot by memework."

COGS = [
    'admin',
    'spam'
]

class Bot(DiscordBot):
    """ Main bot class for destroyer """
    def __init__(self, *, config):
        super().__init__(
            command_prefix=self.get_prefix,
            pm_help=None,
            description=DESCRIPTION
        )

        # Load config
        self.config = config

        # Connect to mongo
        self._mongo = AsyncIOMotorClient(self.config['database'])
        self.db = self._mongo['destroyer']
        
        # Redis
        _redis_future = aioredis.create_pool(
            ('localhost', 6379),
            db=11
        )
        self.redis = self.loop.run_until_complete(_redis_future)

        log.info('Loading cogs.')
        self.load_cogs()
     
    async def get_prefix(self, message):
        if not self.config['prefix']:
            return 'b!'
        return self.config['prefix']
    
    def load_cogs(self):
        for cog in COGS:
            try:
                self.load_extension(f'destroyer.cogs.{cog}')
                log.info(f'Loaded {cog}')
            except Exception as err:
                log.error(f'Failed to load cog {cog}', exc_info=True)

    def clean(self, content):
        # thx dogbot & luna :mmlol:
        content = content.replace('`', '\'')
        content = content.replace('@', '@\u200b')
        content = content.replace('&', '&\u200b')
        content = content.replace('<#', '<#\u200b')
        return content
    
    async def global_ban(self, user):
        """ Globally bans a user from every guild the bot is in. """
        for guild in self.bot.guilds:
            try:
                await guild.ban(user, reason='Cross ban: spammer.')
            except discord.Forbidden as err:
                log.error('Couldn\'t ban %d on %d', user.id, guild.id)

        log.info('Globally banned user (%d)', user.id)

    # Event handlers
    async def on_ready(self):
        log.info('Logged in to discord as %s (%d)', self.user, self.user.id)

    async def on_message(self, message):
        await self.db['messages'].insert_one(dict(message))

        author_id = message.author.id

        if message.author.bot:
            return # lol fuck bots!
        
        try:
            guild_id = message.guild.id
        except AttributeError:
            # we in a DM bois
            pass
        
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def on_command(self, ctx):
        # thanks luna
        content = self.clean(ctx.message.content)

        author = ctx.message.author
        guild = ctx.guild
        checks = [c.__qualname__.split('.')[0] for c in ctx.command.checks]
        location = '[DM]' if isinstance(ctx.channel, discord.DMChannel) else \
                   f'[Guild {guild.name} {guild.id}]'
        
        log.info('%s [cmd] %s(%d) "%s" checks=%s', location, author,
                 author.id, content, ','.join(checks) or '(none)')
    
    async def on_command_error(self, ctx, error):
        pass # TODO: Handle errors
