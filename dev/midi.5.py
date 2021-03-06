#!/usr/bin/env python

# Read MIDI file track and synthesize with PySynth A

# Usage:

# python readmidi.py file.mid [tracknum] [file.wav]  [--syn_b/--syn_c/--syn_d/--syn_e/--syn_p/--syn_s/--syn_samp]

# Based on code from https://github.com/osakared/midifile.py
# which appears to be based on
# https://github.com/gasman/jasmid/blob/master/midifile.js

# Original license:

"""
Copyright (c) 2014, Thomas J. Webb
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pygame, struct, time, sys

class Note(object):
    "Represents a single MIDI note"
    
    note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    
    def __init__(self, channel, pitch, velocity, start, duration = 0):
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity
        self.start = start
        self.duration = duration
    
    def __str__(self):
        s = Note.note_names[(self.pitch - 9) % 12]
        s += str(self.pitch // 12 - 1)
        s += " " + str(self.velocity)
        s += " " + str(self.start) + " " + str(self.start + self.duration) + " "
        return s
    
    def get_end(self):
        return self.start + self.duration

class MidiFile(object):
    "Represents the notes in a MIDI file"
    
    def read_byte(self, file):
        return struct.unpack('B', file.read(1))[0]
    
    def read_variable_length(self, file, counter):
        counter -= 1
        num = self.read_byte(file)
        
        if num & 0x80:
            num = num & 0x7F
            while True:
                counter -= 1
                c = self.read_byte(file)
                num = (num << 7) + (c & 0x7F)
                if not (c & 0x80):
                    break
        
        return (num, counter)
    
    def __init__(self, file_name):
        self.tempo = 120
        try:
            file = open(file_name, 'rb')
            if file.read(4) != b'MThd': raise Exception('Not a MIDI file')
            self.file_name = file_name
            size = struct.unpack('>i', file.read(4))[0]
            if size != 6: raise Exception('Unusual MIDI file with non-6 sized header')
            self.format = struct.unpack('>h', file.read(2))[0]
            self.track_count = struct.unpack('>h', file.read(2))[0]
            self.time_division = struct.unpack('>h', file.read(2))[0]

            # Now to fill out the arrays with the notes
            self.tracks = []
            for i in range(0, self.track_count):
                self.tracks.append([])

            for nn, track in enumerate(self.tracks):
                abs_time = 0.

                if file.read(4) != b'MTrk': raise Exception('Not a valid track')
                size = struct.unpack('>i', file.read(4))[0]

                # To keep track of running status
                last_flag = None
                while size > 0:
                    delta, size = self.read_variable_length(file, size)
                    delta /= float(self.time_division)
                    abs_time += delta

                    size -= 1
                    flag = self.read_byte(file)
                    # Sysex messages
                    if flag == 0xF0 or flag == 0xF7:
                        # print "Sysex"
                        while True:
                            size -= 1
                            if self.read_byte(file) == 0xF7: break
                    # Meta messages
                    elif flag == 0xFF:
                        size -= 1
                        type = self.read_byte(file)
                        if type == 0x2F:    # end of track event
                            self.read_byte(file)
                            size -= 1
                            break
                        print("Meta: " + str(type))
                        length, size = self.read_variable_length(file, size)
                        message = file.read(length)
                        # if type not in [0x0, 0x7, 0x20, 0x2F, 0x51, 0x54, 0x58, 0x59, 0x7F]:
                        print(length, message)
                        if type == 0x51:    # qpm/bpm
                            # http://www.recordingblogs.com/sa/Wiki?topic=MIDI+Set+Tempo+meta+message
                            self.tempo = 6e7 / struct.unpack('>i', b'\x00' + message)[0]
                            print("tempo =", self.tempo, "bpm")
                    # MIDI messages
                    else:
                        if flag & 0x80:
                            type_and_channel = flag
                            size -= 1
                            param1 = self.read_byte(file)
                            last_flag = flag
                        else:
                            type_and_channel = last_flag
                            param1 = flag
                        type = ((type_and_channel & 0xF0) >> 4)
                        channel = type_and_channel & 0xF
                        if type == 0xC:    # detect MIDI program change
                            print("program change, channel", channel, "=", param1)
                            continue
                        size -= 1
                        param2 = self.read_byte(file)
                        
                        # detect MIDI ons and MIDI offs
                        if type == 0x9:
                            track.append(Note(channel, param1, param2, abs_time))
                        elif type == 0x8:
                            for note in reversed(track):
                                if note.channel == channel and note.pitch == param1:
                                    note.duration = abs_time - note.start
                                    break

        except Exception as e:
            print("Cannot parse MIDI file: " + str(e))
        finally:
            file.close()
    
    def __str__(self):
        s = ""
        for i, track in enumerate(self.tracks):
            s += "Track " + str(i+1) + "\n"
            for note in track:
                s += str(note) + "\n"
        return s


RES = 500, 500
BACKGROUND = 100, 100, 100

def ini(s, res):
    global audio, notes, t, inc, first

    audio = {}
    for n in range(1, 89):
            audio[n] = pygame.mixer.Sound("midisnd/midi%02u.wav" % n)
    notes = []
    first = 1e9
    m = MidiFile(sys.argv[1])
    for tn in range(len(m.tracks)):
        for n in m.tracks[tn]:
            if n.velocity > 0:
                tt = int(1000 * n.start)
                first = min(first, tt)
                notes.append([n.pitch - 20, tt])
    t = 0
    inc = 40
    #print(notes)

def play(s, res):
    global t
    s.scroll(dx = -2)
    pygame.draw.rect(s, BACKGROUND, [498, 0, 2, 500])
    for x, y in notes:
        if t <= y-first < t + inc:
            audio[x].stop()
            audio[x].play()
            pygame.draw.rect(s, (255,255,255), [498, 500-4*x, 2, 2])
            #print(y, x)
    t += inc
        
        
class Berlin:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.res = RES
        self.screen = pygame.display.set_mode(self.res, pygame.RESIZABLE)
        pygame.display.set_caption('midi')
        self.screen.fill(BACKGROUND)
        self.clock = pygame.time.Clock()
        ini(self.screen, self.res)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.VIDEORESIZE:
                self.res = event.w, event.h
                self.last = 0
                self.screen = pygame.display.set_mode(self.res, pygame.RESIZABLE)

    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.events()
            self.update()
        pygame.quit()

    def update(self):
        #self.screen.fill(BACKGROUND)
        play(self.screen, self.res)
        pygame.display.flip()

c = Berlin()
c.run()

        
