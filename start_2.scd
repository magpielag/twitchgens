SynthDef.new(\kick,
    {|amp=1, sus=1, pan=0, bus=0 freq=0|
        var osc, env;
		osc= {SinOsc.ar(freq/4)};
		env = {Line.ar(1, 0.4, sus/3, doneAction: 0)};
        osc=(osc * env);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

SynthDef.new(\harp,
    {|amp=0, sus=1, pan=0, bus=0 freq=0|
        var osc, env;
		osc=Saw.kr((freq/2), mul: amp);
		env = {Line.ar(0.2, 0.4, sus/3, doneAction: 0)};
        osc=(osc * env);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

SynthDef.new(\tom,
    {|amp=1, sus=1, pan=0, bus=0 freq=0|
        var osc, env;
		osc=SinOsc.ar((freq/3), mul: amp);
        env=EnvGen.ar(Env.perc(attackTime: 0.01, releaseTime: sus), doneAction: 0);
        osc=(osc * env);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

SynthDef.new(\plucky,
    {|amp=0, sus=0.2, pan=0, bus=0 freq=0|
        var osc, env;
		osc={BPF.ar(LFTri.ar(freq, mul: amp), freq-100, 10.0)};
        env=EnvGen.ar(Env.perc(attackTime: 0.3, releaseTime: sus), doneAction: 0);
        osc=(osc * env);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

SynthDef.new(\snare,
    {|amp=0, sus=0.3, pan=0, bus=0 freq=0|
        var osc, env, noise;
		noise = {LPF.ar(WhiteNoise.ar(1), freq*20)};
		osc = {HPF.ar(noise, freq)};
        env=EnvGen.ar(Env.perc(attackTime: 0.01, releaseTime: sus), doneAction: 0);
        osc=(osc * env);
		osc = (osc * amp);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

SynthDef.new(\hihat,
    {|amp=0, sus=0.1, pan=0, bus=0 freq=0|
        var osc, env, noise, noiseenv;
		noise = {LPF.ar(WhiteNoise.ar(amp), freq*2)};
		noiseenv = {Line.ar(1, 0, 0.1+(sus/4))};
		osc = {HPF.ar(LFTri.ar(freq, mul: amp), 2000)};
        env=EnvGen.ar(Env.perc(attackTime: 0.1, releaseTime: sus/4), doneAction: 0);
		noise = noise * noiseenv;
		osc = noise + osc;
		osc=(osc * env);
		osc = (osc * amp);
        osc = Pan2.ar(osc, pan);
		ReplaceOut.ar(bus, osc)}).add;

FoxDot.start()

s.quit