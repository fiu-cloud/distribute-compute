import phe.paillier as paillier, math, pickle
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
print(pickle.dumps(pubkey))

#encrypted = pubkey.encrypt(math.pi)
#pickledEncrypted = pickle.dumps(encrypted)
#encrypted2 = pickle.loads(pickledEncrypted)
#decrypted = prikey.decrypt(encrypted2)

#print(type(encrypted2))
#print(decrypted)
