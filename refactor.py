import discord
import json
import re


class InvalidCommandException(Exception):
    pass

class Ledger:
    def __init__(self):
        with open('ledger.json', 'r') as inFile:
            self.data = json.load(inFile)
    
    def write(self):
        with open('ledger.json', 'w') as outFile:
            json.dump(self.data, outFile)
    
    def addNewUser(self, user):
        if not user in self.data:
            self.data[user] = {'balance': 100}

class Command:
    def __init__(self, message, types):
        self.sender = message.author

        # Parse the message for tokens.
        tokens = message.content.split(' ')

        # Baseline acceptance criteria
        if len(validationCriteria) > len(tokens)-1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException
        
        # Use case acceptance criteria.
        for index in range(len(types)):
            for criteria in validationCriteria[index]:
                try:
                    if not criteria(tokens[index+1]):
                        raise InvalidCommandException
                except Exception:
                    raise InvalidCommandException
        
        # Types are verified, now parse and store tokens.
        self.arguments = []
        for index in range(len(types)):
            if types[index] != None:
                self.arguments.append(types[index+1](tokens[index]))
            else:
                self.arguments.append(tokens[index+1])

async def send(location, message):
    global client
    await client.send_message(location, message)

with open('../TOKEN') as tokenFile:
    TOKEN = tokenFile.readline()

client = discord.Client()

@client.event
async def on_message(message):
    # Ignore messages sent by beanbot.
    if message.author == client.user:
        return
    print(str(message.content))

    # Open the ledger for reading and modification.
    ledger = Ledger()

    if message.content.startswith('!balance'):
        try:
            # Command !balance takes no vaildation criteria,
            # and has no anticipated types.
            command = Command(message, [], [])
            ledger.addNewUser(command.sender.id)
            balance = ledger.data[command.sender.id]['balance'])
            send(message.channel, 'Your balance is {} beans.'.format(balance))
        except InvalidCommandException:
            # This command literally cannot be invalid
            pass
    
    if message.content.startswith('!transfer'):
        try:
            validationCriteria = []
            validationCriteria.append([int, ])
            command = Command(message, validationCriteria, [])

@client.event
async def on_ready():
    print('Logged in!')

client.run(TOKEN)