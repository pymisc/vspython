# Just to test some basic printing in python

# operators testing
print ("Addition       3 + 2   = ", 3+2)     # addition operator
print ("Multiplication 2 * 3   = ", 2*3)     # multiplication operator
print ("Division       9 / 2   = ", 9/2 )     # division operator
print ("Exponent       2 ** 3  = ", 2 ** 3)    # exponent operator
print ("Floor div      9 // 2  = ", 9 // 2)  # floor division operator 
print ("Modulus        9 % 2   = ", 9 % 2)   # modulus operator - for remainder

# escaping ' in print statement
print ("\n")
print ('vikas\'s "laptop"')

print("Using variables")
x = 2
y = 3
print (x+y)

#z = x + y
#p = print(_) + 10   # This '_' works in IDLE but not here, yet to find how to bring previous value.
#print (p)

print ('{:25s}{:25s}{:35s}'.format("Hello","Testing","third var"))

print ('{:25s}{:15s}{:15s}'.format("Operation","Values","Result"))
print ('{:25s}{:15s}{:15d}'.format("Sum","3+2",3+2))
print ('{:25s}{:15s}{:15f}'.format("Sum","3+2",3+2))

print ("Hello".rjust(10))
print ("Hello".ljust(10))

# Spacing size definitions (will be used in rjust and ljust)
s1=7
s2=20
s3=30

print ("Addition".ljust(s2), "3 + 2".ljust(s1), "=", (3+2))     # addition operator
print ("Multiplication".ljust(s2), "2 * 3".ljust(s1), "=", (2*3))     # multiplication operator
#print ("Division       9 / 2   = ", 9/2 )     # division operator
#print ("Exponent       2 ** 3  = ", 2 ** 3)    # exponent operator
#print ("Floor div      9 // 2  = ", 9 // 2)  # floor division operator 
#print ("Modulus        9 % 2   = ", 9 % 2)   # modulus operator - for remainder
