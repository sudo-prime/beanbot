import discord
import json
import re

responses = {
    'nouser': 'The specified user is not a user on this server.',
    'notbot': 'Only bots can use this command.',
    'hacker': 'Nice try.',
    'posamt': 'Please specify a positive amount.',
    '!transfer': {
        'usage': 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`',
        'nofunds': 'You do not have enough beans to complete the transaction.',
        'success': 'Transaction completed successfully. You now have {} beans in your account. {}'
    },
    '!reward': {
        'usage': '2,bad_args'
    },
    '!request': {
        'usage': '2,bad_args'
    }
}

class InvalidCommandException(Exception):
    def __init__(self, value, loc=''):
        self.value = value
        self.loc = loc
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
    def __init__(self, message, types, loc=''):
        self.sender = message.author
        location = message.channel if loc == '' else loc

        # Parse the message for tokens.
        tokens = message.content.split(' ')

        # Baseline acceptance criteria
        if len(types) > len(tokens)-1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException(responses[tokens[0]]['usage'], location)
        
        # Parse into arguments.
        self.args = []
        for index in range(0, len(types)):
            try:
                self.args.append(types[index](tokens[index+1]))
            except:
                raise InvalidCommandException(responses[tokens[0]]['usage'], location)

async def send(location, message):
    global client
    await client.send_message(location, message)

async def verifyValidUser(mention):
    global client
    try:
        await client.get_user_info(usrid(mention))
        return True
    except:
        return False

def usrid(mention):
    userID = re.sub('<|>|@|!', '', str(mention))
    return userID

with open('../TOKEN') as tokenFile:
    TOKEN = tokenFile.readline()

client = discord.Client()
hackAttempt = False

@client.event
async def on_message(message):
    global hackAttempt
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
        except InvalidCommandException as e:
            # This command literally cannot be invalid
            print(e.value, 'This shouldn\'t have errored!')
            pass
    
    if message.content.startswith('!transfer'):
        try:
            command = Command(message, [int, usrid])
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            ledger.addNewUser(command.sender.id)
            if amount > ledger.data[sender.id]['balance']: raise InvalidCommandException(responses['!transfer']['nofunds'])
            if amount <= 0: raise InvalidCommandException(responses['posamt'])
            if not await verifyValidUser(recipient): raise InvalidCommandException(responses['nouser'])
            ledger.addNewUser(recipient)
            ledger.data[sender.id]['balance'] -= amount
            ledger.data[recipient]['balance'] += amount
            await send(message.channel, responses['!transfer']['success'].format(
                ledger.data[sender.id]['balance'], 
                '(Hey, thanks!)' if recipient == '512696929973698582' else ''))
        except InvalidCommandException as e:
            await send(message.channel, e.value)
    
    if message.content.startswith('!top'):
        try:
            beans = [(await client.get_user_info(key), ledger.data[key]['balance']) for key in ledger.data]
            top = sorted(beans, key=lambda tup: tup[1], reverse=True)
            msg = 'Here\'s the leaderboard:```'
            for i in range(0, 5):
                if i < len(top):
                    user = top[i]
                    msg += '\n{}. {}: {} beans'.format(i+1, user[0].name, user[1])
            msg += '```'
            await send(message.channel, msg)
        except InvalidCommandException as e:
            print(e.value, 'This shouldn\'t have errored!')
            pass
        
    if message.content.startswith('!reward'):
        try:
            botsChannel = message.server.get_channel('514095418481704972')
            if not message.author.bot: raise InvalidCommandException(responses['notbot'], message.channel)
            command = Command(message, [int, usrid], botsChannel)
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            if hackAttempt: raise InvalidCommandException(responses['hacker'], message.channel)
            if amount <= 0: raise InvalidCommandException('2,pos_amt', botsChannel)
            if not await verifyValidUser(recipient): raise InvalidCommandException('1,no_user', botsChannel)
            ledger.addNewUser(recipient)
            ledger.data[recipient]['balance'] += amount
            await send(botsChannel, '0,ok')
        except InvalidCommandException as e:
            await send(e.loc, e.value)
        
    if message.content.startswith('!request'):
        try:
            botsChannel = message.server.get_channel('514095418481704972')
            if not message.author.bot: raise InvalidCommandException(responses['notbot'], message.channel)
            command = Command(message, [int, usrid], botsChannel)
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            if hackAttempt: raise InvalidCommandException(responses['hacker'], message.channel)
            if amount <= 0: raise InvalidCommandException('2,pos_amt', botsChannel)
            if not await verifyValidUser(recipient): raise InvalidCommandException('1,no_user', botsChannel)
            ledger.addNewUser(recipient)
            if ledger.data[recipient]['balance'] < amount: raise InvalidCommandException('1,no_funds', botsChannel)
            ledger.data[recipient]['balance'] -= amount
            await send(botsChannel, '0,ok')
        except InvalidCommandException as e:
            await send(e.loc, e.value)
    
    if message.content.startswith('!spam.hack'):
        hackAttempt = True
    else:
        hackAttempt = False

    ledger.write()

@client.event
async def on_ready():
    print('Logged in!')

client.run(TOKEN)