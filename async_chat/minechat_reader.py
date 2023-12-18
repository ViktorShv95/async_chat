import asyncio
import logging
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import aiofiles
from environs import Env, EnvError


async def read_chat(host: str, port: int, history_file: Path):
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            logging.info(f'Connected to {host}:{port}')
            try:
                while not reader.at_eof():
                    time = datetime.now().strftime('%d.%m.%y %H:%M')
                    message = await reader.readline()
                    message = f'[{time}] {message.decode()}'
                    print(message)
                    await write_history_file(history_file, message)
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            logging.warning('Exception occurred: %s. Recconect in 5 seconds', exc)
            await asyncio.sleep(5)


async def write_history_file(history_file: Path, message: str):
    async with aiofiles.open(history_file, 'a') as f:
        await f.write(message)
        await f.flush()


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
        default=5000,
        help='Порт чат-сервера',
    )
    parser.add_argument(
        '--history',
        type=Path,
        default=Path('minechat.history'),
        help='Путь к файлу с историей чата',
    )
    args = parser.parse_args()

    env = Env()
    env.read_env()
    host = args.host
    port = args.port
    history = args.history

    logging.info(f'Connecting... to {host}:{port}')

    asyncio.run(read_chat(host, port, history))


if __name__ == "__main__":
    main()
