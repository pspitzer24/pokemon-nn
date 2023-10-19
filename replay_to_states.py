import os

import pandas as pd
import numpy as np
import requests as rq

def prep_data() -> tuple:
    return (pd.read_csv('data/pokemon.csv'), pd.read_csv('data/moves.csv'))

def pre_process(file_path: str) -> tuple:
    """
    Takes as input a file path, as a string, and returns an array of
    game states and results from every url in the file.

    Returns: matrix of data (n, 90)
    """

    urls = pd.read_csv(file_path)
    data = np.zeros((0, 94))
    switches = np.zeros((0, 93))
    i = 1
    for url in urls['urls']:
        print('Replay ' + str(i))
        newdata, newswitches = url_to_states(url)
        data = np.vstack((data, newdata))
        switches = np.vstack((switches, newswitches))
        i += 1
    
    return (data, switches, urls['urls'])

def url_to_states(url: str) -> tuple:
    """
    Takes as input a url, as a string, and returns an array of
    game states and results.

    Returns: matrix of data (2*nturns, 90)
    """

    game_log = rq.get(url+".log").text
    if len(game_log) < 50:
        print('ERROR: Replay "' + url + '" was unable to be retrieved.')
        exit()
    #print(game_log)
    #Get p1 name
    i1 = game_log.find('|p1|')+len('|p1|')
    i2 = game_log[i1:].find('|')+i1
    p1 = game_log[i1:i2]

    #Getting winner and total number of turns
    i1 = game_log.find('|win|')+len('|win|')
    i2 = game_log[i1:].find('\n')+i1
    p1_win = game_log[i1:i2] == p1
    i1 = game_log.rfind('|turn|')+len('|turn|')
    i2 = game_log[i1:].find('\n')+i1
    nturns = int(game_log[i1:i2])
    if not '|move|' in game_log[i2:] and not '|switch|' in game_log[i2:]: 
        nturns -= 1
        game_log = game_log[:game_log.rfind('|turn|')]
    else:
        game_log = game_log[:game_log.find('|win|')]
    game_log = game_log[game_log.find('|start\n'):]

    #Grabbing mons and moves
    p1_mons = []
    p1_moves = [[] for _ in range(6)]
    p2_mons = []
    p2_moves = [[] for _ in range(6)]
    lines = game_log.split('\n')
    for line in lines:
        if '|switch|' in line or '|replace|' in line or '|drag|' in line:
            player, new_mon = get_switch_from_line(line)
            if player == '1':
                if new_mon not in p1_mons: p1_mons.append(new_mon)
            else:
                if new_mon not in p2_mons: p2_mons.append(new_mon)
    for line in lines:
        if '|move|' in line:
            user, move = get_move_from_line(line)
            if line[line.find('|p')+2] == '1':
                for i, mon in enumerate(p1_mons):
                    if user in mon: idx = i
                if move not in p1_moves[idx]: p1_moves[idx].append(move)
            else:
                for i, mon in enumerate(p2_mons):
                    if user in mon: idx = i
                if move not in p2_moves[idx]: p2_moves[idx].append(move)

    #Mon names and moves to values
    p1_vals = np.zeros((6, 23))
    p2_vals = np.zeros((6, 23))
    for i, mon in enumerate(p1_mons):
        monvals = mon_to_vals(mon)
        p1_vals[i][0], p1_vals[i][1], p1_vals[i][2] = monvals
        j = 3
        for move in p1_moves[i]:
            movevals = move_to_vals(move)
            p1_vals[i][j], p1_vals[i][j+1], p1_vals[i][j+2], p1_vals[i][j+3], p1_vals[i][j+4] = movevals
            j += 5
    for i, mon in enumerate(p2_mons):
        monvals = mon_to_vals(mon)
        p2_vals[i][0], p2_vals[i][1], p2_vals[i][2] = monvals
        j = 3
        for move in p2_moves[i]:
            movevals = move_to_vals(move)
            p2_vals[i][j], p2_vals[i][j+1], p2_vals[i][j+2], p2_vals[i][j+3], p2_vals[i][j+4] = movevals
            j += 5

    #Inputting default data
    data = np.zeros((nturns*2, 94))
    switches = np.zeros((0, 93))
    p1_score = result_score(nturns, p1_win)
    p2_score = result_score(nturns, not p1_win)
    i = 1
    avals = p1_vals
    bvals = p2_vals
    score = p1_score
    for row in data:
        row[0] = avals[0][0]                         #P1 lead name, hp, type 1, type 2
        row[1] = 1.0
        row[2] = avals[0][1]
        row[3] = avals[0][2]
        row[4] = avals[0][3]                         #P1 lead Move 1 name, type, category, power, accuracy
        row[5] = avals[0][4]
        row[6] = avals[0][5]
        row[7] = avals[0][6]
        row[8] = avals[0][7]
        row[9] = avals[0][8]                         #P1 lead Move 2 name, type, category, power, accuracy
        row[10] = avals[0][9]
        row[11] = avals[0][10]
        row[12] = avals[0][11]
        row[13] = avals[0][12]
        row[14] = avals[0][13]                       #P1 lead Move 3 name, type, category, power, accuracy
        row[15] = avals[0][14]
        row[16] = avals[0][15]
        row[17] = avals[0][16]
        row[18] = avals[0][17]
        row[19] = avals[0][18]                       #P1 lead Move 4 name, type, category, power, accuracy
        row[20] = avals[0][19]
        row[21] = avals[0][20]
        row[22] = avals[0][21]
        row[23] = avals[0][22]
        row[24] = avals[1][0]                        #P1 party 2 name, hp, type 1, type 2
        row[25] = 1.0
        row[26] = avals[1][1]
        row[27] = avals[1][2]
        row[28] = avals[2][0]                        #P1 party 3 name, hp, type 1, type 2
        row[29] = 1.0
        row[30] = avals[2][1]
        row[31] = avals[2][2]
        row[32] = avals[3][0]                        #P1 party 4 name, hp, type 1, type 2
        row[33] = 1.0
        row[34] = avals[3][1]
        row[35] = avals[3][2]
        row[36] = avals[4][0]                        #P1 party 5 name, hp, type 1, type 2
        row[37] = 1.0
        row[38] = avals[4][1]
        row[39] = avals[4][2]
        row[40] = avals[5][0]                        #P1 party 6 name, hp, type 1, type 2
        row[41] = 1.0
        row[42] = avals[5][1]
        row[43] = avals[5][2]
        row[44] = bvals[0][0]                        #P2 lead name, hp, type 1, type 2
        row[45] = 1.0
        row[46] = bvals[0][1]
        row[47] = bvals[0][2]
        row[48] = bvals[0][3]                        #P2 lead Move 1 name, type, category, power, accuracy
        row[49] = bvals[0][4]
        row[50] = bvals[0][5]
        row[51] = bvals[0][6]
        row[52] = bvals[0][7]
        row[53] = bvals[0][8]                        #P2 lead Move 2 name, type, category, power, accuracy
        row[54] = bvals[0][9]
        row[55] = bvals[0][10]
        row[56] = bvals[0][11]
        row[57] = bvals[0][12]
        row[58] = bvals[0][13]                       #P2 lead Move 3 name, type, category, power, accuracy
        row[59] = bvals[0][14]
        row[60] = bvals[0][15]
        row[61] = bvals[0][16]
        row[62] = bvals[0][17]
        row[63] = bvals[0][18]                       #P2 lead Move 4 name, type, category, power, accuracy
        row[64] = bvals[0][19]
        row[65] = bvals[0][20]
        row[66] = bvals[0][21]
        row[67] = bvals[0][22]
        row[68] = bvals[1][0]                        #P2 party 2 name, hp, type 1, type 2
        row[69] = 1.0
        row[70] = bvals[1][1]
        row[71] = bvals[1][2]
        row[72] = bvals[2][0]                        #P2 party 3 name, hp, type 1, type 2
        row[73] = 1.0
        row[74] = bvals[2][1]
        row[75] = bvals[2][2]
        row[76] = bvals[3][0]                        #P2 party 4 name, hp, type 1, type 2
        row[77] = 1.0
        row[78] = bvals[3][1]
        row[79] = bvals[3][2]
        row[80] = bvals[4][0]                        #P2 party 5 name, hp, type 1, type 2
        row[81] = 1.0
        row[82] = bvals[4][1]
        row[83] = bvals[4][2]
        row[84] = bvals[5][0]                        #P2 party 6 name, hp, type 1, type 2
        row[85] = 1.0
        row[86] = bvals[5][1]
        row[87] = bvals[5][2]
        row[88] = 0.0                                #P1 chosen move/switch (0 if unknown)
        row[89] = 0.0
        row[90] = 0.0
        row[91] = 0.0
        row[92] = 0.0
        row[93] = format(score, '.7f')   #Result (turns to win/loss for P1) (negative if P1 lost)
        #print(str(i) + ": " + str(row))
        if i == nturns:
            i = 1
            score = p2_score
            avals = p2_vals
            bvals = p1_vals
        else:
            i += 1

    #Filling in missing data from turns
    turns = game_log.split('|turn|')[1:]
    i = 1
    players = ['1', '2']
    amons = p1_mons
    amoves = p1_moves
    avals = p1_vals
    bmons = p2_mons
    bmoves = p2_moves
    bvals = p2_vals
    for p in players:
        #print('Player ' + p)
        for t, turn in enumerate(turns, start=1):
            lastTurn = False
            if i % nturns == 0: lastTurn = True
            lines = turn.split('\n')
            fainted = False
            #print('Turn ' + str(t))
            for line in lines:
                if '|faint|p' + p + 'a: ' in line:
                    fainted = True
                if '|move|p' + p + 'a: ' in line:
                    user, move = get_move_from_line(line)
                    for j, mon in enumerate(amons):
                        if user in mon: u = j
                    m = amoves[u].index(move)
                    data[i-1][88] = avals[u][(5*m)+3]
                    data[i-1][89] = avals[u][(5*m)+4]
                    data[i-1][90] = avals[u][(5*m)+5]
                    data[i-1][91] = avals[u][(5*m)+6]
                    data[i-1][92] = avals[u][(5*m)+7]
                    #print('Move: ' + user + ' ' + move)
                if not lastTurn and ('|-damage|' in line or '|-heal|' in line or '|-sethp|' in line):
                    if 'move: Revival Blessing' in line: 
                        player, receiver, new_hp = get_revive_from_line(line)
                        hp_val = hp_str_to_val(new_hp)
                        if player == p:
                            idx = amons.index(receiver)
                        else:
                            idx = bmons.index(receiver)
                        data[i] = assign_hp(data[i], idx+1, player == p, hp_val)
                    else: 
                        player, new_hp = get_hp_update_from_line(line)
                        hp_val = hp_str_to_val(new_hp)
                        if player == p:
                            data[i][1] = hp_val
                        else:
                            data[i][45] = hp_val
                    #print('HP: ' + receiver + ' to ' + new_hp)
                if '|switch|' in line or '|replace|' in line or '|drag|' in line:
                    player, new_mon = get_switch_from_line(line)
                    isPa = player == p
                    if isPa: 
                        vals = avals
                        idx = amons.index(new_mon)
                    else: 
                        vals = bvals
                        idx = bmons.index(new_mon)
                    if not lastTurn: 
                        switches = np.vstack((switches, np.append(data[i][:92], data[i][93])))
                        data[i] = mon_swap(data[i], vals, isPa, idx, replace='|replace|' in line)
                        switches[len(switches)-1][88] = invert(data[i][0])
                        switches[len(switches)-1][89] = invert(data[i][1])
                        switches[len(switches)-1][90] = invert(data[i][2])
                        switches[len(switches)-1][91] = invert(data[i][3])
                        if '|switch|' in line and isPa and not fainted and data[i-1][88] == 0:
                            data[i-1][88] = invert(data[i][0])
                            data[i-1][89] = invert(data[i][1])
                            data[i-1][90] = invert(data[i][2])
                            data[i-1][91] = invert(data[i][3])
                    #print('Switch: P' + str(player) + ' ' + new_mon)
            #Carry data over into next turn
            if t < nturns-1:
                for j in range(88):
                    data[i+1][j] = data[i][j]
            i += 1
        amons = p2_mons
        amoves = p2_moves
        avals = p2_vals
        bmons = p1_mons
        bmoves = p1_moves
        bvals = p1_vals

    return (data, switches)

