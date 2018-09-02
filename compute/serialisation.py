import phe.paillier as paillier,pickle,binascii

def serialisePubKey(inputPubKey):
    return str(inputPubKey.n)

def deserialisePubKey(inputSerialisedKey):
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
