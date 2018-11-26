import discord
import json
import re

responses = {
    "nouser": 'The specified user is not a user on this server.',
    "!transfer": {
        "usage": 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`',
        "nofunds": 'You do not have enough beans to complete the transaction.',
        "posamt": 'Please specify a positive transfer amount.',
        "success": 'Transaction completed successfully. You now have {} beans in your account. {}'
    }
}

class InvalidCommandException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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
        if len(types) > len(tokens)-1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException(responses[tokens[0]]['usage'])
        
        # Parse into arguments.
        self.args = []
        for index in range(1, len(types)):
            try:
                self.args.append(types[index](tokens[index]))
            except:
                raise InvalidCommandException(responses[tokens[0]]['usage'])

async def send(location, message):
    global client
    await client.send_message(location, message)

async def verifyValidUser(mention):
    global client
    userID = re.sub("<|>|@|!", "", mention)
    try:
        await client.get_user_info(userID)
        return True
    except discord.NotFound:
        return False

def usrid(mention):
    userID = re.sub("<|>|@|!", "", str(mention))
    return userID

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
            command = Command(message, [])
            ledger.addNewUser(command.sender.id)
            balance = ledger.data[command.sender.id]['balance']
            await send(message.channel, 'Your balance is {} beans.'.format(balance))
        except InvalidCommandException:
            # This command literally cannot be invalid
            pass
    
    if message.content.startswith('!transfer'):
        try:
            command = Command(message, [int, usrid])
            sender = command.sender.id
            recipient = command.args[1]
            amount = command.args[0]
            ledger.addNewUser(command.sender.id)
            if amount > ledger.data[sender]['balance']: raise InvalidCommandException(responses['!transfer']['nofunds'])
            if amount > 0: raise InvalidCommandException(responses['!transfer']['posamt'])
            if not await verifyValidUser(recipient): raise InvalidCommandException(responses['nouser'])
            ledger.addNewUser(recipient)
            ledger.data[sender]    -= amount
            ledger.data[recipient] += amount
            await send(message.channel, responses["success"].format(ledger.data[sender], "(Hey, thanks!)" if recipient == "512696929973698582" else ""))
        except InvalidCommandException as e:
            await send(message.channel, e.value)

@client.event
async def on_ready():
    print('Logged in!')

client.run(TOKEN)