def get_move_from_line(line: str) -> tuple:
    user = line[len('|move|pxa: '):]
    user = user[:user.find('|')]
    move = line[len('|move|pxa: ')+len(user)+1:]
    move = move[:move.find('|')]
    
    return (user, move)

def get_switch_from_line(line: str) -> tuple:
    player = line[line.find('|p')+2]
    new_mon = line[:line.find(',')]
    new_mon = new_mon[new_mon.rfind('|')+1:]
    #Palafin addendum
    if new_mon == 'Palafin-Hero': new_mon = 'Palafin'

    return (player, new_mon)

def get_hp_update_from_line(line: str) -> tuple:
    player = line[line.find('|p')+2]
    receiver = line[line.find('a: ')+len('a: '):]
    receiver = receiver[:receiver.find('|')]
    new_hp = line[line.find('a: ')+len('a: ')+len(receiver)+1:]

    return (player, new_hp)

def get_revive_from_line(line: str) -> tuple:
    player = line[line.find('|p')+2]
    receiver = line[line.find(': ')+len(': '):]
    receiver = receiver[:receiver.find('|')]
    new_hp = line[line.find(': ')+len(': ')+len(receiver)+1:]

    return (player, receiver, new_hp)

def hp_str_to_val(hp: str) -> float:
    if hp.find(' ') != -1:
        if hp.find('|') == -1:
            end = hp.find(' ')
        elif hp.find(' ') < hp.find('|'):
            end = hp.find(' ')
        else:
            end = hp.find('|')
    elif hp.find('|') != -1:
        end = hp.find('|')
    else: 
        end = len(hp)
    hp = hp[:end]
    if hp != '0':
        nums = hp.split('/')
        return format(int(nums[0]) / int(nums[1]), '.7f')
    else:
        return 0.0
    
