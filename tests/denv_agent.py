'''
Simple test agent for distributed environments.
'''
import aiomas

from creamas import CreativeAgent

class DenvTestAgent(CreativeAgent):

    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs