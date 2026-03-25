
import re


a = 23
Name = "karthick"
balance = 55.4

print("Hello %s. Your age is %d and your balance is $ %f" % (Name,a,round(balance,2)))

String = "Karthick is my name"

print(type(String))

print("Name is " + String[0:8])

print(String *3)

print("Even characters " + String[0::2])

print("Odd characters " + String[::])

print(String.replace(" ","-"))
print(re.sub("k","T",String,flags=re.IGNORECASE))
strings = String.split(" ")
print(strings)

print(String[::-1])

for string in strings:
    print(string[::-1], end=" ")

result = [word[::-1] for word in strings]
print(result)

def sum_list(numbers):
    value = 0
    for number in numbers:
        value += number
    return value

def filter_even(numbers):
    return_list=[]
    for number in numbers:
        if number % 2 == 0 :
            return_list.append(number)
    return return_list

def filter_even_comprehension(numbers):
    return_list=[number for number in numbers if number%2==0]
    return return_list

print(sum_list([1,2,3,4,5,6,7,8]))
print(filter_even([1,2,3,4,5,6,7,8]))
print(filter_even_comprehension([1,2,3,4,5,6,7,8]))

dictionary_value = {"Karthick":23,"Raj":30,"Prakash":75,"Ram Kunar":36}

dictionary_result = {name:age for name,age in dictionary_value.items() if age>30}
print(dictionary_result)

def greet_user(details):
    for name, age in details.items():
        print("Hello %s. Your age is %d." %(name,age))

greet_user(dictionary_value)

def multiply(*args):
    result = 1
    for number in args:
        result *= number
    return result

def addition(*args):
    result = 0
    for number in args:
        result += number
    return result

def subtraction(*args):
    result = args[0]
    for number in args[1:]:
        result -= number
    return result

print(addition(2,3,4,5,6,7,8))
print(subtraction(2,3,4,5,6,7,8))
print(multiply(2,3,4,5,6,7,8))


def getmax(numbers):
    maximum = numbers[0]
    for number in numbers:
        if number>maximum:
            maximum = number
    return maximum


def getmax_list(numbers):
    return max(numbers)

print(getmax([1,2,9,4,5,65,7,8]))


print("max_list:")
print(getmax_list([1,2,9,4,5,65,7,8]))

def square_root(numbers):
    result = [number ** 2 for number in numbers]
    return result

print(square_root([1, 2, 3, 4, 5, 6, 7, 8]))

is_palindrome = lambda string: string[::-1] == string

print(is_palindrome("karthick"))
print(is_palindrome("madam"))


String_multi = '''This is a multiline text 
which is used to esnd text or add text in multiple lines
SO you dont need to have multiple lines'''

print(String)