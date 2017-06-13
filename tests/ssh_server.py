'''
Utilities for testing ds-module.
'''
import subprocess
import os

import asyncio, asyncssh, crypt, sys


passwords = {'guest': '',              # guest account with no password
             'test': 'w1jLrFgB7XHs.'   # password of 'test'
            }


async def handle_client(process):
    process.stdout.write('Welcome to my SSH server, %s!\n' %
                         process.channel.get_extra_info('username'))
    line = await process.stdin.readline()
    process.stdout.write("{}\n".format(line))
    process.exit(0)


class MySSHServerSession(asyncssh.SSHServerSession):
    def __init__(self):
        self._input = ''
        self._total = 0

    def connection_made(self, chan):
        self._chan = chan

    def shell_requested(self):
        print("Shell requested.")
        return True

    def exec_requested(self, command):
        self._command = command
        print("Exec requested: {}".format(self._command))
        return True

    def subsystem_requested(self, subsystem):
        print("Subsystem requested: {}".format(subsystem))
        return True

    def session_started(self):
        print("Sessions started! {}".format(self._command))
        ret = subprocess.run(args=[self._command], stdout=subprocess.PIPE, shell=True)
        str_ret = ret.stdout.decode('utf-8')
        self._chan.write(str_ret)
        self._chan.flush()

    def data_received(self, data, datatype):
        print("Data received: {}".format(data))

    def eof_received(self):
        self._chan.exit(0)

    def break_received(self, msec):
        self.eof_received()


class MySSHServer(asyncssh.SSHServer):

    def connection_made(self, conn):
        print('SSH connection received from %s.' %
                  conn.get_extra_info('peername')[0])

    def connection_lost(self, exc):
        loop = asyncio.get_event_loop()
        loop.stop()

    def begin_auth(self, username):
        # If the user's password is the empty string, no auth is required
        return passwords.get(username) != ''

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        pw = passwords.get(username, '*')
        return crypt.crypt(password, pw) == pw

    def session_requested(self):
        return MySSHServerSession()


async def start_server(port):
    await asyncssh.create_server(MySSHServer, 'localhost', port,
                                 server_host_keys=['ssh_test_rsa'])


def run_server(port=8022):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(start_server(port=port))
    except (OSError, asyncssh.Error) as exc:
        sys.exit('Error starting server: ' + str(exc))

    loop.run_forever()


if __name__ == "__main__":
    import argparse
    desc="Start simple SSH server to test DistributedEnvironment"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='port',
                        help="Port number for the server", default=8022)
    args = parser.parse_args()
    print("Starting server in port {}".format(args.port))
    run_server(args.port)