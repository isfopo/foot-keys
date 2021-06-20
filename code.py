from board import *
import digitalio
import time

import usb_midi

import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn

class NoteButton:
    def __init__(self, pin, note, midi):
        self.button = digitalio.DigitalInOut(pin)
        self.button.switch_to_input(pull=digitalio.Pull.DOWN)
        self.note = note
        self.midi = midi
        self.is_on = False
        self.is_held = False
        self.is_sustained = False
        self.is_octave_up = False
        
    def on(self):
        self.midi.send(NoteOn(self.note))
        self.is_on = True
    
    def on_octave_up(self):
        self.midi.send(NoteOn(self.note + 12))
        self.is_on = True
        self.is_octave_up = True
        
    def off(self):
        if not self.is_held and not self.is_sustained:
            self.midi.send(NoteOff(self.note))    
        self.is_on = False
        
    def off_octave_up(self):
        if not self.is_held and not self.is_sustained:
            self.midi.send(NoteOff(self.note + 12))
            self.is_octave_up = False
        self.is_on = False
        
    def get_value(self):
        return self.button.value


midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

STARTING_NOTE = 12

PINS = [GP3, GP4, GP5, GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14, GP15]

note_buttons = []

for i, pin in enumerate(PINS):
    note_buttons.append(NoteButton(pin, STARTING_NOTE + i, midi))
    
hold = digitalio.DigitalInOut(GP18)
hold.switch_to_input(pull=digitalio.Pull.DOWN)

sustain_pedal = digitalio.DigitalInOut(GP20)
sustain_pedal.switch_to_input(pull=digitalio.Pull.DOWN)

octave_up = digitalio.DigitalInOut(GP16)
octave_up.switch_to_input(pull=digitalio.Pull.DOWN)

last_note = None
was_held = None
was_sustained = None
was_octave_up = None
sustained_notes = []

while True:
    is_held = hold.value
    is_sustained = sustain_pedal.value
    is_octave_up = octave_up.value
    
    for note_button in note_buttons:
        if note_button.get_value() and not note_button.is_on:
            if last_note and last_note.is_held:
                last_note.is_held = False
                print(last_note.is_octave_up)
                if not last_note.is_octave_up:
                    last_note.off()
                else:
                    last_note.off_octave_up()
            if not is_octave_up:
                note_button.on()
            else:
                note_button.on_octave_up()
            
        elif not note_button.get_value() and note_button.is_on:
            if is_held:
               note_button.is_held = True
            if is_sustained:
                note_button.is_sustained = True
                sustained_notes.append(note_button)
            if not is_octave_up:
                note_button.off()
            else:
                note_button.off_octave_up()
            last_note = note_button
    
    if was_held and not is_held:
        last_note.is_held = False
        last_note.off()
    
    if was_sustained and not is_sustained:
        for note_button in sustained_notes:
            note_button.is_sustained = False
            note_button.off()
    
    if was_octave_up and not is_octave_up:
        for note_button in note_buttons:
            if note_button.is_octave_up:
                note_button.off_octave_up()
                
    if is_octave_up and not was_octave_up:
        for note_button in note_buttons:
            if note_button.is_on:
                note_button.off()
    
    was_held = is_held
    was_sustained = is_sustained
    was_octave_up = is_octave_up