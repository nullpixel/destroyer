import logging
import sys
import asyncio

from ruamel.yaml import YAML

from destroyer.bot import Bot

log = logging.getLogger(__name__)

with open('config.yaml', 'r') as config_file:
    config = YAML(typ='safe').load(config_file)

log.info('Setting up uvloop')
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    log.info('Uvloop not found')
    pass # use asyncio

bot = Bot(
    config=config
)
bot.run(config['token'])