import traceback
import logging

from discord.ext import commands

from .cog import Cog

log = logging.getLogger(__name__)

class Admin(Cog):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """ Stops the bot. """
        log.info('Shutting down :(')
        await self.bot.logout()
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, cog_name: str):
        """ Loads a cog. """
        try:
            self.bot.load_extension(f'destroyer.cogs.{cog_name}')
        except Exception as err:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
            return
        log.info(f'Loaded {cog_name}')
        await ctx.send(f':ok_hand: `{cog_name}` loaded.')
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, cog_name: str):
        """ Unloads a cog. """
        self.bot.unload_extension(f'destroyer.cogs.{cog_name}')
        log.info(f'Unloaded {cog_name}')
        await ctx.send(f':ok_hand: `{cog_name}` unloaded.')

    # TODO: add more admin commands

def setup(bot):
    bot.add_cog(Admin(bot))