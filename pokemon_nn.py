import os
import time
import numpy as np
import pandas as pd
import pyautogui as pag
import pytesseract as ptess
import cv2
from PIL import Image
import difflib

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from model import MyNetwork
from model import MyDataset

def prep_lists() -> tuple:
    return (pd.read_csv('data/pokemon.csv'), pd.read_csv('data/moves.csv'))

def train(num_epochs: int = 200, lr: float = 1e-4):
    #Train the model using data stored in file.

    turndataset = MyDataset('data/turns.csv')
    switchdataset = MyDataset('data/switches.csv')
    weight_decay = 1e-5

    turndataloader = DataLoader(turndataset, batch_size=32, shuffle=True)
    turnoptimizer = optim.Adam(turnmodel.parameters(), lr=lr, weight_decay=weight_decay)
    turncriterion = nn.MSELoss()
    switchdataloader = DataLoader(switchdataset, batch_size=32, shuffle=True)
    switchoptimizer = optim.Adam(switchmodel.parameters(), lr=lr, weight_decay=weight_decay)
    switchcriterion = nn.MSELoss()

    for epoch in range(num_epochs):
        for inputs, labels in turndataloader:
            turnoptimizer.zero_grad()
            outputs = turnmodel(inputs)
            turnloss = turncriterion(outputs, labels)
            turnloss.backward()
            turnoptimizer.step()
        for inputs, labels in switchdataloader:
            switchoptimizer.zero_grad()
            outputs = switchmodel(inputs)
            #print(outputs)
            outputs = outputs.clone()
            for i, o in enumerate(outputs):
                if torch.isnan(o): outputs[i] = 0.5
            switchloss = switchcriterion(outputs, labels)
            switchloss.backward()
            switchoptimizer.step()
        if ((epoch+1) % 10) == 0: print('Epoch ' + str(epoch+1) + ': Turn Loss: ' + str(format(turnloss.item(), '.3f')) + ', Switch Loss: ' + str(format(switchloss.item(), '.3f')))

def battle(started: bool = False) -> bool:
    #Conduct a single battle all the way through.

    print('Beginning battle...')
    if not started:
        begin_battle()
    battling = True
    turns = np.zeros((0, 94))
    switches = np.zeros((0, 93))
    mondata = np.zeros((6, 24))
    oppdata = np.zeros((6, 24))
    nturns = 0
    
    while battling:
        timer = 0
        while not timeToAttack():
            if timer > 30: 
                #Prevent opponent stalling forever
                startTimer()
                timer = -1000
            if timeToSwitch() and not timeToAttack():
                #Switch is required (switch move or faint)
                mondata, oppdata, data = switch(mondata, oppdata, nturns)
                switches = np.vstack((switches, data))
            elif matchEnd():
                #Match has ended
                battling = False
                break
            time.sleep(.5)
            timer += .5
        if not battling: break

        #Choosing an attack/switch
        mondata, oppdata, data = choose(mondata, oppdata, nturns)
        turns = np.vstack((turns, data))
        nturns += 1
    
    #Check for victory
    iwon = iWon()
    
    #Save match data for later training
    for i in range(len(turns)):
        turns[i][93] = format(result_score(nturns, iwon), '.7f')
    data_to_file(turns, 'data/turns.csv')
    for i in range(len(switches)):
        switches[i][92] = format(result_score(nturns, iwon), '.7f')
    data_to_file(switches, 'data/switches.csv')

    click_main_menu()
    return iwon

