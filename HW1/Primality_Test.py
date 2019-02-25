import math
import random

def simplePrimaryTest(number):
    if number == 2:
       return true
    if number % 2 == 0:
        return False
    
    i = 3
    sqrtOfNumber = math.sqrt(number)
    
    while i <= sqrtOfNumber:
        if number % i == 0:
            return False
        i = i+2
        
    return True

def MillerRabinPrimalityTest(number):
    
    if number == 2:
        return True
    elif number == 1 or number % 2 == 0:
        return False
    

    oddPartOfNumber = number - 1
    
    timesTwoDividNumber = 0
    
    while oddPartOfNumber % 2 == 0:
        oddPartOfNumber = oddPartOfNumber / 2
        timesTwoDividNumber = timesTwoDividNumber + 1 
     

        while True:
            randomNumber = random.randint(2, number)-1
            if randomNumber != 0 and randomNumber != 1:
                break
        
        randomNumberWithPower = pow(randomNumber, oddPartOfNumber, number)
        
        if (randomNumberWithPower != 1) and (randomNumberWithPower != number - 1):
            iterationNumber = 1
            
            while (iterationNumber <= timesTwoDividNumber - 1) and (randomNumberWithPower != number - 1):
                randomNumberWithPower = pow(randomNumberWithPower, 2, number)
                
                iterationNumber = iterationNumber + 1

            if (randomNumberWithPower != (number - 1)):
                return False
            
    return True 
k = input("Give an integer:")
print simplePrimaryTest(k)
#print MillerRabinPrimalityTest(k)
