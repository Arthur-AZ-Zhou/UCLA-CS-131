greeting = "Hello, world!"

largest :: String -> String -> String
largest string1 string2
    | length string1 >= length string2 = string1
    | otherwise = string2

reflect :: Integer -> Integer
reflect 0 = 0
reflect num
    | num < 0 = (-1) + reflect (num + 1)
    | num > 0 = 1 + reflect (num - 1)
    | otherwise = 0

is_even :: Integer -> Bool
is_even 0 = True
is_even 1 = False
is_even num = is_even (num - 2)

is_odd :: Integer -> Bool
is_odd 0 = False
is_odd 1 = True
is_odd num = is_odd (num - 2)