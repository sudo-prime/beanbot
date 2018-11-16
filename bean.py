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
    print(str(message.content))
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
        if sender.id not in ledger:
            ledger[sender.id] = {'balance': 0}
            msg = 'Hello! I can tell this is the first time you\'ve used BeanBot to manage your beans. I\'ve set up an account for you. You may now trade and participate in bean-related activities. \n\nBeanBot says, ```\"Stay in school, and have fun!\"```'
            await client.send_message(message.channel, msg)
        tokens = message.content.split(' ')
        if len(tokens) >= 3:
            if await isValidInputOfType(tokens[1], message.channel, int, 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`'):
                amount = eval(tokens[1])
                if amount <= ledger[sender.id]['balance']: 
                    if amount > 0:
                        recipient = tokens[2]
                        if recipient[2:-1] in ledger:
                            ledger[sender.id]['balance'] -= amount
                            ledger[recipient[2:-1]]['balance'] += amount
                            msg = 'Transaction completed successfully. You now have {} beans in your account.'.format(ledger[sender.id]['balance'])
                            if recipient[2:-1] == '512696929973698582': msg += ' (Hey, thanks!)'
                            await client.send_message(message.channel, msg)
                        else:
                            msg = 'The specified user is not on the ledger. They either do not exist, or have not initialized their account with `!balance`.'
                            await client.send_message(message.channel, msg)
                    else:
                        msg = 'Please specify a positive transfer amount.'
                        await client.send_message(message.channel, msg)
                else:
                    msg = 'You do not have enough beans to complete the transaction.'
                    await client.send_message(message.channel, msg)
        else:
            msg = 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`'
            await client.send_message(message.channel, msg)

    if message.content.startswith('!award'):
        sender = message.author
        tokens = message.content.split(' ')
        if sender.bot:
            if len(tokens) >= 3:
                if await isValidInputOfType(tokens[1], message.channel, int, 'Please enter an amount followed by a mention to the recipient.\nex. `!transfer <amount> <mention>`'):
                    amount = eval(tokens[1])
                    recipient = tokens[2]
                    if recipient[2:-1] in ledger:
                        ledger[recipient[2:-1]]['balance'] += amount
                        ledger[recipient[2:-1]]['balance'] = max(0, ledger[recipient[2:-1]]['balance'])
                        msg = '{} beans awarded.'.format(amount)
                        await client.send_message(message.channel, msg)
                    else:
                        msg = 'The specified user is not on the ledger. They either do not exist, or have not initialized their account with `!balance`.'
                        await client.send_message(message.channel, msg)
            else:
                msg = 'Please enter an amount followed by a mention to the recipient.\nex. `!award <amount> <mention>`'
                await client.send_message(message.channel, msg)
        else:
            msg = 'You\'re not a bot!'
            await client.send_message(message.channel, msg)
    
    if message.content.startswith('!top'):
        beans = [(await client.get_user_info(key), ledger[key]['balance']) for key in ledger]
        top = sorted(beans, key=lambda tup: tup[1], reverse=True)
        msg = 'Here\'s the leaderboard:'
        for i in range(0, 5):
            if i < len(top):
                user = top[i]
                msg += '\n{}. {}: {} beans'.format(i+1, user[0].name, user[1])
        await client.send_message(message.channel, msg)

    # Write the JSON file, with changes
    with open('ledger.json', 'w') as outFile:
        json.dump(ledger, outFile)

async def isValidInputOfType(userInput, channel, validType, errorMsg):
    try:
        evaluated = eval(userInput)
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