#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import errno
import random

# Get correct path to files, based on platform
import platform
host = platform.node().split('.')[0]

sys.path[0:0] = [
    '/home/students/s4230085/public/' + host,
    '/Users/joel/co/thesis/src',
]

import marks

# Use generator if possible
try:
    range = xrange
except:
    pass


TEST_LOCATION = '/home/students/s4230085/public/csse2310/ass4/mtest'
TEST_LOCATION = '/Users/joel/Documents/UQ/2014-s2/csse2310/ass4/mtest'
COMPILE = "make"

DELAY = 2  # Delay (seconds) between starting server and starting clients.

# Information from setup.
CLIENT = ''
SERV = ''
PORTS = []
COMPILATION = {'errors': 0, 'warnings': 0}


def relpath(path, start='.'):
    """Create a relative path from the start directory.
    Adds './' if the file is in the start directory.
    """
    path = os.path.relpath(path, start)
    if not os.path.dirname(path):
        path = "./{0}".format(path)
    return path


def force_symlink(src, dst):
    """Create a symbolic link pointing to src named dst.
    If dst exists, overwrite with new src.
    """
    try:
        os.symlink(src, dst)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(dst)
            os.symlink(src, dst)


def setup_module(options):
    global CLIENT, SERV
    CLIENT = relpath(os.path.join(options['working_dir'], '2310client'))
    SERV = relpath(os.path.join(options['working_dir'], '2310serv'))

    # Create symlink to tests in working dir
    os.chdir(options['working_dir'])
    try:
        force_symlink(TEST_LOCATION, 'tests')
    except OSError:
        pass
    os.chdir(options['temp_dir'])

    # Get user's ports for testing
    if options.get('port', False) and isinstance(options['port'], basestring):
        port = options['port']
    else:
        p = marks.Process(['2310port'])
        port = p.readline_stdout().strip()

    PORTS.append(port)
    for i in range(1, 6):
        PORTS.append(str(int(port) + i))

    if not options.get('silent'):
        print('Using ports for testing:', ', '.join(PORTS), '\n')

    # Modify test environment when running tests (excl. explain mode).
    if not options.get('explain', False):
        # Compile program
        os.chdir(options['working_dir'])
        p = marks.Process(COMPILE.split())
        os.chdir(options['temp_dir'])

        # Count warnings and errors
        warnings = 0
        errors = 0
        while True:
            line = p.readline_stderr()
            if line == '':
                break
            if 'warning:' in line:
                warnings += 1
            if 'error:' in line:
                errors += 1
            print(line, end='')

        # Update count of warnings and errors.
        COMPILATION['errors'] = errors
        COMPILATION['warnings'] = warnings

        # Do not run tests if compilation failed.
        assert p.assert_exit_status(0)

        # Create symlink to tests within temp folder
        try:
            force_symlink(TEST_LOCATION, 'tests')
        except OSError:
            pass


