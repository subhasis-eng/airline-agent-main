# task_queue.py
import asyncio
import traceback

TASK_QUEUE = asyncio.Queue()


async def task_worker():
    print("[task_worker] started")
    while True:
        agent_callable, payload = await TASK_QUEUE.get()
        try:
            res = await agent_callable(payload)
            print(f"[task_worker] {agent_callable.__name__} done: {res}")
        except Exception as e:
            print(f"[task_worker] error in {agent_callable}: {e}")
            traceback.print_exc()
        finally:
            await asyncio.sleep(0.01)
