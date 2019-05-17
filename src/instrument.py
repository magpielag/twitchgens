from FoxDot import *
import random
from instrumentdefs import *
import threading

def setup_defs():
    # Returns dictionary containing instrument title (full) and the first two characters used as a player name.
    return {inst : inst[:2].lower() for inst in LISTDEFS }

instrument_choices = setup_defs() # A dict of all the instrument names and shorthand player names (used to trigger FoxDot).

def change_scale(scale):
    try:
        Scale.default = eval('Scale.{}'.format(scale))
    except AttributeError:
        pass

def change_bpm(v):
    if isinstance(v, int):
        Clock.bpm = v

def random_rhythm():
    # Make list of note divisions:
    divisions = []
    for r in range(0, random.randint(2, 6)):
        divisions.append(random.choice([0.75, 0.5, 0.25, 0.125, 1, 2]))
    stringList = '['
    for i, d in enumerate(divisions):
        if i != len(divisions) - 1:
            stringList = stringList + '{}, '.format(d)
        else:
            stringList = stringList + '{}]'.format(d)
    return stringList

def random_amplitude():
    return [random.randint(1, 10) / 10 for r in range(1, random.randint(2, 6))]

def random_pitch():
    return [random.randint(-4, 4) for r in range(1, random.randint(2, 6))]

def random_pan():
    return [random.randint(-1, 1)]

randomise = {
    'rhythm': random_rhythm,
    'amplitude': random_amplitude,
    'pitch': random_pitch,
    'pan': random_pan
}


