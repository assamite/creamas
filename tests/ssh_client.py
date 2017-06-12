import asyncio, asyncssh, sys

class MySSHClientSession(asyncssh.SSHClientSession):
    def data_received(self, data, datatype):
        print(data, end='')

    def connection_lost(self, exc):
        if exc:
            print('SSH session error: ' + str(exc), file=sys.stderr)

class MySSHClient(asyncssh.SSHClient):
    def connection_made(self, conn):
        print('Connection made to %s.' % conn.get_extra_info('peername')[0])

    def auth_completed(self):
        print('Authentication successful.')

async def run_client(username, password, command):
    conn, client = await asyncssh.create_connection(MySSHClient,
                                                    'localhost',
                                                    8022,
                                                    username=username,
                                                    password=password,
                                                    known_hosts=None)

    async with conn:
        chan, session = await conn.create_session(MySSHClientSession, command)
        await chan.wait_closed()


if __name__ == "__main__":
    import argparse
    desc="Start simple SSH client to test DistributedEnvironment"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='port',
                        help="Port number for the server", default=8022)
    args = parser.parse_args()
    try:
        port = '--port 5600'
        prefix = 'source ~/git/mas/env/bin/activate && '
        cmd = 'source ~/git/mas/env/bin/activate &&  python ~/git/mas/creamas/examples/grid/spawn_test_node.py --agent_cls grid_agent:ExampleGridAgent --port 5600'
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_client('test', 'test', cmd))
    except (OSError, asyncssh.Error) as exc:
        sys.exit('SSH connection failed: ' + str(exc))