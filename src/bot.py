"""

    Bot class talks to via and receives messages to/from the Twitch.TV IRC server.

"""

import config
import socket
import peaceparser
import random
import time
import re
import instrument

# Dicts: instrument_shortcuts { 'CMD': i }, self.instruments { i: OBJECT }
instrument_shortcuts = instrument.get_shortcuts()
regex_strings = {
    'prefixcommand': r'(^[A-Z]{0,3})',
    'removalcommand': r'(^[A-Z]{0,3}\s)',
    'inlinecommand': [r'(\s[A-Z]{1,3}\[)', r'([A-Z]{1,3}\[)', r'([A-Z]{1,3}\s\[)', r'(\s[A-Z]{1,3}\s\[)'],
    'digits': r'([0-9])+'
}

convert_strings = { 'RHY': 'rhythm', 'R': 'rhythm',
    'A': 'amplitude', 'AMP': 'amplitude',
    'P': 'pitch', 'PIT': 'pitch', 'OCT': 'pitch',
    'LR': 'pan', 'PAN': 'pan',
    'C': 'chop', 'CHP': 'chop', 'CHO': 'chop' }

def print_to_chat(message):
    """ Uses the default IRC chat string format to send a message to the users from the 'bot'"""
    socket.send(':{username}!{username}@{username}.{host} PRIVMSG {channel} :{msg}\r\n'
                .format(username=config.NICKNAME, host=config.HOST, channel=config.CHANNEL, msg=message)
                .encode('utf-8'))

