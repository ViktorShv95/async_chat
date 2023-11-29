

import asyncio
import json
import logging
import uuid
from argparse import ArgumentParser

import aiofiles
from environs import Env, EnvError


async def register(host, port, username, message):
    reader, writer = await asyncio.open_connection(host, port)

    try:
        signin_message = (await reader.readline()).decode().strip()
        logging.info({signin_message})
        
        skip_auth_reply = '\n'
        writer.write(skip_auth_reply.encode())
        await writer.drain()

        logging.info(skip_auth_reply.strip())

        request_username_message = (await reader.readline()).decode().strip()
        logging.info(request_username_message)
        
        username_reply = f'{username}\n'
        writer.write(username_reply.encode())
        await writer.drain()

        logging.info(username_reply.strip())

        signup_result = json.loads((await reader.readline()).decode())
        token = signup_result['account_hash']
        logging.info(f'{signup_result["nickname"]} registed. Here is your token: {token}')

        async with aiofiles.open('minechat.token', 'w') as token_file:
            await token_file.write(token)
            logging.info('Token saved in minechat.token')


    finally:
        writer.close()
        await writer.wait_closed()

        if signup_result:
            await authorise(host, port, token, message)


async def authorise(host, port, token, message):
    reader, writer = await asyncio.open_connection(host, port)
    logging.info(f'Connected to {host}:{port}')

    try:
        logging.info(await reader.readline())
        writer.write(f'{token}\n'.encode())
        await writer.drain()
        logging.info(f'Token {token} sent')
    
        auth_result = json.loads((await reader.readline()).decode())
        logging.info(auth_result)

        if not auth_result:
            writer.close()
            await writer.wait_closed()
            logging.error('Invalid token. Please check it or create a new one.')
            return
    
        logging.info(f'Logged in {host}:{port} as {auth_result["nickname"]}')
    
        await submit_message(writer, message)
    finally:
        writer.close()
        await writer.wait_closed()


async def submit_message(writer, message):
    if not message:
        message = '\n'
    else:
        message = message.replace('\n', '').strip()
        message = f'{message}\n\n'

    writer.write(message.encode())
    await writer.drain()
    logging.info(f'Sent message: {message.strip()}')


def main():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    parser = ArgumentParser()
    parser.add_argument(
        '--host',
        type=str,
        default='minechat.dvmn.org',
        help='Адрес чат-сервера',
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5050,
        help='Порт чат-сервера',
    )
    parser.add_argument(
        '--token',
        type=str,
        help='Токен для авторизации',
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Имя пользователя для регистрации',
    )
    parser.add_argument(
        '--message',
        type=str,
        required=True,
        help='Сообщение в чат',
    )
    
    args = parser.parse_args()

    env = Env()
    env.read_env()

    host = args.host
    if not host:
        try:
            host = env.str('HOST')
        except EnvError:
            logging.warning('Host is not set. Set HOST env variable or use --host argument')
            return
    
    port = args.port
    if not port:
        try:
            port = env.int('PORT_SEND_MESSAGE')
        except EnvError:
            logging.warning('Port is not set. Set PORT env variable or use --port argument')
            return
    
    token = ''
    if args.token:
        try:
            token = uuid.UUID(args.user)
        except ValueError:
            logging.warning('Token is not valid UUID')
    else:
        try:
            token = env.str('USER_TOKEN')
        except EnvError:
            logging.warning('Token is not set. Set USER_TOKEN env variable or use --token argument')

    username = args.username
    if not username:
        try:
            username = env.str('CHAT_USERNAME')
        except EnvError:
            logging.warning('Username is not set. Set CHAT_USERNAME env variable or use --username argument')

    if not token and not username:
        logging.warning('Token or username is not set. Use --token or --username arguments')
        return

    message = args.message

    if token:
        asyncio.run(authorise(host, port, token, message))
    else:
        asyncio.run(register(host, port, username, message))

if __name__ == '__main__':
    main()