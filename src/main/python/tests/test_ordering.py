from random import shuffle

def writeOrdered(input):
    return [x + [i] for i,x in list(enumerate(input))]

def readOrdered(data):
    def getKey(elem):
        return elem[len(elem)-1]
    data.sort(key=getKey)
    return [x[:len(x)-1] for x in data]

test = [["0","a"],["1","b"],["2","c"],["3","d"]]
ordered = writeOrdered(test)
shuffle(ordered)
print(ordered)
print(readOrdered(ordered))
