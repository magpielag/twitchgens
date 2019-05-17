import time
import random
import threading

class PeaceParser:
    def __init__(self, timer):
        from bot import print_to_chat as chat
        self.chat = chat
        """ Commands are parsed passively. Every n minutes (user defined, default at 2) the command with the most 
        'votes' (that is, commands entered) is processed. Same thing for instruments.
        This interval runs in a thread, meaning it's run as a background task. No globals are used, rather the final 
        command is stored in self.response which is checked in the main bot loop and run if it's a real variable and not
        None. It is then reset to None and the process begins again.
         """
        self.response = None
        self.start_dicts()
        self.timer = timer
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def start_dicts(self):
        self.commands, self.instruments, self.rhythm, self.amplitude, self.pitch, self.pan = [{} for i in range(0, 6)]


    def run(self):
        while True:
            time.sleep(self.timer*60)
            print('COUNTING VOTES, RETURNING')
            if self.response is None:
                self.return_vote()

    def change_timer(self, new_time):
        if type(new_time) is int:
            self.timer = new_time # Set value if correct format.
        else:
            try: self.change_timer(int(new_time)) # Recurr with new integer value.
            except TypeError: pass # Input is not viable.

    def return_vote(self):
        # Find most popular voted line.
        command, instrument = [self.count_votes(n) for n in [self.commands, self.instruments]]
        rhythm, pitch, amplitude, pan = [self.count_votes_params(n) for n in [self.rhythm, self.pitch,
                                                                              self.amplitude, self.pan]]
        list_params = [command, instrument, rhythm, pitch, amplitude, pan]
        if all([n is None for n in list_params]):
            # No votes to count.
            self.response = None
            return

        for check_param in list_params:
            if check_param is None:
                # Wont be parsed by the main loop again, set to FoxDot defaults.
                list_params[list_params.index(check_param)] = ''
            else:
                # Value is set.
                list_params[list_params.index(check_param)] = str(check_param)


        prefix_string = ''.join('{} '.format(param_char) for param_char in list_params[:2]) # CMD INST
        # CMD[VALS, VALS, VALS] if not none, else will join empty char.
        inline_string = ''.join(['{c}{p}'.format(c=com_char, p=param_val)
                                 if param_val != '' else ''
                                 for com_char, param_val in zip(['R', 'P', 'A', 'PAN'], list_params[2:])])
        # Sets inline as R[X] P[X] A[X] PAN[X] if the parameters are input.

        # Set response var which is checked by the bot.
        self.response = '{p} {i}'.format(p=prefix_string, i=inline_string)
        self.chat(self.response) # Alert users of the winning command.
        self.start_dicts() # Refresh the dicts.
        return

    def give_command(self, command):
        print('Adding command to parser: ', command)
        try:
            self.commands[command] += 1 # Increase vote count.
        except KeyError: self.commands[command] = 1

    def give_instrument(self, inst):
        print('Adding instrument to parser: ', inst)

        try: self.instruments[inst] += 1
        except KeyError: self.instruments[inst] = 1

    def give_parameters(self, parameters):
        print('Adding parameters to parser: ', parameters)

        mapping_dict = {'rhythm': self.rhythm, 'amplitude': self.amplitude, 'pitch': self.pitch, 'pan': self.pan}
        for param_key in parameters: # Look at each parameter.
            parameter_value = parameters[param_key]
            # If the value is a valid type and the key is valid, go.
            if parameter_value is not None and param_key in list(mapping_dict.keys()):
                if type(parameter_value) is str:
                    parameter_value = eval(parameter_value) # Convert to list.
                if type(parameter_value) is not list: # If still not list, the value isn't valid.
                    pass
                else:
                    # Parse through values and map them to vote counts.
                    for value in parameter_value:
                        if type(value) in [int, float]:
                            try:
                                print(mapping_dict[param_key], value)
                                # Attempt to set the dictionary within the mapping dictionary to
                                # equal a key of the parameter value and a value of the vote count!
                                mapping_dict[param_key][value] += 1
                            except KeyError:
                                mapping_dict[param_key][value] = 1

    def count_votes(self, count_dictionary):
        print('Counting votes!')
        print(count_dictionary)
        try:
            max_votes = max(list(count_dictionary.values()))
        except ValueError:
            return None
        winner = None
        for key in count_dictionary:
            if count_dictionary[key] == max_votes:
                if winner is None:
                    winner = key
                else:
                    if type(winner) is list:
                        winner.append(key)
                    else:
                        winner = [winner, key]
        if type(winner) is list:
            return random.choice(winner)
        else:
            return winner

    def count_votes_params(self, count_dictionary):
        try:
            max_votes = max(list(count_dictionary.values()))
        except ValueError:
            return None

        winners = []
        for key in count_dictionary:
            if count_dictionary[key] == max_votes:
                winners.append(key)

        if len(winners) > 0:
            return winners
        else:
            return None