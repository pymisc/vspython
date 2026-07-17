# Here goes lists operations and examples in Python

########################################################
nums = [25,10,9,20,87]

print ("\nHere is the entire list")
print(nums)

print ("\nFirst member of list")
print(nums[0])

print("\nThird member to end of list")
print(nums[2:])

print("\nLast member of list")
print(nums[-1])

print("\n5th member from right hand side")
print(nums[-5])

########################################################

names = ['vikas', 'john', 'paul','tom']

print("\nHere is the entire list")
print(names)

########################################################

values = [10.2,'vikas',54,56]
print("\nHere goes list with multiple types of values in it")
print(values)

########################################################

mixedlst=[nums, names, values]
print("\nHere goes mixing two separate list into one - lists within list")
print(mixedlst)

########################################################

print("\nLists operations - remove. pop, insert etc")
print("\nLISTS - Append")
nums.append(2000)
print(nums)

print("\nLISTS - Insert at a spencific index number")
nums.insert(1,2001)
print(nums)

print("\nLISTS - use of clear function")
nums.clear()
print(nums)
