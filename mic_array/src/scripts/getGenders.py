
genders = {}

def getGenders(speakers, pairs):
    with open(speakers) as s:
        lines = s.readlines()

    for line in lines:
        line = line.strip().split('|')
        genders[int(line[0])] = line[1]

    with open(pairs) as p:
        lines = p.readlines()

    grouped = []

    sum = 0
    prev1 = lines[0].split()[0]
    for pair in lines:
        pair = pair.split()

        if pair[0] == prev1:
            sum += 1
        else:
            grouped.append('{} {} {}{} {}'.format(pair[0], pair[1], genders[int(pair[0])], genders[int(pair[1])], sum))
            sum = 0

        prev1 = pair[0]
    
    with open("D:\kandi\LibriSpeech\speaker_tt_grp.txt", 'w') as w:
        for g in grouped:
            w.write(g + '\n')

getGenders("D:\kandi\LibriSpeech\SPEAKERS-TT.TXT", "D:\\kandi\\LibriSpeech\\test\\task.txt")