def choose(mondata: np.array, oppdata: np.array, nturns: int) -> tuple:
    #Choose attack or switch
    state = np.zeros(93)

    #Collect game data
    mondata = read_user_mons(mondata)
    for i in range(24):
        state[i] = mondata[0][i]
    for i in range(5):
        for j in range(4):
            state[(i*4)+j+24] = mondata[i+1][j]

    oppdata = read_opponent_mons(oppdata)
    for i in range(24):
        state[i+44] = oppdata[0][i]
    for i in range(5):
        for j in range(4):
            state[(i*4)+j+64] = oppdata[i+1][j]

    #Use model to get best move
    choices = []
    for i in range(4):
        choices.append([mondata[0][(5*i)+4], mondata[0][(5*i)+5], mondata[0][(5*i)+6], mondata[0][(5*i)+7], mondata[0][(5*i)+8]])
    for i in range(1, 6):
        choices.append([invert(mondata[i][0]), invert(mondata[i][1]), invert(mondata[i][2]), invert(mondata[i][3]), 0.0])
    outcomes = []
    for i, choice in enumerate(choices):
        if choice[0] == 0.0 or (choice[0] < 0 and choice[1] == 0):
            outcomes.append(-1.0)
            continue
        for j in range(5):
            state[88+j] = choice[j]
        outcomes.append(float(turnmodel(torch.Tensor(state))))

    choice = np.argmax(outcomes)
    print('Choice confidence: ' + str(format(((outcomes[choice])*100), '.2f')))
    if choice < 4:
        print('Turn ' + str(nturns+1) + ' Choice: Move ' + str(choice+1))
        click_move(choice+1)
    else:
        print('Turn ' + str(nturns+1) + ' Choice: Switch to Slot ' + str(choice-2))
        click_switch(choice-2)

    #Save turn data for later training
    for i in range(5):
        state[88+i] = choices[choice][i]
    if choice >= 4:
        for i in range(24):
            temp = mondata[0][i]
            mondata[0][i] = mondata[choice+1][i]
            mondata[choice+1][i] = temp
    
    return (mondata, oppdata, np.append(state, 0.0))

def switch(mondata: np.array, oppdata: np.array, nturns: int) -> tuple:
    #Choose a Pokemon to switch to
    state = np.zeros(92)

    #Collect game data
    mondata = read_user_mons(mondata)
    for i in range(24):
        state[i] = mondata[0][i]
    for i in range(5):
        for j in range(4):
            state[(i*4)+j+24] = mondata[i+1][j]

    oppdata = read_opponent_mons(oppdata)
    for i in range(24):
        state[i+44] = oppdata[0][i]
    for i in range(5):
        for j in range(4):
            state[(i*4)+j+64] = oppdata[i+1][j]

    choices = []
    for i in range(1, 6):
        choices.append([invert(mondata[i][0]), invert(mondata[i][1]), invert(mondata[i][2]), invert(mondata[i][3])])
    outcomes = []
    for i, choice in enumerate(choices):
        if choice[1] == 0:
            outcomes.append(-1.0)
            continue
        for j in range(4):
            state[88+j] = choice[j]
        outcomes.append(float(switchmodel(torch.Tensor(state))))

    choice = np.argmax(outcomes)
    print('Turn ' + str(nturns) + ' Switch: Slot ' + str(choice+2))
    click_switch(choice+2)
    
    for i in range(4):
        state[88+i] = choices[choice][i]
    for i in range(24):
        temp = mondata[0][i]
        mondata[0][i] = mondata[choice+1][i]
        mondata[choice+1][i] = temp

    return (mondata, oppdata, np.append(state, 0.0))

