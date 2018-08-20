import math
import itertools
import phe.paillier as paillier
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

a = math.pi
b = -a
c = (1+math.pi*(10 ** -10))
d = -c
e = math.pi*(10 ** 17)
f = -e

tests = [a,b,c,d,e,f]
combos = itertools.combinations(tests, 2)

def formatDiff(inNumber):
    return '%.2E' % inNumber

def formatPad(inNumber):
    if abs(inNumber) > 10e+17:
        out = ("%+.3f"%inNumber)
    else:
        out = ("%+.20f"%inNumber).zfill(40)
    return out

def encDecTest():
    print()

    print("Encrypt-Decrypt test")
    print("                  a                                        dec(enc(a))                a-dec(enc(a))")
    print("---------------------------------------------------------------------------------------------------")
    for x in tests:
        ex = prikey.decrypt(pubkey.encrypt(x))
        print(formatPad(x) + "   "+formatPad(ex) +"    "+ formatDiff(x - ex))
    return

def additionTest():
    print()
    print("Addition test")
    print("                  a                                      b                       (a+b)-dec(enc(a)+enc(b))              a+b                                dec(enc(a)+enc(b)")
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    for x in combos:
        added = x[0]+x[1]
        e_x0 = pubkey.encrypt(x[0])
        e_x1 = pubkey.encrypt(x[1])
        e_added = e_x0 + e_x1
        d_added = prikey.decrypt(e_added)
        diff = added - d_added
        print(formatPad(x[0]) + "  "+formatPad(x[1])+"     "+formatDiff(diff)+"     "+ formatPad(added)+ "  "+formatPad(d_added))
    return

def multiplicationTest1():
    print()
    print("Multiplication test A")
    print("                  a                                      b                       (a*b)-dec(enc(a)*b)              a*b                                dec(enc(a)*b)")
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    for x in combos:
        multiplied = x[0]*x[1]
        e_x0 = pubkey.encrypt(x[0])
        e_x1 = pubkey.encrypt(x[1])
        e_multiplied = e_x0 * x[1]
        d_multiplied = prikey.decrypt(e_multiplied)
        diff = multiplied - d_multiplied
        print(formatPad(x[0]) + ", "+formatPad(x[1])+", "+formatDiff(diff)+", "+ formatPad(multiplied)+ ","+formatPad(d_multiplied))
    return

def multiplicationTest2():
    print()
    print("Multiplication test B")
    print("                  a                                      b                       (a*b)-dec(a*enc(b))              a*b                                dec(a*enc(b))")
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    for x in combos:
        multiplied = x[0]*x[1]
        e_x0 = pubkey.encrypt(x[0])
        e_x1 = pubkey.encrypt(x[1])
        e_multiplied = e_x1 * x[0]
        d_multiplied = prikey.decrypt(e_multiplied)
        diff = multiplied - d_multiplied
        print(formatPad(x[0]) + ", "+formatPad(x[1])+", "+formatDiff(diff)+", "+ formatPad(multiplied)+ ","+formatPad(d_multiplied))
    return

#encDecTest()
additionTest()
#multiplicationTest1()
#multiplicationTest2()

