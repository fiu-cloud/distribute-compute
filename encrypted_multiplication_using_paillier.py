import phe.paillier as paillier, numpy as np,sys, math, random
import compute.gpdb_io as io
import compute.serialisation as ser
party = sys.argv[1]
_s3_endpoint = sys.argv[2]
_s3_bucket = sys.argv[3]
_host = sys.argv[4]
_database = sys.argv[5]
_user = sys.argv[6]
_password = sys.argv[7]
_s3_finished = "_finished_"
_poll_seconds = 1
# https://mentalmodels4life.net/2018/07/07/multiplication-and-comparison-operations-in-paillier/
io.init(_host,_database,_user,_password,_s3_endpoint, _s3_bucket,_poll_seconds)


# write the thetas to a local store
thetas = open("results.log", "a",1)

def main():

    if party == "p": # private key holder
        pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
        key = ser.serialisePubKey(pubkey)
        io.write([[key]], "pubkey/", "key text",-1)
        x_dash = prikey.decrypt(ser.deserialiseEncrypted(pubkey,(io.read("x/", "value text",0))[0][0]))
        y_dash = prikey.decrypt(ser.deserialiseEncrypted(pubkey,(io.read("y/", "value text",0))[0][0]))
        z = ser.serialiseEncrypted(pubkey.encrypt(x_dash * y_dash))
        io.write([[z]],"z/","value text",0)
        result = prikey.decrypt(ser.deserialiseEncrypted(pubkey,(io.read("multiply_part_b/", "value text",0))[0][0]))
        thetas.write("multiplication result: "+ str(result) + "\r\n")
    elif party == "x":
        x = math.pi
        pubkey = ser.deserialisePubKey((io.read("pubkey/", "key text",-1))[0][0])
        x_rand = random.random() * x
        x_dash = ser.serialiseEncrypted(pubkey.encrypt(x)*x_rand)
        io.write([[x_dash]],"x/","value text",0)
        z = ser.deserialiseEncrypted(pubkey,(io.read("z/", "value text",0))[0][0])
        multiply_part_a = ser.serialiseEncrypted(z * (1/x_rand))
        io.write([[multiply_part_a]],"multiply_part_a/","value text",0)
    elif party == "y":
        y = -math.sqrt(2)
        pubkey = ser.deserialisePubKey((io.read("pubkey/", "key text",-1))[0][0])
        y_rand = random.random() * y
        y_dash = ser.serialiseEncrypted(pubkey.encrypt(y)*y_rand)
        io.write([[y_dash]],"y/","value text",0)
        multiply_part_a = ser.deserialiseEncrypted(pubkey,(io.read("multiply_part_a/", "value text",0))[0][0])
        multiply_part_b = ser.serialiseEncrypted(multiply_part_a * (1/y_rand))
        io.write([[multiply_part_b]],"multiply_part_b/","value text",0)



main()