class Bot:
    def __init__(self):
        """ Bot class, uses websocket to connect to the twitch IRC server. Runs in a continuous loop until
            crash or stopped. """
        self.war = True
        self.voters = {}
        self.votes_needed = 1
        self.setupInstruments()
        global socket
        socket = self.setupSocket()
        assert socket is not None
        self.listen()


    def setupInstruments(self):
        """
            Initalises a dictionary containing all instrument objects (from imported instrument class file, which can
            be accessed using a parsed instrument code (first three letters in full caps).
        """
        instrument_object_list = instrument.instrument_choices
        inst_dict = {}
        for n, inst in zip(range(0, len(instrument_object_list)), instrument_object_list):
            print(list(instrument_object_list.keys())[n])
            inst_dict[n] = instrument.Instrument(list(instrument_object_list.keys())[n])
        self.instruments = inst_dict

    def setupSocket(self):
        """ Sockets is initalised, connection messages are sent and connection is opened. """
        # Initialise a websocket (initially empty).
        _socket = socket.socket()
        # Connect to the IRC using the host address and PORT in the config.py file.
        _socket.connect((config.HOST, config.PORT))
        # Connect to the chatroom using a nickname, password, and channel join command.
        configVars = [config.OAUTH, config.NICKNAME, config.CHANNEL]
        configCommands = ['PASS', 'NICK', 'JOIN']
        for c, v in zip(configVars, configCommands):
            print("{v} {c}\r\n".format(c=c, v=v).encode("utf-8"))
            _socket.send("{v} {c}\r\n".format(c=c, v=v).encode("utf-8"))
        return _socket

    def switch_mode(self):
        """ Switches between war and peace mode, counts votes in favour of one mode over the other, requires a user defined
            value to be reached or surpassed in order to switch modes. Votes are only counted from unique usernames. """
        war_votes = 0
        peace_votes = 0

        for votes in list(self.voters.values()):
            if votes.upper() == 'WAR':
                war_votes += 1
            elif votes.upper() == 'PEACE':
                peace_votes += 1
            else:
                pass

        if war_votes > peace_votes:
            self.war = True
            print_to_chat('WAR MODE! WAAAGGHHH!')

        elif peace_votes > war_votes:
            self.war = False
            print_to_chat('PEACE MODE!')

            try:
                self.peace_parser
                return self.peace_parser
            except AttributeError:
                return peaceparser.PeaceParser(0.5) # Initaise additional parser.
        else:
            return
        return # THIS IS DEMOCRACY MANIFEST.


    def listen(self):
        """
            Code run adfinem, catches and decodes incoming data from socket - which an usually be broken down into two
            types: PINGS and public messages, other IRC inputs are ignored. Connections are closed if pings are not
            responded to, so a pong out occurs whenever recieved. All messages are encoded and decoded using utf-8.
            If a messages is entered, it's either parsed passively and stored in the peace_parser module or it's
            parsed and executed passively using a FIFO system.
        """
        print_to_chat('Hello! Twitchgens is now operational!')
        if self.war:
            print_to_chat('WAR MODE! WAAAGGHHH!')
        print('Starting socket listening...')

        while True:  # Bot runs in a continuous, infinite loop - top level (a bit like an arduino main loop.
            response = socket.recv(2048).decode("utf-8")  # Grab and decode the response packet of 1024 bytes.
            if response == "PING :tmi.twitch.tv\r\n":  # Twitch has a bit of code to manage connections, so it will ping.
               # Check for pings as a priority and respond with a pong to keep the connection open.
                socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))

            elif 'PRIVMSG' in response:  # If a user has sent a message to the chat...

                if 'WAR' in response or 'PEACE' in response:
                    # User is voting for a mode change, check user.
                    username = response.split(':')[1].split('!')[0]
                    if 'WAR' in response and 'PEACE' not in response:
                        self.voters[username] = 'WAR'
                    elif 'PEACE' in response and 'WAR' not in response:
                        self.voters[username] = 'PEACE'
                    print(len(self.voters), self.votes_needed)
                    if len(self.voters) >= self.votes_needed:
                        # If votes are exceeded (total), they are counted and the mode is switched.
                        self.peace_parser = self.switch_mode()
                else:
                    # Normal message parse.
                    if not self.war: # If peace mode.
                        print('Message from peaceful user...')
                        self.parse_message(response.split('PRIVMSG {} :'.format(config.CHANNEL))[1], False)
                        if self.peace_parser.response is not None:
                            # If there is a popular command vote confirmed in the parser, run it and refresh.
                            self.parse_message(self.peace_parser.response, True)
                            self.peace_parser.response = None
                    else:
                        self.parse_message(response.split('PRIVMSG {} :'.format(config.CHANNEL))[1], self.war)


            time.sleep(1 / config.MSG_RATE)  # The connection is ever-so fragile so there needs to be a tiny pause every loop.

    def parse_message(self, message, war_mode):
        """
            Messages are parsed in three seperate sections, the prefix (ADD, REM, CHG, ...), the instrument (BAS, SQU, ...)
            and the inline (instrument parameters).
        """
        def parse_prefix(command, message):
            """ Grab prefix command and resolve the message intention without parsing further into the message.
                Return bool equal to whether the parsing is complete.
                Parsing is done through regex matching and subtracting using a variety of check strings, which are
                used to check for the different section formats (e.g. inlines can be X[ or X [ with leading whitespaces.

                Peaceful parses are passive, meaning the commands don't end up being executed, rather they are sent to a
                second parser which stores and periodically checks them.
            """

            if not war_mode: # If war_mode is false.
                if command in ['RND', 'BPM', 'SCL', 'ADD', 'REM', 'CHG', 'STP', 'PLY', 'POL', 'REV', 'GLC']:
                    self.peace_parser.give_command(command)
                    return True
                else: return False

            print('Adding war command')

            if command == 'RND':
                # Pick random instrument, add an empty dictionary - this will randomise all the variables.
                instrument_choice = random.choice(list(self.instruments.values()))
                instrument_choice.add({'rhythm': None, 'amplitude': None, 'pitch': None, 'pan': None, 'chop': None})
                return False

            elif command == 'BPM':
                result = re.match(regex_strings['digits'], message).group(0) # Grab first digit results.
                instrument.change_bpm(int(result))
                return False

            elif command == 'SCL':
                instrument.change_scale(message.split(' ')[0])

            elif command in ['ADD', 'REM', 'CHG', 'STP', 'PLY', 'POL', 'REV', 'GLC']: # TODO: Expand as needed.
                return True

            return None

        def parse_instrument(command, message):
            try:
                instrument_name = None
                result = re.match(regex_strings['prefixcommand'], message).group(0)
                for titles in instrument_shortcuts:
                    print(titles, result)
                    if result.upper() == titles:
                        instrument_name = titles
                        target_instrument = self.instruments[instrument_shortcuts[titles]] # Find inst in list
                        message = re.sub(regex_strings['prefixcommand'], '', message) # Remove inst from string.
                        print(message)
                try:  # Iter through all instrument shortcut names, if non match, choose at random.
                    target_instrument
                except NameError:
                    raise AttributeError  # Shortcut to bottom except.
            except AttributeError:
                # No instrument, get a random one.
                target_instrument = self.instruments[random.randint(0, len(self.instruments) - 1)]
                instrument_name = random.choice(list(instrument_shortcuts.keys()))

            if not war_mode:
                if instrument_name is not None:
                    self.peace_parser.give_instrument(instrument_name)

            if command == 'REM':
                target_instrument.remove()
                return False

            elif command == "PLY":
                target_instrument.play()

            elif command == "STP":
                target_instrument.playing = False
                return False

            elif command == "POL":
                target_instrument.polyrhythm()
                return False

            elif command == 'REV':
                target_instrument.reverse()
                return False

            elif command == 'GLC':
                target_instrument.glitch()
                return False

            return target_instrument, message

        def parse_inline(message):
            val_dict = {'rhythm': None, 'amplitude': None, 'pitch': None, 'pan': None, 'chop': None}
            for re_str in regex_strings['inlinecommand']:
                try:
                    while True: # Loop until AttributeError encountered.
                        match = re.search(re_str, message) # Find match within the string for first of four inline searches.
                        match_string = match.group(0) # Get the match, can trigger AttributeError.
                        match_split = message.split(match_string)[1] # Get the values, the end bracket and the rest of the string.
                        inline_command = match_string.split('[')[0].replace(' ', '') # Chop off the bracket.
                        bracket_split = match_split.split(']')[0] # Chop off ultimate bracket.
                        comma_split = bracket_split.split(',') # Break up inner list (as str) into individual parts.

                        try:
                            val_dict[convert_strings[inline_command]] = [eval(v) for v in comma_split]
                        except SyntaxError:
                            val_dict[convert_strings[inline_command]] = None
                        except KeyError:
                            return False # Fixes an error where an incorrect command is used.
                        except TypeError:
                            return False # Fixes an error where an incorrect split is made (due to no brackets or commas?)

                        message = re.sub(re_str, '', message, count=1) # Remove the current inline focus and reset.

                except AttributeError:
                    pass # Return to the for loop.
            return val_dict # Return value dictionary.

        # 1. Find prefix command (ADD, REM, RAN).
        result = command = re.match(regex_strings['prefixcommand'], message).group(0) # Find prefix command.
        message = re.sub(regex_strings['removalcommand'], '', message, count=1)
        parsing = parse_prefix(result, message)
        if not parsing or parsing is None: # Resolve the command if its a prefix command.
            return

        # 2. Command is add, remove, or change - Find the inline values for this command (instrument, duration, etc...)
        # Find instrument under discussion, and get subtracted string with instrument tag removed.
        try:
            target_instrument, message = parse_instrument(command, message)
            print('Target instrument is {}'.format(target_instrument))
        except TypeError:
            print('Error in instrument parse.')
            return

        # 3. Find inline arguments to set parameters of instrument before playing, OR
        instrument_variables = parse_inline(message)

        if type(instrument_variables) is not bool:
            if not war_mode:
                self.peace_parser.give_parameters(instrument_variables)
                return
            elif command == 'ADD':
                print('Adding {}'.format(instrument_variables))
                target_instrument.add(instrument_variables)
            elif command == 'CHG':
                target_instrument.change(instrument_variables)
        return



Bot() # Run the bot! No __main___ in sight!