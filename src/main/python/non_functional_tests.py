
import time, phe.paillier as paillier, random, pickle,binascii,math,sys,base64
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)


iterations = 1000

def serialisePubKey(inputPubKey):
    return str(inputPubKey.n)

def deserialisePubKey(inputSerialisedKey):
    #g will always be n + 1
    return paillier.PaillierPublicKey(int(inputSerialisedKey))

def serialiseEncrypted(inputEncrypted):
    return str(inputEncrypted.ciphertext()) + " " +str(inputEncrypted.exponent)

def deserialiseEncrypted(pubKey, input):
    cipher,exponent = input.split(" ")
    output = paillier.EncryptedNumber(pubKey, int(cipher), int(exponent))
    return output

def serialisePriKey(input):
    return binascii.b2a_base64(pickle.dumps(input)).decode('ascii')

def deserialisePriKey(input):
    return pickle.loads(binascii.a2b_base64(input.encode('ascii')))

print("Serialisation test 1 : "+ str(math.fabs(math.pi * 3 - prikey.decrypt(pubkey.encrypt(math.pi) + pubkey.encrypt(math.pi) * 2)) < 0.01))
pubkey2 = deserialisePubKey(serialisePubKey(pubkey))
prikey2 = deserialisePriKey(serialisePriKey(prikey))
print("Serialisation test 2 : "+ str(math.fabs(math.pi * 3 - prikey.decrypt(pubkey.encrypt(math.pi) + pubkey2.encrypt(math.pi) * 2)) < 0.01))
print("Serialisation test 3 : "+ str(math.fabs(math.pi * 3 - prikey2.decrypt(pubkey.encrypt(math.pi) + pubkey.encrypt(math.pi) * 2)) < 0.01))
partA = deserialiseEncrypted(pubkey2,serialiseEncrypted(pubkey.encrypt(math.pi)))
partB = pubkey2.encrypt(math.pi) * 2
partC = deserialiseEncrypted(pubkey,serialiseEncrypted(pubkey2.encrypt(math.pi))) * 3
print("Serialisation test 4 : "+ str(math.fabs((math.pi * 12 - prikey2.decrypt((partA + partB + partC)*2))) < 0.01))


raw = []
start = time.time()
for i in range(0, iterations):
    if random.random() < 0.5:
        raw.append(random.random()* 10000000.01)
    else:
        raw.append(-(random.random()* 10000000.01))
total_elapsed = time.time() - start
elapsed = 1/(total_elapsed / iterations)
print("GENERATE RAND (ops/second) "+str(elapsed))

encrypted = []
start = time.time()
for i in range(0, iterations):
    encrypted.append(pubkey.encrypt(raw[i]))
total_elapsed = time.time() - start
elapsed = 1/(total_elapsed / iterations)
print("ENCRYPTION (ops/second) "+str(elapsed))

encrypted2 = []
start = time.time()
for i in range(0, iterations):
    encrypted2.append(deserialiseEncrypted(pubkey,serialiseEncrypted(encrypted[i])))

total_elapsed = time.time() - start
elapsed = 1/(total_elapsed / iterations)
print("SERIALISE & DESERIALISE(ops/second) "+str(elapsed))


encrypted2 =encrypted.copy()
random.shuffle(encrypted2)
raw2 = raw.copy()
random.shuffle(raw2)

additions = []
start = time.time()
for i in range(0, iterations):
    additions.append(encrypted[i] + encrypted2[i])
total_elapsed = time.time() - start
elapsed = 1/(total_elapsed / iterations)
print("ADDITIONS (ops/second) "+str(elapsed))

products = []
start = time.time()
for i in range(0, iterations):
    products.append(encrypted[i] * raw2[i])
total_elapsed = time.time() - start
elapsed = 1/(total_elapsed / iterations)
print("MULTIPLICATIONS (ops/second) "+str(elapsed))