class Instrument():
    def __init__(self, instrument_name):
        # 1. Choose an instrument definition, this is used to assign playback to synthDefs in SuperCollider/FoxDot.
        try:
            self.synth_def = instrument_name
        except KeyError: # If there is no instrument given, just choose a random one.
            self.synth_def = random.choice(list(instrument_choices.keys()))

        self.parameters = {}

        self.play_modes = {
            'single': '{idx} >> {inst}({pitch}, amp={amp}, dur={dur}, pan={pan}, chop={chop})',
            'multi': '{idx} >> {inst}([var({pitch}, 4)], amp=linvar({amp}, 4), dur=var({dur}, 4), pan=linvar({pan}, 4), chop=var({chop}, 4))',
            'stop': '{idx}.stop()'
        }

        self.poly = False
        self.poly_index = None
        self.playing = False  # User states what they want to happen to the instrument on initialisation.
        self.mode = 'single'
        self.interval = 2
        self.setup()

    def setup(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True

    def start(self):
        self.play()

    def play(self):
        self.playing = True
        try:
            self.thread.start()
        except RuntimeError:
            self.setup()
            self.thread.start()

    def stop(self):
        print('Stopping ', instrument_choices[self.synth_def])
        eval(self.play_modes['stop'].format(idx=instrument_choices[self.synth_def]))
        if self.poly:
            eval(self.play_modes['stop'].format(idx='zz'))
            self.poly = False

    def add(self, parameters_dict):
        """ Add a new set of parameters to an instrument - will either initalise these parameters, causing the
                instrument to play, or will append the new set of parameters to the instrument's current parameters.
        """

        self.mode = 'single'
        if len(self.parameters) == 0:
            for parameters in parameters_dict:
                if parameters_dict[parameters] is None:
                    try:
                        self.parameters[parameters] = randomise[parameters]()
                    except KeyError:
                        print('Cannot find randomisation for parameter {}, setting as default'.format(parameters))
                        self.parameters[parameters] = 0
                else:
                    self.parameters[parameters] = parameters_dict[parameters]
            self.play()

        else:
            # Take current parameters, append the new ones.
            for parameters in parameters_dict:
                    if parameters_dict[parameters] is not None:
                        print(self.parameters[parameters], parameters_dict[parameters])
                        if type(self.parameters[parameters]) is list and type(parameters_dict[parameters]) is list:
                            self.parameters[parameters] = self.parameters[parameters] + parameters_dict[parameters]
                        else:
                            if self.parameters[parameters] is None:
                                self.parameters[parameters] = parameters_dict[parameters]
                            else:
                                self.parameters[parameters] = eval(self.parameters[parameters]) + eval(parameters_dict[parameters])
                    else:
                        try: self.parameters[parameters] = randomise[parameters]
                        except KeyError: self.parameters[parameters] = 0
        print(self.parameters)

    def change(self, parameter_dict):
        # Check input, then change current params.
        for parameter in self.parameters:
            if parameter_dict[parameter] is None:
                pass
            else:
                if parameter in list(parameter_dict):
                    # Check input params are same type as current params (list or str poly'd list).
                    print('TYPES:', type(parameter_dict[parameter]), type(self.parameters[parameter]))
                    if type(parameter_dict[parameter]) is type(self.parameters[parameter]):
                        self.parameters[parameter] = parameter_dict[parameter]
                    else: # Check if values are equal but not types.
                        if eval(self.parameters[parameter]) == eval(parameter_dict[parameter]):
                            self.parameters[parameter] = str(eval(parameter_dict[parameter]))


    def polyrhythm(self):
        """ Create new mode for poly that is handled differently in the play function, will need to initalise a new player
            with the same variables but with a halved or doubled rhythm? """
        # Get current rhythm list.
        if self.playing is False:
            return
        if type(self.parameters['rhythm']) is str:
            pol = []
            for r in self.parameters['rhythm'][1:-1].split(','):
                if 'rest' in r:
                    pol.append(0)
                else:
                    try:
                        pol.append(float(r.replace(' ', ''))/2)
                    except ValueError:
                        try: pol.append(int(r.replace(' ', '')/2))
                        except ValueError: print('NOPE')

            self.polyrhythm_values = '{}'.format([str_r if str_r != 0 else rest(1) for str_r in pol])

        else:
            self.polyrhythm_values = [int(r)/2 for r in self.parameters['rhythm']]

        self.poly = True

    def reverse(self):
        for parameter in self.parameters:
            if type(self.parameters[parameter]) is list:
                self.parameters[parameter] = self.parameters[parameter][::1] # Reverse the values in the lists.

    def glitch(self):
        self.parameters['chop'] = str((random.randint(10, 60)/10))

    def calc_time(self):
        # Return total time in seconds of the instruments bar duration.
        times = self.parameters['rhythm']
        if type(times) is str:
            bracket_split = times.split('[')
            if bracket_split[1] == '':
                # Interweaved/multidimensional list/array. MUST BE HANDLED DIFFERENTLY TO A SINGLETON LIST.
                comma_split = ''.join([c for c in bracket_split.split(',')]) # Remove all commas from the string-converted list.
                for count, re_string in zip(range(2, 0), [r'(\[)', r'(])']):
                    comma_split = re.sub(re_string, '', comma_split, count=count)
                final_split = comma_split.split('[') # Remove inter-value bracket (e.g. 1, 2, 3 [ 4, 5, 6)
                shell_list = []
                for string_list in final_split:
                    temp_list = []
                    for string_char in string_list:
                        if string_char != ' ':
                            temp_list.append(eval(string_char)) # Turn into a number or evaluate as a fraction.
                    shell_list.append(temp_list)
                list_sum = [sum(list_n) for list_n in shell_list] # List containing sums of the internal lists (e.g. [5, 6, 2]).
                return int(sum(list_sum)/len(list_sum)) # Return average (mean).
            else: # Treat as single-dimension list.
                time_values = []
                bracket_split = bracket_split[1].split(']')[0]
                comma_split = bracket_split.split(',')
                for string_value in comma_split:
                    time_values.append(eval(string_value))
                return sum(time_values) # Return time sum value.
        else:
            for time in times:
                if type(time) is list:
                    time_total = 0
                    for sub_time in time:
                        time_total = time_total + sub_time
                    return time_total
                else:
                    return sum(times)


    def remove(self):
        self.stop()
        self.parameters = { 'instrument': self.synth_def, 'rhythm': None, 'pitch': None,
                            'amplitude': None, 'pan': None, 'chop': None } # Reset parameters to default.
        return

    def run(self):
        if type(self.parameters['rhythm']) is str:
            self.parameters['rhythm'] = eval(self.parameters['rhythm'])
        print(self.parameters['chop'])
        # Start the FoxDot player using the correct instrument and corresponding player index, load audio params.
        try: 
            eval(self.play_modes[self.mode].format(idx=instrument_choices[self.synth_def], inst=self.synth_def,
                                                dur='{}'.format([r for r in self.parameters["rhythm"]]),
                                                    pitch=self.parameters["pitch"],
                                                amp=self.parameters["amplitude"], pan=self.parameters["pan"],
                                               chop=self.parameters['chop']))
        except TypeError:
            # If there is a problem with the types during evaluation, the FoxDot connection will close, catch this.
            pass

        if self.poly:
            # If there is a polyrhythmic instrument setup, new instrument, halve all rhythm values.
            eval(self.play_modes['single'].format(idx='zz',
                                                   inst=self.synth_def,
                                                   dur=self.polyrhythm_values, pitch=self.parameters["pitch"],
                                                   amp=self.parameters["amplitude"], pan=self.parameters["pan"],
                                                   chop=self.parameters["chop"]))

        while self.playing:
            time.sleep(self.calc_time())
            # TODO: Clock value (wait time) from total durations of an instrument.
            break

        if self.playing:
            self.run()
        else:
            self.stop()


def get_shortcuts():
    # Used by the bot, contains three char tiles and the instrument indexes. 
    d = {}
    for i, titles in enumerate(list(instrument_choices.keys())):
        d[titles[:3].upper()] = i
    return d