class Client(marks.TestCase):

    timeout = 20

    @marks.ignore_result
    def test_compilation(self):
        # Record compilation results
        self.add_detail('errors', COMPILATION['errors'])
        self.add_detail('warnings', COMPILATION['warnings'])

    @marks.marks('client_args', category_marks=4)
    def test_args_usage_1(self):
        p = self.process([CLIENT], timeout=10)
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('client_args', category_marks=4)
    def test_args_usage_2(self):
        p = self.process([CLIENT, 'thing'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('client_args', category_marks=4)
    def test_args_usage_3(self):
        p = self.process([CLIENT, 'name', 'game'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('client_args', category_marks=4)
    def test_args_usage_4(self):
        p = self.process([CLIENT, 'name', 'game', PORTS[0], 'localhost', 'e'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('client_args', category_marks=4)
    def test_args_invplayer_1(self):
        p = self.process([CLIENT, '', 'game', '2310'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invplayer.err')
        self.assert_exit_status(p, 2)

    @marks.marks('client_args', category_marks=4)
    def test_args_invplayer_2(self):
        p = self.process([CLIENT, 'name\n', 'game', '2310'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invplayer.err')
        self.assert_exit_status(p, 2)

    @marks.marks('client_args', category_marks=4)
    def test_args_invgame_1(self):
        p = self.process([CLIENT, 'name', 'game\n', '2310'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invgame.err')
        self.assert_exit_status(p, 3)

    @marks.marks('client_args', category_marks=4)
    def test_args_invgame_2(self):
        p = self.process([CLIENT, 'name', '', '2310'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invgame.err')
        self.assert_exit_status(p, 3)

    @marks.marks('client_args', category_marks=4)
    def test_args_invport_1(self):
        p = self.process([CLIENT, 'name', 'game', ''])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('client_args', category_marks=4)
    def test_args_invport_2(self):
        p = self.process([CLIENT, 'name', 'game', '100000'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('client_args', category_marks=4)
    def test_args_invport_3(self):
        p = self.process([CLIENT, 'name', 'game', '0'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('client_args', category_marks=4)
    def test_args_invport_4(self):
        p = self.process([CLIENT, 'name', 'game', '800test'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('client_args', category_marks=4)
    def test_args_conn_failed_1(self):
        p = self.process([CLIENT, 'name', 'game', '2310', 'bad'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/connfailed.err')
        self.assert_exit_status(p, 5)

    @marks.marks('client_args', category_marks=4)
    def test_args_conn_failed_2(self):
        p = self.process([CLIENT, 'name', 'game', '100'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/connfailed.err')
        self.assert_exit_status(p, 5)

# Do these two tests actually fit?

    @marks.marks('single_game', category_marks=10)
    def test_conn(self):
        serv = self.process(['nc', '-l', PORTS[0]])
        self.delay(DELAY)
        p = self.process([CLIENT, 'name', 'game', PORTS[0]])
        self.assert_stdout(serv, 'name\n')
        self.assert_stdout(serv, 'game\n')
        serv.kill()
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invsetup.err')
        self.assert_exit_status(p, 6)

    @marks.marks('single_game', category_marks=10)
    def test_invsetup_1(self):
        serv = self.process(['nc', '-l', PORTS[0]], timeout=int(10+DELAY))
        self.delay(DELAY)
        p = self.process([CLIENT, 'name', '2game', PORTS[0]], timeout=5)
        self.assert_stdout(serv, 'name\n')
        self.assert_stdout(serv, '2game\n')
        serv.send('2 C\n')
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invsetup.err')
        self.assert_exit_status(p, 6)

# Client single game

    @marks.marks('single_game', category_marks=10)
    def test_single_game_2A(self):
        serv = self.process(['nc', '-l', PORTS[0]], 'tests/c/g2A.s.in')
        self.delay(DELAY)
        c = self.process([CLIENT, 'name', '2g', PORTS[0]], 'tests/c/g2A.c.in')
        self.assert_stdout_matches_file(serv, 'tests/c/g2A.s.out')
        self.assert_stdout_matches_file(c, 'tests/c/g2A.c.out')
        self.assert_stderr(c, '')
        self.assert_exit_status(c, 0)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_2B(self):
        serv = self.process(['nc', '-l', PORTS[0]], 'tests/c/g2B.s.in')
        self.delay(DELAY)
        c = self.process([CLIENT, 'p2', '2g', PORTS[0]], 'tests/c/g2B.c.in')
        self.assert_stdout_matches_file(serv, 'tests/c/g2B.s.out')
        self.assert_stdout_matches_file(c, 'tests/c/g2B.c.out')
        self.assert_stderr(c, '')
        self.assert_exit_status(c, 0)

    @marks.marks('single_game', category_marks=10)
    def test_invmsg_1(self):
        self.process(['nc', '-l', PORTS[0]], 'tests/c/invmsg.1.in')
        self.delay(DELAY)
        p = self.process([CLIENT, 'name', 'game', PORTS[0]])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/c/invmsg.err')
        self.assert_exit_status(p, 7)

    @marks.marks('single_game', category_marks=10)
    def test_server_loss_1(self):
        self.process(['nc', '-l', PORTS[0]], 'tests/c/servloss.1.in')
        self.delay(DELAY)
        p = self.process([CLIENT, 'name', 'game', PORTS[0]])
        self.assert_stdout_matches_file(p, 'tests/c/servloss.1.out')
        self.assert_stderr_matches_file(p, 'tests/c/servloss.err')
        self.assert_exit_status(p, 8)

    @marks.marks('single_game', category_marks=10)
    def test_server_reject_1(self):
        self.process(['nc', '-l', PORTS[0]], 'tests/c/reject.1.s.in')
        self.delay(DELAY)
        p = self.process(
            [CLIENT, 'name', '2g', PORTS[0]], 'tests/c/reject.1.c.in')
        self.assert_stdout_matches_file(p, 'tests/c/reject.1.out')
        self.assert_stderr(p, '')
        self.assert_exit_status(p, 0)

    @marks.marks('single_game', category_marks=10)
    def test_server_reprompt_1(self):
        self.process(['nc', '-l', PORTS[0]], 'tests/c/g2A.s.in')
        self.delay(DELAY)
        p = self.process(
            [CLIENT, 'name', '2g', PORTS[0]], 'tests/c/reprompt.1.c.in')
        self.assert_stdout_matches_file(p, 'tests/c/reprompt.1.out')
        self.assert_stderr(p, '')
        self.assert_exit_status(p, 0)


class Server(marks.TestCase):

    timeout = 20

    @marks.marks('serv_args', category_marks=4)
    def test_args_usage_1(self):
        p = self.process([SERV])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('serv_args', category_marks=4)
    def test_args_usage_2(self):
        p = self.process([SERV, '2311', '2310'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/usage.err')
        self.assert_exit_status(p, 1)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_access_1(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/nothing'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckaccess.err')
        self.assert_exit_status(p, 2)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_access_2(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/locked'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckaccess.err')
        self.assert_exit_status(p, 2)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_read_1(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/bad.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckread.err')
        self.assert_exit_status(p, 3)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_read_2(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/bad3.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckread.err')
        self.assert_exit_status(p, 3)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_read_3(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/dash.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckread.err')
        self.assert_exit_status(p, 3)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_read_4(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/short.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckread.err')
        self.assert_exit_status(p, 3)

    @marks.marks('serv_args', category_marks=4)
    def test_args_deck_read_5(self):
        p = self.process([SERV, PORTS[1], PORTS[0], 'tests/long.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/deckread.err')
        self.assert_exit_status(p, 3)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_1(self):
        p = self.process([SERV, PORTS[1], '0', 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_2(self):
        p = self.process([SERV, PORTS[1], '800things', 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_3(self):
        p = self.process([
            SERV, PORTS[1],
            PORTS[0], 'tests/ex.deck', PORTS[0], 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_4(self):
        p = self.process([SERV, PORTS[0], PORTS[0], 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_5(self):
        p = self.process([SERV, PORTS[0], '0', 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_invport_6(self):
        p = self.process([SERV, '', PORTS[0], 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/invport.err')
        self.assert_exit_status(p, 4)

    @marks.marks('serv_args', category_marks=4)
    def test_args_port_listen_1(self):
        p = self.process([SERV, PORTS[1], '80', 'tests/ex.deck'])
        self.assert_stdout(p, '')
        self.assert_stderr_matches_file(p, 'tests/s/portlisten.err')
        self.assert_exit_status(p, 5)

    @marks.marks('serv_args', category_marks=4)
    def test_args_port_listen_2(self):
        self.process(['nc', '-l', PORTS[0]])
        self.delay(DELAY)
        serv = self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.assert_stdout(serv, '')
        self.assert_stderr_matches_file(serv, 'tests/s/portlisten.err')
        self.assert_exit_status(serv, 5)

    @marks.marks('serv_args', category_marks=4)
    def test_args_port_listen_3(self):
        serv = self.process([SERV, '80', PORTS[0], 'tests/ex.deck'])
        self.assert_stdout(serv, '')
        self.assert_stderr_matches_file(serv, 'tests/s/portlisten.err')
        self.assert_exit_status(serv, 5)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_2g(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        c1 = self.process([CLIENT, 'p1', '2g', PORTS[0]], 'tests/s/2g.p1.in')
        c2 = self.process([CLIENT, 'p2', '2g', PORTS[0]], 'tests/s/2g.p2.in')
        self.assert_stdout_matches_file(c1, 'tests/s/2g.p1.out')
        self.assert_stdout_matches_file(c2, 'tests/s/2g.p2.out')
        self.assert_stderr(c1, '')
        self.assert_stderr(c2, '')
        self.assert_exit_status(c1, 0)
        self.assert_exit_status(c2, 0)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_2long(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex3.deck'])
        self.delay(DELAY)
        name = 'Not-as-big-as-Medium-Sized-Jock-but-bigger-than-Wee-Jock Jock'
        c1 = self.process(
            [CLIENT, name, '2long', PORTS[0]], 'tests/s/2long.p1.in')
        c2 = self.process(
            [CLIENT, 'Aloysius Snuffleupagus', '2long', PORTS[0]],
            'tests/s/2long.p2.in')
        self.assert_stdout_matches_file(c1, 'tests/s/2long.p1.out')
        self.assert_stdout_matches_file(c2, 'tests/s/2long.p2.out')
        self.assert_stderr(c1, '')
        self.assert_stderr(c2, '')
        self.assert_exit_status(c1, 0)
        self.assert_exit_status(c2, 0)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_2very_long(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex3.deck'])
        self.delay(DELAY)
        c1 = self.process(
            [CLIENT, 'Aloysius Snuffleupagus', '2verylong', PORTS[0]],
            'tests/s/2long.p2.in')
        c2 = self.process(['nc', '-4', 'localhost', PORTS[0]])

        # Send input
        c2.send("{0}\n".format('X' * 5000))
        c2.send("2verylong\n")
        with open('tests/s/2verylong.p2.in', 'r') as f:
            for line in f:
                c2.send(line)

        self.assert_stdout_matches_file(c1, 'tests/s/2verylong.p1.out')
        self.assert_stdout_matches_file(c2, 'tests/s/2verylong.p2.out')
        self.assert_stderr(c1, '')
        self.assert_stderr(c2, '')
        self.assert_exit_status(c1, 0)
        self.assert_exit_status(c2, 0)

    def play_single_game_sort(self, port, game, four=False):
        c1 = self.process(
            [CLIENT, 'Alex', game, port], 'tests/s/{0}.A.in'.format(game))
        c3 = self.process(
            [CLIENT, 'bob', game, port], 'tests/s/{0}.C.in'.format(game))
        c2 = self.process(
            [CLIENT, 'Connor', game, port], 'tests/s/{0}.B.in'.format(game))
        if four:
            c4 = self.process(
                [CLIENT, 'gameover', game, port],
                'tests/s/{0}.D.in'.format(game))

        self.assert_stdout_matches_file(c1, 'tests/s/{0}.A.out'.format(game))
        self.assert_stdout_matches_file(c2, 'tests/s/{0}.B.out'.format(game))
        self.assert_stdout_matches_file(c3, 'tests/s/{0}.C.out'.format(game))
        self.assert_stderr(c1, '')
        self.assert_stderr(c2, '')
        self.assert_stderr(c3, '')
        self.assert_exit_status(c1, 0)
        self.assert_exit_status(c2, 0)
        self.assert_exit_status(c3, 0)

        if four:
            self.assert_stdout_matches_file(
                c4, 'tests/s/{0}.D.out'.format(game))
            self.assert_stderr(c4, '')
            self.assert_exit_status(c4, 0)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_3ga(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '3ga')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_3g4(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex4.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '3g4')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_3g4_bad(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex4.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '3g4_bad')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_3g5(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex5.deck'])
        self.delay(DELAY)
        self.play_single_game_sort(PORTS[0], '3g5')

    @marks.marks('single_game', category_marks=10)
    def test_single_game_3g6(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex6.deck'])
        self.delay(DELAY)
        self.play_single_game_sort(PORTS[0], '3g6')

    @marks.marks('single_game', category_marks=10)
    def test_single_game_4g7(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex7.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '4g7')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_4ga(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '4ga')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_4gb(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exb.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '4gb')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_4g5(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex5.deck'])
        self.delay(DELAY)
        self.play_single_game_sort(PORTS[0], '4g5', four=True)

    @marks.marks('single_game', category_marks=10)
    def test_single_error_1(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        c1 = self.process([CLIENT, 'p1', '2g', PORTS[0]], 'tests/s/e2g.p1.in')
        c2 = self.process([CLIENT, 'p2', '2g', PORTS[0]], 'tests/s/e2g.p2.in')
        self.assert_stdout_matches_file(c1, 'tests/s/e2g.p1.out')
        self.assert_stdout_matches_file(c2, 'tests/s/e2g.p2.out')
        self.assert_stderr(c1, '')
        self.assert_stderr_matches_file(c2, 'tests/c/eoi.err')
        self.assert_exit_status(c1, 0)
        self.assert_exit_status(c2, 9)

    @marks.marks('single_game', category_marks=10)
    def test_single_game_reprompt(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '2g_bad')])

    @marks.marks('single_game', category_marks=10)
    def test_single_game_no(self):
        self.process(
            [SERV, PORTS[1], PORTS[0], 'tests/ex.deck'], timeout=int(5+DELAY))
        self.delay(DELAY)
        c1 = self.process(
            ['nc', '-4', 'localhost', PORTS[0]], 'tests/s/no.p1.in')
        c2 = self.process(
            ['nc', '-4', 'localhost', PORTS[0]], 'tests/s/no.p2.in')
        self.assert_stdout_matches_file(c1, 'tests/s/no.p1.out')
        self.assert_stdout_matches_file(c2, 'tests/s/no.p2.out')

    def start_games(self, ports=(), players=2):
        if not 0 <= len(ports) < 5:
            raise ValueError('Can only have 1 to 5 ports')

        prefixes = ['p', 'player', 'name', 'Name of the player']
        clients = []

        for i, port in enumerate(ports):
            prefix = random.choice(prefixes)
            g = {'name': '{0}game{1}'.format(players, i), 'p': []}
            names = []
            for p in range(players):
                name = '{0}{1}'.format(prefix, p)
                names.append(name)
                c = {
                    'name': name,
                    'game': g,
                    'nc': self.process(['nc', '-4', 'localhost', port]),
                    'id': chr(ord('A') + p),
                }
                g['p'].append(c)
                clients.append(c)
            g['players'] = '{0}\n'.format('\n'.join(sorted(names)))

        # Randomise order of clients
        random.shuffle(clients)

        # Send setup information
        for c in clients:
            c['nc'].send('{0}\n{1}\n'.format(c['name'], c['game']['name']))

        # Get player count and IDs
        for c in clients:
            self.assert_stdout(c['nc'], "{0} {1}\n".format(players, c['id']))

        # Get player names
        for c in clients:
            self.assert_stdout(c['nc'], c['game']['players'])

        return clients

    def play_games(self, ports=(), shuffle=False):
        # Setup all players
        clients = []

        for i, (port, game) in enumerate(ports):
            num_players = 4
            try:
                num_players = int(game[0])
            except:
                pass

            for p in range(num_players):
                c = {
                    'name': 'p{0}'.format(p + 1),
                    'game': '{0}.{1}'.format(game, i),
                    'port': port,
                }
                c['in'] = 'tests/s/{0}.{1}.in'.format(game, c['name'])
                c['out'] = 'tests/s/{0}.{1}.out'.format(game, c['name'])
                clients.append(c)

        if shuffle:
            # Randomise order of clients
            random.shuffle(clients)

        # Start the clients
        for c in clients:
            c['proc'] = self.process(
                [CLIENT, c['name'], c['game'], c['port']], c['in'])

        # Check output and exit status
        for c in clients:
            self.assert_stdout_matches_file(c['proc'], c['out'])
            self.assert_stderr(c['proc'], '')
            self.assert_exit_status(c['proc'], 0)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_start_2(self):
        """Test 2 games (2 player) can start concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[0], PORTS[0]), 2)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_start_3(self):
        """Test two games (2 player) can start concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[0], PORTS[0], PORTS[0]), 4)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_start_4(self):
        """Test two games (2 player) can start concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[0], PORTS[0], PORTS[0], PORTS[0]), 3)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_2g(self):
        """Test two games (2 player) can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '2g'), (PORTS[0], '2g')])

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_exa(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '4ga'), (PORTS[0], '3ga')])

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_2ex(self):
        """Test 10 games (2 player) can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '2g') for i in range(10)]
        self.play_games(ports)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_4g7(self):
        """Test 3 games (4 player) can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex7.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4g7') for i in range(4)]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_3g4(self):
        """Test 5 games (3 player) can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex4.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '3g4') for i in range(5)]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_4gb(self):
        """Test 3 games (4 player) can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exb.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4gb') for i in range(3)]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_single', category_marks=8)
    def test_multiple_vary(self):
        """Test 4 games can run concurrently on a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4ga'), (PORTS[0], '3ga'),
                 (PORTS[0], '3ga'), (PORTS[0], '4ga')]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_start_2(self):
        """Test 2 games (2 player) can start concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[0], PORTS[2]), 2)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_start_3(self):
        """Test 3 games (2 player) can start concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[0], PORTS[2]), 2)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_start_4(self):
        """Test 4 games (3 player) can start concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck',
                     PORTS[2], 'tests/ex.deck', PORTS[3], 'tests/ex.deck'])
        self.delay(DELAY)
        self.start_games((PORTS[3], PORTS[2], PORTS[2], PORTS[0]), 3)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_2g(self):
        """Test two games (2 player) can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '2g'), (PORTS[2], '2g')]
        self.play_games(ports)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_1(self):
        """Test 2 games can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4ga'), (PORTS[2], '2g')]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_2(self):
        """Test 4 games can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exb.deck',
                     PORTS[2], 'tests/exb.deck', PORTS[3], 'tests/exb.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4gb'), (PORTS[0], '4gb'),
                 (PORTS[2], '4gb'), (PORTS[3], '4gb')]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_3(self):
        """Test 3 games can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4ga'), (PORTS[0], '3ga'),
                 (PORTS[2], '2g')]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_4(self):
        """Test 6 games can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck',
                     PORTS[2], 'tests/ex.deck', PORTS[3], 'tests/ex7.deck',
                     PORTS[4], 'tests/ex4.deck', PORTS[5], 'tests/exb.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4ga'), (PORTS[0], '3ga'),
                 (PORTS[3], '4g7'), (PORTS[2], '2g'),
                 (PORTS[5], '4gb'), (PORTS[4], '3g4')]
        self.play_games(ports, shuffle=True)

    @marks.marks('concurrent_multiple', category_marks=8)
    def test_ports_vary(self):
        """Test 12 games can run concurrently on separate ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck',
                     PORTS[2], 'tests/ex.deck', PORTS[3], 'tests/ex7.deck',
                     PORTS[4], 'tests/ex4.deck', PORTS[5], 'tests/exb.deck'])
        self.delay(DELAY)
        ports = [(PORTS[0], '4ga'), (PORTS[0], '3ga'),
                 (PORTS[3], '4g7'), (PORTS[2], '2g'),
                 (PORTS[5], '4gb'), (PORTS[2], '2g'),
                 (PORTS[0], '3ga'), (PORTS[4], '3g4'),
                 (PORTS[5], '4gb'), (PORTS[0], '4ga'),
                 (PORTS[4], '3g4'), (PORTS[3], '4g7')]
        self.play_games(ports, shuffle=True)

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_error_1(self):
        """Test game port start failure from admin"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/thing.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'Unable to access deckfile\n')

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_error_2(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/long.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'Error reading deck\n')

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_error_3(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex4.deck\n'.format(PORTS[1]))
        self.assert_stdout(nc, 'Invalid port number\n')

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_error_4(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('this is not valid\n')
        nc.send('Scores\n')
        nc.send('P2310thing tests/ex4.deck\n')
        self.assert_stdout(nc, 'Invalid port number\n')

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_game_1(self):
        """Test two games (2 player) can run concurrently on separate ports.
        Second port is started via the admin server.
        """
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'OK\n')

        self.play_games([(PORTS[2], '2g'), (PORTS[2], '2g')])

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_game_2(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'OK\n')

        self.play_games([(PORTS[0], '2g'), (PORTS[2], '2g')])

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_game_3(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex7.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'OK\n')

        ports = [(PORTS[0], '2g'), (PORTS[2], '4g7')]
        self.play_games(ports)

    @marks.marks('admin_p', category_marks=4)
    def test_admin_P_game_4(self):
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex7.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'OK\n')
        nc.send('P{0} tests/exa.deck\n'.format(PORTS[3]))
        self.assert_stdout(nc, 'OK\n')
        nc.send('P{0} tests/ex4.deck\n'.format(PORTS[4]))
        self.assert_stdout(nc, 'OK\n')
        nc.send('P{0} tests/exb.deck\n'.format(PORTS[5]))
        self.assert_stdout(nc, 'OK\n')

        ports = [(PORTS[0], '2g'), (PORTS[2], '4g7'), (PORTS[3], '4ga'),
                 (PORTS[3], '3ga'), (PORTS[5], '4gb')]
        self.play_games(ports)

    @marks.marks('admin_s', category_marks=4)
    def test_admin_S_1(self):
        """Test scores are correctly stored for a single port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '2g'), (PORTS[0], '2g')])
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('S\n')
        self.assert_stdout(nc, 'p1,2,4,0\n')
        self.assert_stdout(nc, 'p2,2,8,2\n')
        self.assert_stdout(nc, 'OK\n')

    @marks.marks('admin_s', category_marks=4)
    def test_admin_S_2(self):
        """Test scores are correctly stored for two ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex.deck',
                     PORTS[2], 'tests/ex.deck'])
        self.delay(DELAY)
        self.play_games([(PORTS[0], '2g'), (PORTS[2], '2g')])
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('S\n')
        self.assert_stdout(nc, 'p1,2,4,0\n')
        self.assert_stdout(nc, 'p2,2,8,2\n')
        self.assert_stdout(nc, 'OK\n')

    @marks.marks('admin_s', category_marks=4)
    def test_admin_S_3(self):
        """Test scores are correctly stored for many ports"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/exa.deck',
                     PORTS[2], 'tests/ex.deck', PORTS[3], 'tests/ex7.deck',
                     PORTS[4], 'tests/ex4.deck', PORTS[5], 'tests/exb.deck'])
        self.delay(DELAY)
        ports = [(PORTS[2], '2g'), (PORTS[2], '2g'), (PORTS[0], '4ga'),
                 (PORTS[3], '4g7'), (PORTS[5], '4gb'), (PORTS[0], '3ga'),
                 (PORTS[4], '3g4')]
        self.play_games(ports)

        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('S\n')
        self.assert_stdout(nc, 'p1,7,14,2\n')
        self.assert_stdout(nc, 'p2,7,19,3\n')
        self.assert_stdout(nc, 'p3,5,8,1\n')
        self.assert_stdout(nc, 'p4,3,5,1\n')
        self.assert_stdout(nc, 'OK\n')

    @marks.marks('admin_s', category_marks=4)
    def test_admin_S_4(self):
        """Check scores of game with a draw"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex5.deck'])
        self.delay(DELAY)
        self.play_single_game_sort(PORTS[0], '4g5', four=True)

        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('S\n')
        self.assert_stdout(nc, 'Alex,1,0,0\n')
        self.assert_stdout(nc, 'Connor,1,0,0\n')
        self.assert_stdout(nc, 'bob,1,4,1\n')
        self.assert_stdout(nc, 'gameover,1,4,1\n')
        self.assert_stdout(nc, 'OK\n')

    @marks.marks('admin_s', category_marks=4)
    def test_admin_S_5(self):
        """Check scores on game port started by admin port"""
        self.process([SERV, PORTS[1], PORTS[0], 'tests/ex5.deck'])
        self.delay(DELAY)
        nc = self.process(['nc', '-4', 'localhost', PORTS[1]])
        nc.send('P{0} tests/ex7.deck\n'.format(PORTS[2]))
        self.assert_stdout(nc, 'OK\n')

        self.play_games([(PORTS[2], '4g7')])
        self.play_single_game_sort(PORTS[0], '4g5', four=True)

        nc.send('S\n')
        self.assert_stdout(nc, 'Alex,1,0,0\n')
        self.assert_stdout(nc, 'Connor,1,0,0\n')
        self.assert_stdout(nc, 'bob,1,4,1\n')
        self.assert_stdout(nc, 'gameover,1,4,1\n')
        self.assert_stdout(nc, 'p1,1,1,0\n')
        self.assert_stdout(nc, 'p2,1,4,1\n')
        self.assert_stdout(nc, 'p3,1,2,0\n')
        self.assert_stdout(nc, 'p4,1,1,0\n')
        self.assert_stdout(nc, 'OK\n')


if __name__ == '__main__':
    import multiprocessing
    port_queue = multiprocessing.Queue()
    available_ports = [str(i) for i in range(3000, 4000, 20)]
    for port in available_ports:
        port_queue.put(port)

    def assign_port(options):
        options['port'] = port_queue.get()
        print(options['submission'], options['port'])

    def release_port(options):
        port_queue.put(options['port'])

    options = {'marking_setup': assign_port, 'marking_tear_down': release_port}
    marks.main(options=options)
