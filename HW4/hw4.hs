import Data.List (group)

longest_run :: [Bool] -> Int
longest_run xs = maximum (0 : map length (filter (all (== True)) (group xs)))

data Tree = Empty | Node Integer [Tree]

max_tree_value :: Tree -> Integer
max_tree_value Empty = 0
max_tree_value (Node value subtrees) = maximum (value : map max_tree_value subtrees)

sumSquares :: Integer -> Integer
sumSquares n = helper n 0
    where
    helper 0 acc = acc
    helper n acc = helper (n - 1) (acc + n ^ 2)