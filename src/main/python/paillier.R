
library(homomorpheR)
keypair <<- PaillierKeyPair$new(modulusBits = 1024)
pubkey <<- keypair$pubkey
privkey  <<-keypair$getPrivateKey()
largenum <<- 2^50
zero  <<- pubkey$encrypt("0")

# Convenience function
zipf <<- function(x1,x2,x3) {
    res = c()
    for (i in 1:length(x1)) res = c(res,x1[i],x2[i],x3[i])
    res
}

encodeFloat <<- function(x, e=0) {
    x = x * 10^e
    x1 = floor(x)
    x2 = x - x1
    x2 = floor(x2 * largenum)
    exps = rep(e, length(x))
    zipf(x1,x2,exps)
}

encrypt <<- function(z, e=0) {
    y = encodeFloat(z, e)
    res = rep(zero, length(y))
    for (i in 1:length(y)) {
        if (i %% 3 == 0) { res[i] = y[i] }
        else { res[i] = pubkey$encrypt((y[i])) }
    }
    res
}

decrypt <<- function(en) {
    uen = en
    for (i in 1:length(uen)) {
        if (i %% 3 != 0) uen[i] = privkey$decrypt(en[i])
    }
    # deal with negative results
    for (i in 1:length(uen)) {
        if (i %% 3 != 0 && # don't process exponents
        uen[i] >= as.double(pubkey$n/3.0)) { uen[i] = uen[i] - pubkey$n }
    }
    res = c()
    for (i in seq(1, length(uen), 3)) {
        res = c(res,
        (as.double(uen[i]) + as.double(uen[i+1]/(largenum))) / as.double(10^uen[i+2]))
    }
    return(res)
}


addenc <<- function(x, y) {
    res = x
    for (i in seq(1, length(x), 3)) {
        if (x[i+2] != y[i+2]) { # if different exponent, make the exponents equal by multiplying
            res[i+2] = max(x[i+2], y[i+2])
            xdiff = res[i+2] - x[i+2]
            ydiff = res[i+2] - y[i+2]
            if (xdiff > 0) {
                x[i] = pubkey$mult(x[i], 10^(xdiff))
                x[i+1] = pubkey$mult(x[i+1], 10^(xdiff))
            }
            if (ydiff > 0) {
                y[i] = pubkey$mult(y[i], 10^(ydiff))
                y[i+1] = pubkey$mult(y[i+1], 10^(ydiff))
            }
        }
        res[i] = pubkey$add(x[i], y[i])
        res[i+1] = pubkey$add(x[i+1], y[i+1])
    }
    res
}

subenc <<- function(x, y) {
    for (i in seq(1, length(x), 3)) {
        y[i] = pubkey$mult(y[i], -1)
        y[i+1] = pubkey$mult(y[i+1], -1)
    }
    addenc(x, y)
}

smultenc <<- function(x,y) {
    prec = 5
    yint = floor(y * 10^prec)
    res = x
    for (i in seq(1, length(x), 3)) {
        res[i] = pubkey$mult(x[i], yint)
        res[i+1] = pubkey$mult(x[i+1], yint)
        res[i+2] = x[i+2] + prec
    }
    res
}
