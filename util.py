import os
import json
import pandas as pd

def get_moves() -> None:
    with open('data/pokemon.txt') as f:
        data = f.read()
    data = data.strip()
    data = data[3:]
    j = json.loads(data)
    
    moves = set()

    for pokemon_data in j.values():
        roles = pokemon_data.get('roles', {})
        for role in roles.values():
            role_moves = role.get('moves', {})
            moves.update(role_moves.keys())

    moves = sorted(moves)

    with open('data/moves.txt', 'w') as f:
         f.write('\n'.join(moves))

def fix_switches():
    turns = pd.read_csv('data/turns.csv')

    for idx, row in turns.iterrows():
        if pd.isnull(row['choice']):
            turns.loc[idx, 'choice'] = turns.loc[idx+1, 'p1'] * -1
            turns.loc[idx, 'c1'] = turns.loc[idx+1, 'p1hp'] * -1
            turns.loc[idx, 'c2'] = turns.loc[idx+1, 'p1t1'] * -1
            turns.loc[idx, 'c3'] = turns.loc[idx+1, 'p1t2'] * -1

    turns.to_csv('data/turns.csv', index=False)

def update_data_moves(pos: int):
    #pos is the position of the new move

    moves = pd.read_csv('data/moves.csv')
    turns = pd.read_csv('data/turns.csv')
    switches = pd.read_csv('data/switches.csv')

    for idx, row in turns.iterrows():
        try:
            turns.loc[idx, 'move1'] = update_entry(row['move1'], len(moves), pos)
            turns.loc[idx, 'move2'] = update_entry(row['move2'], len(moves), pos)
            turns.loc[idx, 'move3'] = update_entry(row['move3'], len(moves), pos)
            turns.loc[idx, 'move4'] = update_entry(row['move4'], len(moves), pos)
            turns.loc[idx, 'omove1'] = update_entry(row['omove1'], len(moves), pos)
            turns.loc[idx, 'omove2'] = update_entry(row['omove2'], len(moves), pos)
            turns.loc[idx, 'omove3'] = update_entry(row['omove3'], len(moves), pos)
            turns.loc[idx, 'omove4'] = update_entry(row['omove4'], len(moves), pos)
            if row['choice'] > 0:
                turns.loc[idx, 'choice'] = update_entry(row['choice'], len(moves), pos)
        except:
            print(idx)
            return
        
    for idx, row in switches.iterrows():
        try:
            switches.loc[idx, 'move1'] = update_entry(row['move1'], len(moves), pos)
            switches.loc[idx, 'move2'] = update_entry(row['move2'], len(moves), pos)
            switches.loc[idx, 'move3'] = update_entry(row['move3'], len(moves), pos)
            switches.loc[idx, 'move4'] = update_entry(row['move4'], len(moves), pos)
            switches.loc[idx, 'omove1'] = update_entry(row['omove1'], len(moves), pos)
            switches.loc[idx, 'omove2'] = update_entry(row['omove2'], len(moves), pos)
            switches.loc[idx, 'omove3'] = update_entry(row['omove3'], len(moves), pos)
            switches.loc[idx, 'omove4'] = update_entry(row['omove4'], len(moves), pos)
            if row['choice'] > 0:
                switches.loc[idx, 'choice'] = update_entry(row['choice'], len(moves), pos)
        except:
            print(idx)
            return

    #print(turns)
    turns.to_csv('data/turns.csv', index=False)
    switches.to_csv('data/switches.csv', index=False)