def read_user_mons(mondata: np.array) -> np.array:
    #Read the user's current game state as an array of values (used to feed into the model).

    try:
        pos1, pos2 = pag.locateCenterOnScreen('ref_images/switch.png', confidence=0.9)
    except:
        print("ERROR: User's pokemon data was not successfully obtained")
        return
    
    left = pos1-28
    top = pos2-160
    pos1 += 20
    pos2 += 40

    #Grabbing player pokemon data
    if mondata[0][0] == 0.0:
        for i in range(6):
            #Grabbing images
            pag.moveTo((pos1, pos2))
            try:
                hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', region = (left, top, 480, 420), confidence=0.95)
            except:
                hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', confidence=0.95)
            mon_img = pag.screenshot(region = (hp1-10, hp2-50, 300, 20)).convert('L')
            hp_img = pag.screenshot(region = (hp1+10, hp2-8, 150, 15)).convert('L')
            move_imgs = []
            for j in range(4):
                move_imgs.append(pag.screenshot(region = (hp1, hp2+50+(j*15), 150, 15)).convert('L'))

            #Image improvement and extraction
            mon = img_to_text(mon_img)
            hp = img_to_text(hp_img)
            pmoves = []
            for img in move_imgs:
                txt = img_to_text(img).strip()
                if len(txt) < 3 or txt == '':
                    break
                pmoves.append(txt)
            
            #Convert to float values
            monvals = mon_to_vals(mon)
            mondata[i][0], mondata[i][2], mondata[i][3] = monvals
            mondata[i][1] = text_to_health(hp)
            for j, move in enumerate(pmoves):
                try:
                    movevals = move_to_vals(move)
                    mondata[i][(j*5)+4], mondata[i][(j*5)+5], mondata[i][(j*5)+6], mondata[i][(j*5)+7], mondata[i][(j*5)+8] = movevals
                except:
                    mondata[i][(j*5)+4] = mondata[i][(j*5)+5] = mondata[i][(j*5)+6] = mondata[i][(j*5)+7] = mondata[i][(j*5)+8] = 0.0

            pos1 += 105
            left += 105
    else:
        mons = []
        for i in range(6): mons.append(mondata[i][0])

        for i in range(6):
            #Grabbing images
            pag.moveTo((pos1, pos2))
            try:
                hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', region = (left, top, 480, 420), confidence=0.95)
            except:
                hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', confidence=0.95)
            mon_img = pag.screenshot(region = (hp1-10, hp2-50, 300, 20)).convert('L')
            hp_img = pag.screenshot(region = (hp1+10, hp2-8, 150, 15)).convert('L')

            #Image improvement and extraction
            mon = img_to_text(mon_img)
            hp = img_to_text(hp_img)
            
            #Swap/assign values
            monvals = mon_to_vals(mon)
            try:
                idx = mons.index(monvals[0])
            except:
                print(mondata)
                print(mons)
                print(monvals[0])
                print('---Index exception---')
                exit()
            if idx != i:
                for j in range(24):
                    temp = mondata[i][j]
                    mondata[i][j] = mondata[idx][j]
                    mondata[idx][j] = temp
                temp = mons[i]
                mons[i] = mons[idx]
                mons[idx] = temp
            elif i == 0:
                mondata[i][1] = text_to_health(hp)
                break
            mondata[i][1] = text_to_health(hp)

            pos1 += 105
            left += 105
    return mondata

def read_opponent_mons(oppdata: np.array) -> np.array:
    #Read the opponent's current game state as an array of values (used to feed into the model).

    try:
        p1, p2 = pag.locateCenterOnScreen('ref_images/user.png', confidence=0.9)
    except:
        print("ERROR: Opponent's pokemon data was not successfully obtained")
        return
    
    pos1 = p1 - 160
    pos2 = p2 + 140
    #Grabbing opponent pokemon data
    for i in range(6):
        #Grabbing images
        pag.moveTo((pos1, pos2))
        try:
            hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', region = (520, 70, 480, 420), confidence=0.95)
        except:
            try:
                hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', confidence=0.95)
            except: 
                while i < 6:
                    oppdata[i][1] = 1.0
                    i += 1
                break
        mon_img = pag.screenshot(region = (hp1-10, hp2-50, 300, 20)).convert('L')
        hp_img = pag.screenshot(region = (hp1+10, hp2-8, 150, 15)).convert('L')
        move_imgs = []
        for j in range(4):
            move_imgs.append(pag.screenshot(region = (hp1, hp2+50+(j*15), 150, 15)).convert('L'))

        #Image improvement and extraction
        mon = img_to_text(mon_img)
        hp = img_to_text(hp_img)
        pmoves = []
        for img in move_imgs:
            txt = img_to_text(img).strip()
            if len(txt) < 3 or txt == '':
                break
            pmoves.append(txt)
        
        #Convert to float values
        monvals = mon_to_vals(mon)
        oppdata[i][0], oppdata[i][2], oppdata[i][3] = monvals
        oppdata[i][1] = text_to_health(hp)
        for j, move in enumerate(pmoves):
            try:
                movevals = move_to_vals(move)
                oppdata[i][(j*5)+4], oppdata[i][(j*5)+5], oppdata[i][(j*5)+6], oppdata[i][(j*5)+7], oppdata[i][(j*5)+8] = movevals
            except:
                oppdata[i][(j*5)+4] = oppdata[i][(j*5)+5] = oppdata[i][(j*5)+6] = oppdata[i][(j*5)+7] = oppdata[i][(j*5)+8] = 0.0

        if i == 2:
            pos1 -= 60
            pos2 += 30
        else:
            pos1 += 30
    
    #Verifying opponents lead pokemon
    pag.moveTo((p1-290, p2+110))
    try:
        hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', region = (380, 70, 480, 150), confidence=0.95)
    except:
        try:
            hp1, hp2 = pag.locateCenterOnScreen('ref_images/hp.png', confidence=0.95)
        except:
            return oppdata
    mon_img = pag.screenshot(region = (hp1-10, hp2-50, 300, 20)).convert('L')
    mon = img_to_text(mon_img)
    monvals = mon_to_vals(mon)
    if not oppdata[0][0] == monvals[0]:
        for i in range(1, 6):
            if oppdata[i][0] == monvals[0]:
                for j in range(24):
                    temp = oppdata[0][j]
                    oppdata[0][j] = oppdata[i][j]
                    oppdata[i][j] = temp
                break

    return oppdata

