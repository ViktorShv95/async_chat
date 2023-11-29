import asyncio
import logging
import aiofiles
from datetime import datetime


async def read_chat():
    reader, writer = None, None

    while True:
        try:
            reader, writer = await asyncio.open_connection("minechat.dvmn.org", 5000)
            try:
                connection_time = datetime.now().strftime("%d.%m.%y %H:%M")
                logging.info(f"[{connection_time}] connected to minechat.dvmn.org:5000")
                while not reader.at_eof():
                    time = connection_time = datetime.now().strftime("%d.%m.%y %H:%M")
                    message = await reader.readline()
                    message = f"[{time}] {message.decode()}"
                    print(message)
                    await write_log_file(message)
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            logging.warning("Exception occurred: %s. Recconect in 5 seconds", exc)
            await asyncio.sleep(5)


async def write_log_file(message: str):
    async with aiofiles.open("log.txt", "a") as f:
        await f.write(message)
        await f.flush()


if __name__ == "__main__":
    asyncio.run(read_chat())
