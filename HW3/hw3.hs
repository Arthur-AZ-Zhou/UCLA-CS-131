scale_nums lst n =
    map (\x -> x * n) lst

only_odds :: [[Integer]] -> [[Integer]]
only_odds = filter (all odd)

largest :: String -> String -> String
largest first second =
    if length first >= length second then first else second

largest_in_list :: [String] -> String
largest_in_list lst = foldl largest "" lst

count_if :: (a -> Bool) -> [a] -> Integer
count_if predicate_func [] = 0
count_if predicate_func (x:xs) 
    | (predicate_func x) = 1 + (count_if predicate_func xs)
    | otherwise = count_if predicate_func xs

count_if_with_filter :: (a -> Bool) -> [a] -> Int
count_if_with_filter predicate_func lst = length (filter predicate_func lst)

count_if_with_fold :: (a -> Bool) -> [a] -> Int
count_if_with_fold predicate_func = foldl (\accum x -> if predicate_func x then accum + 1 else accum) 0

foo :: Integer -> Integer -> Integer -> (Integer -> a) -> [a]
foo = \x -> \y -> \z -> \t -> map t [x, x+z..y]

data InstagramUser = Influencer [String] [InstagramUser] | Normie deriving (Eq)

lit_collab :: InstagramUser -> InstagramUser -> Bool
lit_collab user1 user2 = (user1 == Influencer [] []) && (user2 == Influencer [] [])

is_sponsor :: InstagramUser -> String -> Bool
is_sponsor (Influencer sponsors []) sponsor = sponsor `elem` sponsors
is_sponsor Normie _ = False

count_influencers :: InstagramUser -> Integer
count_influencers (Influencer _ followers) = fromIntegral $ length (filter isInfluencer followers)
    where
        isInfluencer :: InstagramUser -> Bool
        isInfluencer (Influencer _ _) = True
        isInfluencer Normie = False
count_influencers Normie = 0




data LinkedList = EmptyList | ListNode Integer LinkedList deriving Show

ll_contains :: LinkedList -> Integer -> Bool
ll_contains EmptyList _ = False  
ll_contains (ListNode value rest) target
    | value == target = True     
    | otherwise = ll_contains rest target  

ll_insert :: LinkedList -> Integer -> Integer -> LinkedList
ll_insert lst value index
    | index <= 0 = ListNode value lst 
    | otherwise = insertAt lst value index 

insertAt :: LinkedList -> Integer -> Integer -> LinkedList
insertAt EmptyList value _ = ListNode value EmptyList 
insertAt (ListNode v rest) value 1 = ListNode value (ListNode v rest) 
insertAt (ListNode v rest) value index = ListNode v (insertAt rest value (index - 1)) 
