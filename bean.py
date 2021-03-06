import discord
import json
import re, math
from datetime import datetime
from datetime import timedelta
from time import sleep

responses = {
    'sprout': '**{}**, you harvest {} beans. Your balance is now {} beans.',
    'notime': '**{}**, you still have {} hours and {} minutes before your next harvest is ready.',
    'nouser': '**{}**, the specified user is not a user on this server.',
    'notbot': '**{}**, only bots can use this command.',
    'hacker': 'Nice try.',
    'posamt': '**{}**, please specify a positive amount.',
    'balance':'**{}**, your balance is {} beans.',
    '!transfer': {
        'usage': '**{}**, please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`',
        'nofunds': '**{}**, you do not have enough beans to complete the transaction.',
        'success': '**{}**, the transaction was completed successfully. \nYou now have {} beans in your account. {}'
    },
    '!reward': {
        'usage': '2,bad_args,{}'
    },
    '!request': {
        'usage': '2,bad_args,{}'
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
            for user in self.data:
                self.data[user]['lsprout'] = datetime.strptime(
                    self.data[user]['lsprout'],
                    '%Y-%m-%d %H:%M:%S.%f')
    
    def write(self):
        with open('ledger.json', 'w') as outFile:
            json.dump(self.data, outFile, default=str)
    
    def addNewUser(self, user):
        if not user in self.data:
            self.data[user] = {
                'balance': 100,
                'lsprout': datetime(1970, 1, 1, 0, 0, 10, 10)
            }

class Command:
    def __init__(self, message, types, usage='', loc=''):
        commands = ['!balance', '!transfer', '!top', '$b', '$t', 
                    '!reward', '!request', '!sprout']

        self.sender = message.author
        location = message.channel if loc == '' else loc

        # Parse the message for tokens.
        tokens = message.content.split(' ')

        if tokens[0] not in commands:
            raise InvalidCommandException(None, location)

        # Baseline acceptance criteria
        if len(types) > len(tokens) - 1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException(usage, location)
        
        # Parse into arguments.
        self.args = []
        for index in range(0, len(types)):
            try:
                self.args.append(types[index](tokens[index+1]))
            except:
                raise InvalidCommandException(usage, location)

async def send(location, message):
    global client
    await client.send_message(location, message)

async def sendRich(location, message, color=0x22dd22):
    global client
    embed = discord.Embed(title="", description=message, color=color)
    await client.send_message(location, embed=embed)

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

    # Open the ledger for reading and modification.
    ledger = Ledger()

    if message.content.startswith('!balance') or message.content.startswith('$b'):
        try:
            # Command !balance takes no vaildation criteria,
            # and has no anticipated types.
            command = Command(message, [])
            sender = command.sender
            ledger.addNewUser(sender.id)
            balance = ledger.data[sender.id]['balance']
            await sendRich(
                message.channel, 
                responses['balance'].format(sender.name, balance))
        except InvalidCommandException as e:
            # This command literally cannot be invalid.
            pass
    
    if message.content.startswith('!transfer'):
        try:
            # Anticipate !transfer <int> <user mention>
            command = Command(message, [int, usrid], responses['!transfer']['usage'])
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            ledger.addNewUser(command.sender.id)
            if amount > ledger.data[sender.id]['balance']:
                raise InvalidCommandException(responses['!transfer']['nofunds'].format(sender.name))
            if amount <= 0:
                raise InvalidCommandException(responses['posamt'].format(sender.name))
            if not await verifyValidUser(recipient):
                raise InvalidCommandException(responses['nouser'].format(sender.name))
            ledger.addNewUser(recipient)
            ledger.data[sender.id]['balance'] -= amount
            ledger.data[recipient]['balance'] += amount
            await sendRich(message.channel, responses['!transfer']['success'].format(
                sender.name,
                ledger.data[sender.id]['balance'], 
                '(Hey, thanks!)' if recipient == '512696929973698582' else ''))
        except InvalidCommandException as e:
            if not e.value == None: await sendRich(message.channel, e.value, 0xdd2222)
    
    if message.content.startswith('!top') or message.content.startswith('$t'):
        try:
            command = Command(message, [])
            beans = []
            for key in ledger.data:
                user = await client.get_user_info(key)
                beans.append((user, ledger.data[key]['balance']))
            top = sorted(beans, key=lambda tup: tup[1], reverse=True)
            msg = ''
            for i in range(0, 5):
                if i < len(top):
                    temp = '\n{}: {}:{} beans'.format(i+1, top[i][0].name, top[i][1])
                    spaces = ' ' * (max(1, (31 - (len(temp)))))
                    msg += '\n`{}. {}:'.format(i+1, top[i][0].name)
                    msg += spaces
                    msg += '{} beans`'.format(top[i][1])
            await sendRich(message.channel, msg)
        except InvalidCommandException as e:
            pass
        
    if message.content.startswith('!reward'):
        try:
            botsChannel = message.server.get_channel('514095418481704972')
            if not message.author.bot:
                raise InvalidCommandException(
                    responses['notbot'].format(sender.name),
                    message.channel)
            command = Command(message, [int, usrid], responses['!reward']['usage'], botsChannel)
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            if hackAttempt:
                raise InvalidCommandException(responses['hacker'], message.channel)
            if amount <= 0:
                raise InvalidCommandException('2,pos_amt', botsChannel)
            if not await verifyValidUser(recipient):
                raise InvalidCommandException('1,no_user', botsChannel)
            ledger.addNewUser(recipient)
            ledger.data[recipient]['balance'] += amount
            await send(botsChannel, '0,ok')
        except InvalidCommandException as e:
            if not e.value == None:
                if e.loc == message.channel: await sendRich(e.loc, e.value, 0xdd2222)
                else: await send(e.loc, e.value)
        
    if message.content.startswith('!request'):
        try:
            botsChannel = message.server.get_channel('514095418481704972')
            if not message.author.bot:
                raise InvalidCommandException(
                    responses['notbot'].format(sender.name),
                    message.channel)
            command = Command(message, [int, usrid], responses['!request']['usage'], botsChannel)
            sender = command.sender
            recipient = command.args[1]
            amount = command.args[0]
            if hackAttempt:
                raise InvalidCommandException(responses['hacker'], message.channel)
            if amount <= 0:
                raise InvalidCommandException('2,pos_amt', botsChannel)
            if not await verifyValidUser(recipient):
                raise InvalidCommandException('1,no_user', botsChannel)
            ledger.addNewUser(recipient)
            if ledger.data[recipient]['balance'] < amount:
                raise InvalidCommandException('1,no_funds', botsChannel)
            ledger.data[recipient]['balance'] -= amount
            await send(botsChannel, '0,ok')
        except InvalidCommandException as e:
            if not e.value == None:
                if e.loc == message.channel: await sendRich(e.loc, e.value, 0xdd2222)
                else: await send(e.loc, e.value)
    
    if message.content.startswith('!sprout'):
        try:
            # Command !balance takes no vaildation criteria,
            # and has no anticipated types.
            command = Command(message, [])
            sender = command.sender
            ledger.addNewUser(sender.id)
            balance = ledger.data[sender.id]['balance']
            lastSprout = ledger.data[sender.id]['lsprout']
            delta = datetime.now() - lastSprout
            if delta < timedelta(days=1):
                raise InvalidCommandException(responses['notime'].format(sender.name, 
                    int((timedelta(days=1).total_seconds() - delta.total_seconds()) // 3600),
                    int(((timedelta(days=1).total_seconds() - delta.total_seconds()) % 3600) // 60)))
            # User can sprout
            ledger.data[sender.id]['lsprout'] = datetime.now()
            newBeans = math.floor(((2 * balance) + 10) ** 0.75)
            ledger.data[sender.id]['balance'] += newBeans
            await sendRich(message.channel, responses['sprout'].format(sender.name, newBeans, ledger.data[sender.id]['balance']))
        except InvalidCommandException as e:
            if not e.value == None: await sendRich(message.channel, e.value, 0xdd2222)

    hackAttempt = message.content.startswith('!spam.hack')

    ledger.write()

@client.event
async def on_ready():
    print('Logged in!')

client.run(TOKEN)
