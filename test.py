import copy

class Joker:
    joke = "I dressed as a UDP packet at the party. Nobody got it."

    def change_joke(self):
        print(f'self.joke = {self.joke}')
        print(f'Joker.joke = {Joker.joke}')
        Joker.joke = "How does an OOP coder get wealthy? Inheritance."
        self.joke = "Why do Java coders wear glasses? They can't C#."
        print(f'self.joke = {self.joke}')
        print(f'Joker.joke = {Joker.joke}')

def main():
    j = Joker()
    print(f'j.joke = {j.joke}')
    print(f'Joker.joke = {Joker.joke}')
    j.change_joke()
    print(f'j.joke = {j.joke}')
    print(f'Joker.joke = {Joker.joke}')

main()



def _generator(self):
        for head in self.array:
            current = head
            while current:
                yield current.value
                current = current.next

ht.iter = lambda: HashTableIterator(ht)
for item in ht:
    print(item)

class HashTableIterator:
def __init__(self, hash_table):
    self.array = hash_table.array
    self.bucket_index = 0
    self.current = None

def __iter__(self):
    return self

def __next__(self):
    # Find the next node in the hash table
    while self.current is None and self.bucket_index < len(self.array):
        self.current = self.array[self.bucket_index]
        self.bucket_index += 1
    if self.current is None:
        raise StopIteration
    value = self.current.value
    self.current = self.current.next
    return value

iterator = iter(ht) 
while True:
    try:
        item = next(iterator) 
        print(item)
    except StopIteration:
        break

# class Event:
#     def __init__(self, start_time, end_time):
#         if (end_time <= start_time):
#             raise ValueError
        
#         self.start_time = start_time
#         self.end_time = end_time

# class Calendar:
#     def __init__(self):
#         self.events = []

#     def get_events(self):
#         return self.events

#     def add_event(self, event):
#         if (isinstance(event, Event) == False):
#             raise TypeError
#         else:
#             self.events.append(event)

# class AdventCalendar(Calendar):
#     def __init__(self, year):
#         self.year = year
        
# def main():
#     event = Event(10, 20)
#     print(f"Start: {event.start_time}, End: {event.end_time}")

#     try:
#         invalid_event = Event(20, 10)
#         print("Success")
#     except ValueError:
#         print("Created an invalid event")

#     calendar = Calendar()
#     print(calendar.get_events())
#     calendar.add_event(Event(10, 20))
#     print(calendar.get_events()[0].start_time)

#     try:
#         calendar.add_event("not an event")
#     except TypeError:
#         print("Invalid event")

#     advent_calendar = AdventCalendar(2022)
#     print(advent_calendar.get_events())

# main()


# def largest_sum(nums, k):
#     if k < 0 or k > len(nums):
#         raise ValueError("k must be between 0 and the length of nums")
#     elif k == 0:
#         return 0
    
#     sum = 0
#     for num in nums[0 : k]:
#         sum += num

#     max_sum = sum
#     for i in range(0, len(nums) - k):
#         sum -= nums[i]
#         sum += nums[i + k]
#         max_sum = max(sum, max_sum)

#     return max_sum

# def main():
#     print(largest_sum([3,5,6,2,3,4,5], 3))
#     print(largest_sum([10,-8,2,6,-1,2], 4))

# main()




# class NotDuck:
#     def __init__(self):
#         pass

#     def quack(self):
#         print("quack")

# class Duck:
#     def __init__(self):
#         pass 

# class IsDuckNoQuack(Duck):
#     def __init__(self):
#         pass

# def is_duck_a(duck):
#     try:
#         duck.quack()
#         return True
#     except:
#         return False

# def is_duck_b(duck):
#     return isinstance(duck, Duck)

# def main():
#     duck_instance = NotDuck()  # Instance of the Quack class
#     duck_instance2 = IsDuckNoQuack();

#     print(is_duck_a(duck_instance))  # This should return True
#     print(is_duck_b(duck_instance))  # This should return False
#     print(is_duck_a(duck_instance2))  # This should return False
#     print(is_duck_b(duck_instance2))  # This should return True

# main()




# class Comedian:
#     def __init__(self, joke):
#         self.__joke = joke

#     def change_joke(self, joke):
#         self.__joke = joke

#     def get_joke(self):
#         return self.__joke
    
# def process(c):
#     c = copy.copy(c)
#     c[1] = Comedian("joke3")
#     c.append(Comedian("joke4"))
#     c = c + [Comedian("joke5")]
#     c[0].change_joke("joke6")

# def main():
#     c1 = Comedian("joke1")
#     c2 = Comedian("joke2")
#     com = [c1, c2]
#     process(com)
#     c1 = Comedian("joke7")

#     for c in com:
#         print(c.get_joke())

#     print("hello world")

# main()