from discord.ext.commands import Context as DiscordContext

class Context(DiscordContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    # TODO: add context stuff