def assign_hp(row: np.array, mon: np.array, pa: bool, hp_val: float):
    s = ((mon-1) * 4) + 20
    if not pa: s += 44
    row[s] = hp_val
    return row

def mon_to_vals(mon: str) -> tuple:
    for _, poke in pokemon.iterrows():
        if mon == poke[0]:
            return (poke[1], poke[2], poke[3])
    for _, poke in pokemon.iterrows():
        if mon in poke[0] or poke[0] in mon:
            return (poke[1], poke[2], poke[3])

def move_to_vals(move: str) -> tuple:
    for _, mo in moves.iterrows():
        if move == mo[0]:
            return (mo[1], mo[2], mo[3], mo[4], mo[5])
        
def mon_swap(row: np.array, vals: np.array, isPa: bool, idx: int, replace: bool=False) -> np.array:
    s1 = 0
    s2 = 24
    if not isPa:
        s1 += 44
        s2 += 44
    
    for i in range(5):
        if vals[idx][0] == row[(i*4)+s2]:
            s2 += i*4
            break
    
    for i in range(20):
        row[s1+i+4] = vals[idx][i+3]

    for i in range(4):
        if replace and i == 1: continue
        temp = row[s1+i]
        row[s1+i] = row[s2+i]
        row[s2+i] = temp

    return row