def img_to_text(img) -> str:
    ocv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    denoised_image = cv2.fastNlMeansDenoisingColored(ocv_img, None, 10, 10, 7, 21)
    enhanced_pil_image = Image.fromarray(cv2.cvtColor(cv2.convertScaleAbs(denoised_image, alpha=1.5, beta=0), cv2.COLOR_BGR2RGB))
    return ptess.image_to_string(enhanced_pil_image, config='--psm 6 --oem 3').strip()

def find_closest_partial_match(target, string_list):
    best_match = None
    best_match_ratio = 0
    
    for string in string_list:
        matcher = difflib.SequenceMatcher(None, target, string)
        match_ratio = matcher.ratio()
        
        if match_ratio > best_match_ratio:
            best_match = string
            best_match_ratio = match_ratio
    
    return best_match

def preprocess_mon(mon: str) -> str:
    if '@' in mon:
        mon = mon[:mon.find('@')].strip()
    if '(' in mon:
        mon = mon[mon.find('(')+1:].strip()
    if ')' in mon:
        mon = mon[:mon.find(')')].strip()

    return mon

def mon_to_vals(mon: str) -> tuple:
    mon = preprocess_mon(mon)
    mon = find_closest_partial_match(mon, pokemon['name'])
    if mon == None: 
        print('Mon is none')
        return (0.0, 0.0, 0.0)
    for _, poke in pokemon.iterrows():
        if mon == poke[0]:
            return (poke[1], poke[2], poke[3])
    for _, poke in pokemon.iterrows():
        if mon in poke[0] or poke[0] in mon:
            return (poke[1], poke[2], poke[3])

def move_to_vals(move: str) -> tuple:
    move = find_closest_partial_match(move, moves['name'])
    if move == None:
        print('Move is none')
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    for _, mo in moves.iterrows():
        if move == mo[0]:
            return (mo[1], mo[2], mo[3], mo[4], mo[5])

def text_to_health(hp: str) -> float:
        matcher = difflib.SequenceMatcher(None, hp, 'fainted')
        if matcher.ratio() > 0.5:
            return 0.0
        else:
            safety_count = 0
            while True:
                try:
                    return format(float(hp[:hp.find('%')])/100, '.7f')
                except:
                    if len(hp) <= 1 or safety_count > 100: return format(1.0, '.7f')
                    if not hp[0].isnumeric():
                        hp = hp[1:].strip()
                    elif hp[-1] != '%' and not hp[-1].isnumeric():
                        hp = hp[:-1].strip()
                safety_count += 1

def timeToAttack() -> bool:
    if pag.locateOnScreen('ref_images/attack.png', confidence=0.95) == None:
        return False
    else:
        return True
    
def timeToSwitch() -> bool:
    if pag.locateOnScreen('ref_images/switch.png', confidence=0.95) == None:
        return False
    else:
        return True
    
def matchEnd() -> bool:
    if pag.locateOnScreen('ref_images/end.png', confidence=0.95) == None:
        return False
    else:
        return True

