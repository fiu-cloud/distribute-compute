def schema(iteration):
    return "(a text, b integer, c float8)"

def iterationCount():
    return 10

def init(party):
    if party == "a":
        rowCount = 1000000
        data = []
        for i in range(0, rowCount, 1):
            data.append([str(i),i,i+0.5])
        return data
    else:
        return []

def apply(iteration,party,input):
    return list(map(lambda x: [x[0], x[1]+1, x[2]+1], input))

def iterationIncrementor(party,iteration):
    if party == "a":
        return iteration
    else:
        return iteration + 1