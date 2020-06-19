#!/usr/bin/env python

import pygame, struct, time

RES = 300, 200
BACKGROUND = 100, 100, 100

def ini(s, res):
    global audio, notes, t, inc

    audio = {}
    for n in range(1, 89):
            audio[n] = pygame.mixer.Sound("midisnd/midi%02u.wav" % n)
    notes = []
    for l in open("sttmp.csv"):
        x = l.strip().split(", ")
        if x[2] == "Note_on_c" and x[5] != "0":
            notes.append([int(x[4])-20, int(x[1])])
    t = 0
    inc = 20
    #print(notes)

def play(s, res):
    global t
    for x, y in notes:
        if t <= y < t + inc:
            audio[x].play()
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

