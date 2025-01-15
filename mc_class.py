import discord
import socketio
import os
from discord.ext import commands, tasks
from math_stuff import *
from aes import AES
from dotenv import load_dotenv
from shared_memory_dict import SharedMemoryDict


def get_bot(prefix: str, channel_id: int):
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix=prefix, intents=intents)
    bot.add_cog(multiCom(bot, channel_id, bot.command_prefix))
    return bot


class multiCom(commands.Cog):
    prefix = ''
    prefix_temp = ''
    connections = []
    # connection entry structure: (prefix: str, AES object: AES)
    key_part = 0
    master_key = 20
    receiving = 0
    s_in = ''
    external_sio = socketio.AsyncRedisManager('redis://', write_only=False, channel='flask-socketio')

    def __init__(self, bot: commands.Bot, channel_id: int, prefix: int):
        self.bot = bot
        self.prefix = prefix
        self.channel_id = channel_id
        self.n, self.d, self.e = generate_keys(1028)
        self.smd = SharedMemoryDict(name='msg_in', size=1024)
        self.main_task.start()

    def get_id_from_prefix(self, prefix: str):
        for i in range(len(self.connections)):
            if self.connections[i][0] == prefix:
                return i

    async def key_exchange_0(self, ctx, prefix_foreign: str):
        self.prefix_temp = prefix_foreign
        await ctx.send(f'{prefix_foreign}keyExchange1 {self.n} {self.e}')

    async def key_exchange_1(self, ctx, n_2: int, e_2: int):
        self.key_part = generate_large_prime(128)
        await ctx.send(f'{self.prefix_temp}keyExchange2 {pow(self.key_part, e_2, n_2)} {self.n} {self.e}')

    async def key_exchange_2(self, ctx, key_part: int, n_2: int, e_2: int):
        self.key_part = pow(key_part, self.d, self.n)
        key_part_2 = generate_large_prime(128)
        self.master_key = self.key_part * key_part_2
        self.connections.append((self.prefix_temp, AES(self.master_key)))
        print(f'\nMaster Key: {self.master_key}\nPrefix: {self.prefix_temp}\n')
        await self.external_sio.emit('bot_connect', {'message': self.prefix_temp})
        await ctx.send(f'{self.prefix_temp}keyExchange3 {pow(key_part_2, e_2, n_2)}')

    async def key_exchange_3(self, ctx, key_part_2: int):
        self.master_key = self.key_part * pow(key_part_2, self.d, self.n)
        self.connections.append((self.prefix_temp, AES(self.master_key)))
        print(f'\nMaster Key: {self.master_key}\nPrefix: {self.prefix_temp}\n')
        await self.external_sio.emit('bot_connect', {'message': self.prefix_temp})
        await ctx.send('Connection succeed, messages can be transmitted')

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'\n{self.bot.user.name} {self.bot.command_prefix} has connected to Discord! \n \n')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message sender is a bot and if the message starts with the command
        if message.author.bot and message.content.startswith(self.bot.command_prefix + 'keyExchange0'):
            await self.key_exchange_0(message.channel, str(message.content).split(' ')[1])
        if message.author.bot and message.content.startswith(self.bot.command_prefix + 'keyExchange1'):
            await self.key_exchange_1(
                message.channel,
                int(str(message.content).split(' ')[1]),
                int(str(message.content).split(' ')[2])
            )
        if message.author.bot and message.content.startswith(self.bot.command_prefix + 'keyExchange2'):
            await self.key_exchange_2(
                message.channel,
                int(str(message.content).split(' ')[1]),
                int(str(message.content).split(' ')[2]),
                int(str(message.content).split(' ')[3])
            )
        if message.author.bot and message.content.startswith(self.bot.command_prefix + 'keyExchange3'):
            await self.key_exchange_3(
                message.channel,
                int(str(message.content).split(' ')[1])
            )
        if message.author.bot and message.content.startswith(self.bot.command_prefix + 'getMessage'):
            if self.receiving > 0:
                self.s_in += str(message.content).split(' ')[1]
                self.receiving -= 1
                if self.receiving <= 0:
                    await self.get_message(
                        message.channel,
                        self.s_in.split(' ')[0],
                        self.s_in.split(' ')[1]
                    )
                    self.receiving = 0
            else:
                self.receiving = int(message.content.split(' ')[1])
                self.s_in = message.content.split(' ')[2] + ' '

    async def connect(self, prefix_foreign: str):
        self.prefix_temp = prefix_foreign
        await self.bot.get_channel(self.channel_id).send(f'{prefix_foreign}keyExchange0 {self.bot.command_prefix}')

    async def send_message(self, prefix_foreign: str, s: str):
        channel = self.bot.get_channel(self.channel_id)
        temp_list = []
        enc_id = self.get_id_from_prefix(prefix_foreign)
        if isinstance(enc_id, int):
            for char in s:
                temp_list.append(str(self.connections[enc_id][1].encrypt(ord(char))))
            s = ','.join(temp_list)
            temp_list = []
            for i in range(len(s) // 1800 + 1):
                if (len(s) - (i * 1800)) < 1800:
                    temp_list.append(len(s) - (i * 1800))
                else:
                    temp_list.append(1800)
            await channel.send(f'{prefix_foreign}getMessage {len(temp_list)} {self.bot.command_prefix}')
            start = 0
            for size in temp_list:
                await channel.send(f'{prefix_foreign}getMessage {s[start: start + size]}')
                start += size

    async def get_message(self, ctx, prefix: str, s: str):
        temp_list = s.split(',')
        out = f'{prefix} '
        for char in temp_list:
            out += chr(self.connections[self.get_id_from_prefix(prefix)][1].decrypt(int(char)))
        await self.external_sio.emit('decrypt_in', {'message': out})

    @tasks.loop(seconds=1)
    async def main_task(self):
        # message inc check
        if 'message' in self.smd and self.smd['message'][0]:
            await self.send_message(self.smd['message'][1], self.smd['message'][2])
            self.smd['message'] = (False, '', '')

        # connect check
        if 'connect' in self.smd and self.smd['connect'][0]:
            await self.connect(str(self.smd['connect'][1]))
            self.smd['connect'] = (False, '')

        # ping sender
        await self.external_sio.emit('ping', {'message': str(round(self.bot.latency * 1000, 1)) + ' ms'})
        await self.external_sio.emit('bot_prefix', {'message': self.prefix})


if __name__ == '__main__':
    load_dotenv()
    bot = get_bot('a!', int(os.getenv('CHANNEL_ID')))
    bot.run(os.getenv('DISCORD_TOKEN'))
