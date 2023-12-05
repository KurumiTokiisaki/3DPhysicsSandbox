f = open('input.txt', 'r')
lines = f.read()
lineArray = lines.splitlines()
tempArray = []
intArray = []
intArrayIdx = []

for l in range(len(lineArray)):
    tempArray.append([])
    intArray.append([])
    intArrayIdx.append([])
    for i in range(len(lineArray[l])):
        tempArray[l].append(lineArray[l][i])

totalArray = []
for c in range(len(tempArray)):
    totalArray.append('')
    for _ in range(len(tempArray[c])):
        totalArray[c] = f'{totalArray[c]}{tempArray[c][_]}'

words = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', '1', '2', '3', '4', '5', '6', '7', '8', '9']
numbers = {
    'one': '1',
    'two': '2',
    'three': '3',
    'four': '4',
    'five': '5',
    'six': '6',
    'seven': '7',
    'eight': '8',
    'nine': '9',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9'
}

print(totalArray)
outArray = []
for w in range(len(totalArray)):
    lowestIdx = float('inf')
    lowestNum = ''
    highestIdx = -float('inf')
    highestNum = ''
    for n in range(len(words)):
        if totalArray[w].find(words[n]) != -1:
            if totalArray[w].find(words[n]) < lowestIdx:
                lowestIdx = totalArray[w].find(words[n])
                lowestNum = numbers[words[n]]
            if totalArray[w].rfind(words[n]) > highestIdx:
                highestIdx = totalArray[w].rfind(words[n])
                highestNum = numbers[words[n]]
    outArray.append(int(lowestNum + highestNum))
print(outArray)
print(sum(outArray))