def update_data_mons(pos: int):
    #pos is the position of the new mon

    mons = pd.read_csv('data/pokemon.csv')
    turns = pd.read_csv('data/turns.csv')
    switches = pd.read_csv('data/switches.csv')

    for idx, row in turns.iterrows():
        try:
            turns.loc[idx, 'p1'] = update_entry(row['p1'], len(mons), pos)
            turns.loc[idx, 'p2'] = update_entry(row['p2'], len(mons), pos)
            turns.loc[idx, 'p3'] = update_entry(row['p3'], len(mons), pos)
            turns.loc[idx, 'p4'] = update_entry(row['p4'], len(mons), pos)
            turns.loc[idx, 'p5'] = update_entry(row['p5'], len(mons), pos)
            turns.loc[idx, 'p6'] = update_entry(row['p6'], len(mons), pos)
            turns.loc[idx, 'o1'] = update_entry(row['o1'], len(mons), pos)
            turns.loc[idx, 'o2'] = update_entry(row['o2'], len(mons), pos)
            turns.loc[idx, 'o3'] = update_entry(row['o3'], len(mons), pos)
            turns.loc[idx, 'o4'] = update_entry(row['o4'], len(mons), pos)
            turns.loc[idx, 'o5'] = update_entry(row['o5'], len(mons), pos)
            turns.loc[idx, 'o6'] = update_entry(row['o6'], len(mons), pos)
            if row['choice'] < 0:
                turns.loc[idx, 'choice'] = update_entry(row['choice']*-1, len(mons), pos) * -1
        except:
            print(idx)
            return
        
    for idx, row in switches.iterrows():
        try:
            switches.loc[idx, 'p1'] = update_entry(row['p1'], len(mons), pos)
            switches.loc[idx, 'p2'] = update_entry(row['p2'], len(mons), pos)
            switches.loc[idx, 'p3'] = update_entry(row['p3'], len(mons), pos)
            switches.loc[idx, 'p4'] = update_entry(row['p4'], len(mons), pos)
            switches.loc[idx, 'p5'] = update_entry(row['p5'], len(mons), pos)
            switches.loc[idx, 'p6'] = update_entry(row['p6'], len(mons), pos)
            switches.loc[idx, 'o1'] = update_entry(row['o1'], len(mons), pos)
            switches.loc[idx, 'o2'] = update_entry(row['o2'], len(mons), pos)
            switches.loc[idx, 'o3'] = update_entry(row['o3'], len(mons), pos)
            switches.loc[idx, 'o4'] = update_entry(row['o4'], len(mons), pos)
            switches.loc[idx, 'o5'] = update_entry(row['o5'], len(mons), pos)
            switches.loc[idx, 'o6'] = update_entry(row['o6'], len(mons), pos)
            if row['choice'] < 0:
                switches.loc[idx, 'choice'] = update_entry(row['choice']*-1, len(mons), pos) * -1
        except:
            print(idx)
            return

    #turns.to_csv('data/turns.csv', index=False)
    switches.to_csv('data/switches.csv', index=False)

def update_entry(val: float, len: int, pos: int) -> float:
    num = round(val * (len-1))
    if num >= pos: num += 1
    return format(num/(len), '.7f')

def update_moves() -> None:
    with open('data/movedata.txt') as f:
        movedata = f.read()

    with open('data/moves.txt') as f:
        moves = f.read().split('\n')

    with open('data/types.txt') as f:
        types = f.read().split('\n')

    cmoves = ['Struggle,0.0,0.0,0.0,0.2000000,1.0000000']
    for idx, move in enumerate(moves, start = 1):
        m = move.lower()
        m = m.replace(' ', '')
        m = m.replace('-', '')
        mo = movedata[movedata.find(m + ': {'):]
        mo = mo[:mo.find('contestType: ')]
        mval = format(idx/len(moves), '.7f')
        typee = mo[mo.find('type: "') + len('type: "'):]
        typee = typee[:typee.find('"')]
        for i, t in enumerate(types, start = 1):
            if t == typee: 
                typee = format(i/len(types), '.7f')
                break
        category = mo[mo.find('category: "') + len('category: "'):]
        category = category[:category.find('"')]
        if category == 'Physical':
            category = 0.0
        elif category == 'Special':
            category = 1.0
        elif category == 'Status':
            category = 0.5
        power = mo[mo.find('basePower: ') + len('basePower: '):]
        power = power[:power.find(',')]
        power = format(float(power)/250, '.7f')
        accuracy = mo[mo.find('accuracy: ')+ len('accuracy: '):]
        accuracy = accuracy[:accuracy.find(',')]
        if accuracy == 'true': accuracy = '101'
        accuracy = format(float(accuracy)/101, '.7f')
        cmoves.append(move + ',' + str(mval) + ',' + str(typee) + ',' + str(category) + ',' + str(power) + ',' + str(accuracy))

    return cmoves

