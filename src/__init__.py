import json
import time
import random
import hashlib
def get_config(key):
    config_file = "/home/Mystery700/support/support_ticket/src/config.json" # always use absolute path, not relative path
    file = open(config_file, "r")
    config = json.loads(file.read())
    file.close()
    
    if key in config:
        return config[key]
    else:
        raise Exception("Key {} is not found in config.json".format(key))

def generate_ticket_id():
    # Get the current time in milliseconds
    current_time = int(time.time() * 1000)

    # Generate a random number
    random_number = random.randint(0, 99999)
    # Combine time and random number to form a unique ID string
    unique_string = f"{current_time}-{random_number}"

    # Use a more secure hash function for a more compact ID
    ticket_id = hashlib.sha256(unique_string.encode()).hexdigest()

    return ticket_id

def truncate(text, max_length):
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def generate_employee_id(prefix="EMP-", length=4):
    # Generate a random number with the specified length
    number = random.randint(10**(length-1), (10**length)-1)
    return f"{prefix}{number}"
