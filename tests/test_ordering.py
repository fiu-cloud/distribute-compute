from random import shuffle
import compute.gpdb_io as io

test = [["0","a"],["1","b"],["2","c"],["3","d"]]
distributed_store = io.writeOrdered(test)
shuffle(distributed_store)
print("unordered: "+ str(distributed_store))
print("ordered: "+ str(io.readOrdered(distributed_store)))