def invert(num):
    if num == 0.0: return num
    else: return num * -1.0

def result_score(nturns: int, iwon: bool) -> float:
    if nturns > 100: nturns = 100
    if iwon:
        return ((100-nturns)/200) + 0.5
    else:
        return nturns/200

def write_turns_to_file(data: np.array, out_path: str):
    """ 
    Takes as input a matrix of data and outputs
    the data to a file.

    Returns: none
    """

    with open(out_path, 'w') as file:
        file.write('p1,p1hp,p1t1,p1t2,move1,m1t,m1c,m1p,m1a,move2,m2t,m2c,m2p,m2a,move3,m3t,m3c,m3p,m3a,move4,m4t,m4c,m4p,m4a,p2,p2hp,p2t1,p2t2,p3,p3hp,p3t1,p3t2,p4,p4hp,p4t1,p4t2,p5,p5hp,p5t1,p5t2,p6,p6hp,p6t1,p6t2,o1,o1hp,o1t1,o1t2,omove1,om1t,om1c,om1p,om1a,omove2,om2t,om2c,om2p,om2a,omove3,om3t,om3c,om3p,om3a,omove4,om4t,om4c,om4p,om4a,o2,o2hp,o2t1,o2t2,o3,o3hp,o3t1,o3t2,o4,o4hp,o4t1,o4t2,o5,o5hp,o5t1,o5t2,o6,o6hp,o6t1,o6t2,choice,c1,c2,c3,c4,result\n')
        for row in data:
            out_line = ''
            for element in row:
                out_line = out_line + str(element) + ','
            file.write(out_line[:-1] + '\n')

