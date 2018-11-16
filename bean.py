import discord
import json
from pprint import pprint

with open('../TOKEN') as tokenFile:
    TOKEN = tokenFile.readline()

client = discord.Client()

@client.event
async def on_message(message):
    # Ignore messages sent by beanbot
    if message.author == client.user:
        return
    
    # Open the ledger for reading and modification
    with open('ledger.json', 'r') as inFile:
        ledger = json.load(inFile)

    if message.content.startswith('!balance'):
        sender = message.author
        if sender.id not in ledger:
            ledger[sender.id] = {'balance': 0}
            msg = 'Hello! I can tell this is the first time you\'ve used BeanBot to manage your beans. I\'ve set up an account for you. You may now trade and participate in bean-related activities. \n\nBeanBot says, ```\"Stay in school, and have fun!\"```'
            await client.send_message(message.channel, msg)
        beans = ledger[sender.id]['balance']
        msg = 'You have {} beans in your account.'.format(beans)
        await client.send_message(message.channel, msg)
    
    if message.content.startswith('!transfer'):
        sender = message.author
        # Return if the sender's not on the ledger, and display welcome message
        if sender.id not in ledger:
            ledger[sender.id] = {'balance': 0}
            msg = 'Hello! I can tell this is the first time you\'ve used BeanBot to manage your beans. I\'ve set up an account for you. You may now trade and participate in bean-related activities. \n\nBeanBot says, ```\"Stay in school, and have fun!\"```'
            await client.send_message(message.channel, msg)
        tokens = message.content.split(' ')
        # If the user specifies to few tokens, return
        if len(tokens) < 3:
            msg = 'Please enter an amount followed by a mention to the recipient.\nex. !transfer <amount> <mention>'
            await client.send_message(message.channel, msg)
            return
        # If the user specified a non-integer value for amount, return
        if not await isValidInputOfType(tokens[1], message.channel, int, 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`'): return
        amount = eval(tokens[1])
        # If the user doesn't have enough beans to complete the transaction, return
        if amount > ledger[sender.id]['balance']:
            msg = 'You do not have enough beans to complete the transaction.'
            await client.send_message(message.channel, msg)
            return
        recipient = tokens[2]
        # If the recipient isn't on the ledger, return
        if recipient[2:-1] not in ledger:
            msg = 'The specified user is not on the ledger. They either do not exist, or have not initialized their account with `!balance`.'
            await client.send_message(message.channel, msg)
            return
        # Finally, complete the transaction
        ledger[sender.id]['balance'] -= amount
        ledger[recipient[2:-1]]['balance'] += amount
        msg = 'Transaction completed successfully. You now have {} beans in your account.'.format(ledger[sender.id]['balance'])
        await client.send_message(message.channel, msg)

    # Write the JSON file, with changes
    with open('ledger.json', 'w') as outFile:
        json.dump(ledger, outFile)

async def isValidInputOfType(userInput, channel, validType, errorMsg):
    try:
        evaluated = eval(userInput)
        print(evaluated, isinstance(evaluated, validType))
        if not isinstance(evaluated, validType):
            msg = 'Invalid input. {}'.format(errorMsg)
            await client.send_message(channel, msg)
            return False
    except Exception as e:
        print(e)
        msg = 'Invalid input. {}'.format(errorMsg)
        await client.send_message(channel, msg)
        return False
    return True

async def verifyUserIsOnLedger(user, channel, ledger):
    if user.id not in ledger:
        ledger[user.id] = {'balance': 0}
        msg = 'Hello, {0.mention}. I can tell this is the first time you\'ve used BeanBot to manage your beans. I\'ve set up an account for you. You may now trade and participate in bean-related activities. \n\nBeanBot says, ```\"Stay in school, and have fun!\"```'.format(user)
        await client.send_message(channel, msg)
        return False
    return True

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)