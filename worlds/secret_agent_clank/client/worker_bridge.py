"""Async IPC to a serial game process; this module never opens PINE."""
import asyncio
import multiprocessing
import time

from .game_worker import GameRuntime, worker_main


class GameWorker:
    def __init__(self, on_event, *, runtime_factory=GameRuntime, timeout=180):
        self.on_event = on_event
        self.runtime_factory = runtime_factory
        self.timeout = timeout
        self.lock = asyncio.Lock()
        self.process = self.connection = None
        self.broken = False
        self.closed = False

    def _start(self):
        context = multiprocessing.get_context('spawn')
        self.connection, child = context.Pipe()
        self.process = context.Process(target=worker_main, args=(child, self.runtime_factory),
                                       name='SAC game worker', daemon=True)
        try:
            self.process.start()
        except Exception:
            self.process = None
            self.connection.close()
            raise
        finally:
            child.close()

    def _exchange(self, command, payload, loop):
        if self.process is None:
            self._start()
        self.connection.send((command, payload))
        deadline = time.monotonic() + self.timeout
        while True:
            if not self.connection.poll(0.1):
                if not self.process.is_alive():
                    raise ConnectionError('SAC game worker exited')
                if time.monotonic() >= deadline:
                    raise TimeoutError('SAC game worker stopped responding')
                continue
            message = self.connection.recv()
            if message[0] == 'event':
                loop.call_soon_threadsafe(self.on_event, *message[1:])
            elif message[0] == 'result':
                return message[1]
            else:
                raise RuntimeError(message[1])

    async def request(self, command, payload=None):
        async with self.lock:
            if self.closed or self.broken:
                raise ConnectionError('Game worker unavailable; restart the client (and game if loading is held)')
            operation = asyncio.create_task(asyncio.to_thread(
                self._exchange, command, payload, asyncio.get_running_loop()))
            try:
                # Cancellation must not release the lock while an exchange still
                # owns the pipe. Otherwise a later RPC could consume its reply.
                return await asyncio.shield(operation)
            except asyncio.CancelledError:
                try:
                    await operation
                except (EOFError, OSError, TimeoutError):
                    self.broken = True
                    await asyncio.to_thread(self._stop)
                except Exception:
                    pass
                raise
            except (EOFError, OSError, TimeoutError):
                self.broken = True
                await asyncio.to_thread(self._stop)
                raise

    def _stop(self):
        if self.process is not None:
            self.process.join(0.5)
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(5)
            if self.process.is_alive():
                self.process.kill()
                self.process.join()
        if self.connection is not None:
            self.connection.close()

    async def close(self):
        if self.closed:
            return
        graceful = self.process is None and not self.lock.locked()
        pending = None
        try:
            if not graceful and not self.broken:
                pending = asyncio.create_task(self.request('shutdown'))
                done, _ = await asyncio.wait({pending}, timeout=10)
                if done:
                    try:
                        pending.result()
                        graceful = True
                    except Exception:
                        graceful = False
        finally:
            self.closed = True
            await asyncio.to_thread(self._stop)
            if pending is not None:
                await asyncio.gather(pending, return_exceptions=True)
        return graceful