def write_switches_to_file(data: np.array, out_path: str):
    """ 
    Takes as input a matrix of data and outputs
    the data to a file.

    Returns: none
    """

    with open(out_path, 'w') as file:
        file.write('p1,p1hp,p1t1,p1t2,move1,m1t,m1c,m1p,m1a,move2,m2t,m2c,m2p,m2a,move3,m3t,m3c,m3p,m3a,move4,m4t,m4c,m4p,m4a,p2,p2hp,p2t1,p2t2,p3,p3hp,p3t1,p3t2,p4,p4hp,p4t1,p4t2,p5,p5hp,p5t1,p5t2,p6,p6hp,p6t1,p6t2,o1,o1hp,o1t1,o1t2,omove1,om1t,om1c,om1p,om1a,omove2,om2t,om2c,om2p,om2a,omove3,om3t,om3c,om3p,om3a,omove4,om4t,om4c,om4p,om4a,o2,o2hp,o2t1,o2t2,o3,o3hp,o3t1,o3t2,o4,o4hp,o4t1,o4t2,o5,o5hp,o5t1,o5t2,o6,o6hp,o6t1,o6t2,choice,c1,c2,c3,result\n')
        for row in data:
            out_line = ''
            for element in row:
                out_line = out_line + str(element) + ','
            file.write(out_line[:-1] + '\n')

def append_data_to_file(data: np.array, out_path: str):
    """ 
    Takes as input a matrix of turn data and appends
    the data to a file.

    Returns: none
    """

    with open(out_path, 'a') as file:
        for row in data:
            out_line = ''
            for element in row:
                out_line = out_line + str(element) + ','
            file.write(out_line[:-1] + '\n')

def append_urls_to_file(urls: np.array, out_path: str):
    """ 
    Takes as input an array of replay urls and appends
    the urls to a file.

    Returns: none
    """

    with open(out_path, 'a') as file:
        for url in urls:
            file.write(url + ', \n')

def clean_replays(file_path: str):
    with open(file_path, 'w') as file:
        file.write('urls, \n')

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')

    replays_path = os.path.join(os.path.dirname(__file__), 'data/replays.csv')
    print('Beginning processing...')
    pokemon, moves = prep_data()
    turns, switches, urls = pre_process(replays_path)
    print('Outputting to file...')
    append_urls_to_file(urls, 'data/done_replays.csv')
    clean_replays(replays_path)
    append_data_to_file(turns, "data/turns.csv")
    append_data_to_file(switches, "data/switches.csv")

    print('Done!')