def update_pokemon() -> None:
    with open('data/pokedex.txt') as f:
        pokedex = f.read()

    with open('data/pokemon.txt') as f:
        pokemon = f.read()

    with open('data/types.txt') as f:
        types = f.read().split('\n')

    pokemon = pokemon.split('\n')[1:-1]
    cmons = []
    for idx, mon in enumerate(pokemon, start=1):
        mon = mon[mon.find('"') + len('"'):]
        mon = mon[:mon.find('"')]
        m = mon.lower()
        m = m.replace(' ', '')
        m = m.replace('-', '')
        mval = format(idx/len(pokemon), '.7f')
        pok = pokedex[pokedex.find(m + ': {'):]
        pok = pok[:pok.find('color: ')]
        ts = pok[pok.find('types: [') + len('types: ['):]
        ts = ts[:ts.find(']')]
        ts = ts.replace('"', '')
        ts = ts.split(', ')
        t1 = ts[0].strip()
        for i, t in enumerate(types, start = 1):
            if t == t1: 
                t1 = format(i/len(types), '.7f')
                break
        t2 = 0.0
        if len(ts) > 1:
            t2 = ts[1].strip()
            for i, t in enumerate(types, start = 1):
                if t == t2: 
                    t2 = format(i/len(types), '.7f')
                    break
        cmons.append(mon + ',' + str(mval) + ',' + str(t1) + ',' + str(t2))

    return cmons

def check_lens():
    turns = pd.read_csv('data/turns.csv')
    switches = pd.read_csv('data/switches.csv')

    for _, row in turns.iterrows():
        if len(row) != 94: print(len(row))
    for _, row in switches.iterrows():
        if len(row) != 94: print(len(row))

def remove_empty():
    switches = pd.read_csv('data/switches.csv')

    switches = switches.drop('c4', axis=1)

    switches.to_csv('data/switches.csv', index=False)

def rework_results():
    turns = pd.read_csv('data/turns.csv')
    switches = pd.read_csv('data/switches.csv')

    for idx, row in switches.iterrows():
        for i, data in turns.iterrows():
            if row['result'] == data['result']:
                switches.loc[idx, 'result'] = i
                break
    count = 0
    for idx, row in turns.iterrows():
        count += 1
        if row['result'] == 1.0:
            if count > 100: count = 100
            for i in range(count):
                turns.loc[idx-i, 'result'] = ((100-count)/200) + 0.5
            count = 0
        elif row['result'] == -1.0:
            if count > 100: count = 100
            for i in range(count):
                turns.loc[idx-i, 'result'] = count/200
            count = 0
    for idx, row in switches.iterrows():
        switches.loc[idx, 'result'] = turns.loc[row['result'], 'result']

    turns.to_csv('data/turns.csv', index=False)
    switches.to_csv('data/switches.csv', index=False)

def write_moves_to_file(data: list, out_path: str):
    with open(out_path, 'w') as file:
        file.write('name,nameval,tval,catval,bpval,accval\n')
        for move in data:
            file.write(move + '\n')

def write_pokemon_to_file(data: list, out_path: str):
    with open(out_path, 'w') as file:
        file.write('name,nameval,type1,type2\n')
        for mon in data:
            file.write(mon + '\n')

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')

    update_data_moves(2)