def iWon() -> bool:
    if pag.locateOnScreen('ref_images/won.png', confidence=0.95) == None:
        return False
    else:
        return True
    
def begin_battle():
    #Click the begin battle button if it can be found.

    battle = pag.locateCenterOnScreen('ref_images/battle_icon.png', region=(20, 160, 310, 420), confidence=0.9)
    if battle == None:
        print('Battle button not present on screen')
        exit()

    pag.click(battle)
    pag.click((960, 540))

def click_move(move: int):
    #Click move as indicated by input.

    try:
        pos1, pos2 = pag.locateCenterOnScreen('ref_images/attack.png', confidence=0.9)
    except:
        try:
            pos1, pos2 = pag.locateCenterOnScreen('ref_images/attack.png', confidence=0.9)
        except:
            print('Move buttons not found, assuming battle ended.')
            return

    if(move == 1):
        pos = (pos1+50, pos2+30)
    elif(move == 2):
        pos = (pos1+210, pos2+30)
    elif(move == 3):
        pos = (pos1+370, pos2+30)
    else:
        pos = (pos1+530, pos2+30)

    pag.click(pos)
    pag.click((960, 540))
    if timeToAttack():
        if move > 3: move = 0
        move += 1
        click_move(move)

def click_switch(switch_to: int):
    #Click team member to switch to as indicated by input.

    try:
        pos1, pos2 = pag.locateCenterOnScreen('ref_images/switch.png', confidence=0.9)
    except:
        try:
            pos1, pos2 = pag.locateCenterOnScreen('ref_images/switch.png', confidence=0.9)
        except:
            print('Switch buttons not found, assuming battle has ended.')
            return

    if (switch_to == 2):
        pos = (pos1+130, pos2+30)
    elif (switch_to == 3):
        pos = (pos1+240, pos2+30)
    elif (switch_to == 4):
        pos = (pos1+350, pos2+30)
    elif (switch_to == 5):
        pos = (pos1+460, pos2+30)
    else:
        pos = (pos1+560, pos2+30)

    pag.click(pos)
    pag.click((960, 540))
    if timeToSwitch():
        if switch_to > 5: switch_to = 1
        switch_to += 1
        click_switch(switch_to)

def click_main_menu():
    #Click the main menu button if it can be found

    try:
        m1, m2 = pag.locateCenterOnScreen('ref_images/end.png', confidence=0.95)
    except:
        print('Main menu button not present on screen')
        exit()

    m1 -= 60
    pag.click((m1, m2))
    pag.click((960, 540))

def startTimer():
    #Click to start the timer if it can be found

    try:
        pag.click(pag.locateCenterOnScreen('ref_images/timer.png', confidence=0.95))
        pag.click(pag.locateCenterOnScreen('ref_images/starttimer.png', confidence=0.95))
    except:
        print('Timer failed to be started')

    pag.click((960, 540))

def invert(num):
    if num == 0.0: return num
    else: return num * -1.0

def result_score(nturns: int, iwon: bool) -> float:
    if nturns > 100: nturns = 100
    if iwon:
        return ((100-nturns)/200) + 0.5
    else:
        return nturns/200

def data_to_file(data: np.array, outfile: str):
    with open(outfile, 'a') as file:
        for row in data:
            out_line = ''
            for element in row:
                out_line = out_line + str(element) + ','
            file.write(out_line[:-1] + '\n')

def reportResults(results: list):
    if len(results) < 1: return
    wins = 0
    for i, result in enumerate(results):
        if result: 
            print('Won battle ' + str(i+1))
            wins += 1
        else:
            print('Lost battle ' + str(i+1))
    
    print('Won ' + str(wins) + ' battles out of ' + str(len(results)))

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')

    pokemon, moves = prep_lists()

    turnmodel = MyNetwork(93, 500, 1)
    switchmodel = MyNetwork(92, 500, 1)
    
    train(num_epochs=100, lr=1e-6)

    numbattles = 5
    results = []
    for i in range(numbattles):
        iwon = battle()
        results.append(iwon)
        if iwon:
            print('Battle #' + str(i+1) + ' ended in victory.')
        else:
            print('Battle #' + str(i+1) + ' ended in defeat.')
    
    reportResults(results)