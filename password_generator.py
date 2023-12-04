import string
import random
import os
import time
from colorama import Fore, Style
from pyfiglet import Figlet
from tqdm import tqdm
import winsound
import inquirer

def generate_password(length):
    try:
        characters = string.ascii_letters + string.digits + string.punctuation + "çâêîôûàèìòùëïüÿÇÂÊÎÔÛÀÈÌÒÙËÏÜŸ"
        password = "".join(random.choice(characters) for _ in range(length))
        return password
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_title():
    title = "Welcome to the Secure Password Generator!"
    for i in range(len(title)+1):
        clear_console()
        print(Fore.GREEN + title[:i] + Style.RESET_ALL + title[i:].lower())
        time.sleep(0.1)

def print_typewriter(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.1)
    print()

def print_password_strength(password):
    # Calculate the strength of the password (this is just a simple example)
    strength = len(password) / 24

    # Determine the color based on the strength
    if strength < 0.5:
        color = Fore.RED
    elif strength < 0.75:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN

    # Print the password strength as an ASCII art gauge
    print("Password strength: ", end="")
    for i in range(20):
        if i < strength * 20:
            print(color + "#" + Style.RESET_ALL, end="")
            time.sleep(0.1)  # Add a delay for the animated filling effect
        else:
            print(" ", end="")
    print()

def print_ascii_art(text, font):
    f = Figlet(font=font)
    print(f.renderText(text))

print_ascii_art("Welcome to the Secure Password Generator!", 'slant')
print(Fore.YELLOW + "========================================\n" + Style.RESET_ALL)
time.sleep(2)

while True:
    questions = [
        inquirer.List('level',
            message="Please choose the level of safety for your password:",
            choices=['1. 8 characters (Moderately Safe)', '2. 16 characters (Safer)', '3. 24 characters (God Level Safety)'],
        ),
    ]
    answers = inquirer.prompt(questions)

    # Extract the number from the answer and convert it to an integer
    level = int(answers['level'][0])
    length = level * 8
    break
else:
    print(Fore.RED + "\nInvalid choice. Please enter 1, 2, or 3.\n" + Style.RESET_ALL)
    time.sleep(2)
clear_console()

clear_console()
print("\nGenerating your password")
for i in tqdm(range(100)):
    time.sleep(0.02)

password = generate_password(length)
if password is not None:
    print_password_strength(password)
    print(Fore.GREEN + f"Your password has been successfully generated! Here it is:\n\n{password}\n" + Style.RESET_ALL)
    winsound.Beep(1000, 500)
    print_typewriter("Remember to keep your password safe and secure. Don't share it with anyone!")