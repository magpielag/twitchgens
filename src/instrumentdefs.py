from FoxDot import FileSynthDef, SynthDef

tom = FileSynthDef('tom')
tom.add()
snare = FileSynthDef("snare")
snare.add()
kick = FileSynthDef("kick")
kick.add()
plucky = FileSynthDef('plucky')
plucky.add()
hihat = FileSynthDef('hihat')
hihat.add()

LISTDEFS = ['tom', 'harp', 'snare', 'kick', 'plucky', 'hihat', 'squish', 'bass',
            'fuzz', 'klank', 'ripple', 'soprano', 'marimba']
