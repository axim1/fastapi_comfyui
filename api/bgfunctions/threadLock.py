import threading

# creating a threadlock to count the number of tasks accessing resources
thread_lock = threading.Lock()
# count of number of tasks running
global_counter = 0
