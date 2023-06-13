import auth
from getpass import getpass

auth = auth.Auth()

username = input('Username: ')
while True:
    password = getpass()
    password2 = getpass('Confirm: ')

    if password == password2:
        auth.create_user(username, password)
        break
    else:
        print('Passwords do not match')