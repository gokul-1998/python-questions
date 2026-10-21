"""
advanced/solutions/solutions.py
Executable reference implementations for Advanced Questions (Q16 - Q30).
Run directly via: python advanced/solutions/solutions.py
"""

from __future__ import annotations

import asyncio
import collections
import concurrent.futures
import contextlib
import queue
import random
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, TypeVar

# Import shared utilities from common_start.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common_start import logger, runtime_concurrency_info

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


# ============================================================================
# Q16: Deadlock Prevention via Global Lock Ordering Context Manager
# ============================================================================
@contextlib.contextmanager
def acquire_locks_in_order(*locks: threading.Lock) -> Iterator[None]:
    """Breaks Coffman's Circular Wait condition by sorting locks by memory address."""
    sorted_locks = sorted(set(locks), key=id)
    try:
        for lock in sorted_locks:
            lock.acquire()
        yield
    finally:
        for lock in reversed(sorted_locks):
            lock.release()


def q16_deadlock_free_transfer() -> tuple[int, int]:
    """Transfers funds in opposite directions concurrently without deadlocking."""
    acct_a = {"balance": 1000, "lock": threading.Lock()}
    acct_b = {"balance": 1000, "lock": threading.Lock()}

    def transfer(src: dict[str, Any], dst: dict[str, Any], amount: int) -> None:
        with acquire_locks_in_order(src["lock"], dst["lock"]):
            src["balance"] -= amount
            dst["balance"] += amount

    threads = [
        threading.Thread(target=transfer, args=(acct_a, acct_b, 10))
        for _ in range(50)
    ] + [
        threading.Thread(target=transfer, args=(acct_b, acct_a, 5))
        for _ in range(50)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return acct_a["balance"], acct_b["balance"]


# ============================================================================
# Q17: Livelock Resolution via Randomized Jitter Backoff
# ============================================================================
def q17_livelock_avoidance_transfer() -> bool:
    """Uses non-blocking acquire + randomized jitter to avoid livelock."""
    lock_1 = threading.Lock()
    lock_2 = threading.Lock()

    def polite_worker(first: threading.Lock, second: threading.Lock) -> bool:
        while True:
            if first.acquire(timeout=0.005):
                try:
                    if second.acquire(blocking=False):
                        try:
                            return True
                        finally:
                            second.release()
                finally:
                    first.release()
            # Jitter breaks symmetric retry livelock
            time.sleep(random.uniform(0.0005, 0.003))

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(polite_worker, lock_1, lock_2)
        f2 = ex.submit(polite_worker, lock_2, lock_1)
        return f1.result(timeout=2.0) and f2.result(timeout=2.0)


# ============================================================================
# Q18: Runtime Detection for Free-Threaded Python (PEP 703 / Py_GIL_DISABLED)
# ============================================================================
def q18_check_free_threaded_runtime() -> dict[str, Any]:
    """Checks whether the current interpreter runs with the GIL disabled."""
    info = runtime_concurrency_info()
    info["recommended_cpu_pool"] = (
        "ThreadPoolExecutor" if not info["gil_enabled"] else "ProcessPoolExecutor"
    )
    return info


# ============================================================================
# Q19: Bounded Blocking Queue from Scratch (LeetCode #1188)
# ============================================================================
class BoundedBlockingQueue(Generic[T]):
    """Thread-safe bounded blocking queue built from Lock + Condition variables."""

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._queue: collections.deque[T] = collections.deque()
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def enqueue(self, element: T) -> None:
        with self._not_full:
            while len(self._queue) >= self._capacity:
                self._not_full.wait()
            self._queue.append(element)
            self._not_empty.notify()

    def dequeue(self) -> T:
        with self._not_empty:
            while not self._queue:
                self._not_empty.wait()
            item = self._queue.popleft()
            self._not_full.notify()
            return item

    def size(self) -> int:
        with self._lock:
            return len(self._queue)


# ============================================================================
# Q20: Writer-Preference Read-Write Lock (RWLock)
# ============================================================================
class WriterPreferenceRWLock:
    """Allows concurrent readers but blocks new readers when a writer is waiting."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._active_readers = 0
        self._active_writers = 0
        self._waiting_writers = 0

    @contextlib.contextmanager
    def read_lock(self) -> Iterator[None]:
        with self._cond:
            while self._active_writers > 0 or self._waiting_writers > 0:
                self._cond.wait()
            self._active_readers += 1
        try:
            yield
        finally:
            with self._cond:
                self._active_readers -= 1
                if self._active_readers == 0:
                    self._cond.notify_all()

    @contextlib.contextmanager
    def write_lock(self) -> Iterator[None]:
        with self._cond:
            self._waiting_writers += 1
            try:
                while self._active_readers > 0 or self._active_writers > 0:
                    self._cond.wait()
                self._active_writers += 1
            finally:
                self._waiting_writers -= 1
        try:
            yield
        finally:
            with self._cond:
                self._active_writers -= 1
                self._cond.notify_all()


# ============================================================================
# Q21: Thread-Safe Striped/Sharded LRU Cache with TTL
# ============================================================================
class _LRUShard(Generic[K, V]):
    def __init__(self, capacity: int, ttl_seconds: float) -> None:
        self.capacity = max(1, capacity)
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
        self.store: collections.OrderedDict[K, tuple[V, float]] = collections.OrderedDict()

    def get(self, key: K) -> V | None:
        now = time.monotonic()
        with self.lock:
            if key not in self.store:
                return None
            val, expires_at = self.store[key]
            if now > expires_at:
                del self.store[key]
                return None
            self.store.move_to_end(key)
            return val

    def put(self, key: K, value: V) -> None:
        expires_at = time.monotonic() + self.ttl
        with self.lock:
            if key in self.store:
                self.store.move_to_end(key)
            self.store[key] = (value, expires_at)
            if len(self.store) > self.capacity:
                self.store.popitem(last=False)


class ShardedThreadSafeLRUCache(Generic[K, V]):
    """Reduces lock contention by sharding keys across independent locks."""

    def __init__(self, total_capacity: int = 64, num_shards: int = 8, ttl_seconds: float = 60.0) -> None:
        shard_cap = max(1, total_capacity // num_shards)
        self._shards = [_LRUShard[K, V](shard_cap, ttl_seconds) for _ in range(num_shards)]

    def _get_shard(self, key: K) -> _LRUShard[K, V]:
        return self._shards[hash(key) % len(self._shards)]

    def get(self, key: K) -> V | None:
        return self._get_shard(key).get(key)

    def put(self, key: K, value: V) -> None:
        self._get_shard(key).put(key, value)


# ============================================================================
# Q22: Dining Philosophers (LeetCode #1226) — Waiter Semaphore + Lock Ordering
# ============================================================================
class DiningPhilosophers:
    """Prevents deadlock by bounding concurrent diners to N-1 (4) via a Semaphore."""

    def __init__(self) -> None:
        self._forks = [threading.Lock() for _ in range(5)]
        self._waiter = threading.Semaphore(4)

    def wants_to_eat(
        self,
        philosopher: int,
        pick_left: Callable[[], None],
        pick_right: Callable[[], None],
        eat: Callable[[], None],
        put_left: Callable[[], None],
        put_right: Callable[[], None],
    ) -> None:
        left_fork = self._forks[philosopher]
        right_fork = self._forks[(philosopher + 1) % 5]
        with self._waiter:
            with left_fork, right_fork:
                pick_left()
                pick_right()
                eat()
                put_right()
                put_left()


# ============================================================================
# Q23: Thread-Safe Singleton with Double-Checked Locking
# ============================================================================
class ThreadSafeSingleton:
    """Double-checked locking ensures lock overhead only occurs on first creation."""

    _instance: ThreadSafeSingleton | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> ThreadSafeSingleton:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance


# ============================================================================
# Q24: Custom ThreadPool Implementation from Scratch
# ============================================================================
class CustomThreadPool:
    """Minimal production-style ThreadPool with Future support and graceful shutdown."""

    def __init__(self, max_workers: int = 4) -> None:
        self._tasks: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any], concurrent.futures.Future[Any]] | None] = queue.Queue()
        self._shutdown = False
        self._lock = threading.Lock()
        self._workers = [
            threading.Thread(target=self._worker_loop, name=f"CustomPool-{i}", daemon=True)
            for i in range(max_workers)
        ]
        for w in self._workers:
            w.start()

    def _worker_loop(self) -> None:
        while True:
            item = self._tasks.get()
            try:
                if item is None:
                    return
                fn, args, kwargs, fut = item
                if not fut.set_running_or_notify_cancel():
                    continue
                try:
                    result = fn(*args, **kwargs)
                    fut.set_result(result)
                except BaseException as exc:
                    fut.set_exception(exc)
            finally:
                self._tasks.task_done()

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> concurrent.futures.Future[T]:
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Cannot submit tasks after shutdown")
            fut: concurrent.futures.Future[T] = concurrent.futures.Future()
            self._tasks.put((fn, args, kwargs, fut))
            return fut

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            for _ in self._workers:
                self._tasks.put(None)
        if wait:
            for w in self._workers:
                w.join()


# ============================================================================
# Q25: Thread-Safe Token Bucket Rate Limiter
# ============================================================================
class TokenBucketRateLimiter:
    """Lazily refills tokens using monotonic clock without background threads."""

    def __init__(self, capacity: float, refill_rate_per_sec: float) -> None:
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate_per_sec)
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def allow_request(self, tokens_needed: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False


# ============================================================================
# Q26: Bridging asyncio Event Loops and OS Threads
# ============================================================================
def q26_bridge_asyncio_and_threads() -> int:
    """Runs an asyncio loop in a background thread and submits coroutines thread-safely."""
    loop = asyncio.new_event_loop()
    loop_ready = threading.Event()

    def run_event_loop() -> None:
        asyncio.set_event_loop(loop)
        loop_ready.set()
        loop.run_forever()

    loop_thread = threading.Thread(target=run_event_loop, name="AsyncLoopThread")
    loop_thread.start()
    loop_ready.wait()

    async def async_compute(x: int) -> int:
        # Offload blocking call safely to a worker thread from inside asyncio
        val = await asyncio.to_thread(lambda v: v * 2, x)
        return val + 1

    # Submit coroutine from MainThread into AsyncLoopThread safely
    concurrent_future = asyncio.run_coroutine_threadsafe(async_compute(21), loop)
    result = concurrent_future.result(timeout=2.0)

    loop.call_soon_threadsafe(loop.stop)
    loop_thread.join()
    loop.close()
    return result


# ============================================================================
# Q27: Building H2O Molecule Synchronizer (LeetCode #1117)
# ============================================================================
class H2OMoleculeBuilder:
    """Ensures threads bond in strict sets of 2 Hydrogen and 1 Oxygen."""

    def __init__(self) -> None:
        self._h_sem = threading.Semaphore(2)
        self._o_sem = threading.Semaphore(1)
        self._barrier = threading.Barrier(3)

    def hydrogen(self, release_hydrogen: Callable[[], None]) -> None:
        with self._h_sem:
            self._barrier.wait()
            release_hydrogen()

    def oxygen(self, release_oxygen: Callable[[], None]) -> None:
        with self._o_sem:
            self._barrier.wait()
            release_oxygen()


# ============================================================================
# Q28: Multithreaded Web Crawler with Atomic Deduplication (LeetCode #1242)
# ============================================================================
def q28_multithreaded_crawler(start_url: str, graph: dict[str, list[str]]) -> list[str]:
    """Crawls same-hostname URLs using atomic check-and-set to avoid duplicate work."""
    hostname = start_url.split("/")[2]
    visited: set[str] = {start_url}
    visit_lock = threading.Lock()

    def get_urls(url: str) -> list[str]:
        time.sleep(0.005)
        return graph.get(url, [])

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        active_futures: set[concurrent.futures.Future[list[str]]] = {
            executor.submit(get_urls, start_url)
        }

        while active_futures:
            done, active_futures = concurrent.futures.wait(
                active_futures, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for fut in done:
                for next_url in fut.result():
                    if next_url.split("/")[2] == hostname:
                        with visit_lock:
                            if next_url not in visited:
                                visited.add(next_url)
                                active_futures.add(executor.submit(get_urls, next_url))

    return sorted(visited)


# ============================================================================
# Q29: Tuning CPython Thread Switch Interval Context Manager
# ============================================================================
@contextlib.contextmanager
def custom_switch_interval(seconds: float) -> Iterator[None]:
    """Temporarily adjusts CPython's bytecode thread switch interval and restores it."""
    original = sys.getswitchinterval()
    sys.setswitchinterval(seconds)
    try:
        yield
    finally:
        sys.setswitchinterval(original)


# ============================================================================
# Q30: Subinterpreters / InterpreterPoolExecutor Fallback Pattern (Python 3.13/3.14)
# ============================================================================
def q30_subinterpreter_or_thread_pool(items: list[int]) -> list[int]:
    """Uses InterpreterPoolExecutor (PEP 734) if available in Python 3.14+, else ThreadPoolExecutor."""
    executor_cls = getattr(
        concurrent.futures,
        "InterpreterPoolExecutor",
        concurrent.futures.ThreadPoolExecutor,
    )
    with executor_cls(max_workers=2) as executor:
        return list(executor.map(int, items))


if __name__ == "__main__":
    logger.info("Running Advanced Multithreading Solutions Verification...")
    assert q16_deadlock_free_transfer() == (750, 1250)
    assert q17_livelock_avoidance_transfer() is True
    assert "gil_enabled" in q18_check_free_threaded_runtime()

    bbq = BoundedBlockingQueue[int](capacity=2)
    bbq.enqueue(10)
    bbq.enqueue(20)
    assert bbq.size() == 2 and bbq.dequeue() == 10

    rw = WriterPreferenceRWLock()
    with rw.write_lock():
        shared_val = 42
    with rw.read_lock():
        assert shared_val == 42

    cache = ShardedThreadSafeLRUCache[str, int](total_capacity=16, num_shards=4, ttl_seconds=5.0)
    cache.put("alpha", 99)
    assert cache.get("alpha") == 99

    s1, s2 = ThreadSafeSingleton(), ThreadSafeSingleton()
    assert s1 is s2

    custom_pool = CustomThreadPool(max_workers=2)
    fut = custom_pool.submit(lambda a, b: a + b, 15, 27)
    assert fut.result(timeout=1.0) == 42
    custom_pool.shutdown(wait=True)

    limiter = TokenBucketRateLimiter(capacity=2, refill_rate_per_sec=100)
    assert limiter.allow_request(2) is True and limiter.allow_request(1) is False

    assert q26_bridge_asyncio_and_threads() == 43

    h2o = H2OMoleculeBuilder()
    atoms: list[str] = []
    atom_lock = threading.Lock()
    h2o_threads = [
        threading.Thread(target=h2o.hydrogen, args=(lambda: atoms.append("H"),))
        for _ in range(4)
    ] + [
        threading.Thread(target=h2o.oxygen, args=(lambda: atoms.append("O"),))
        for _ in range(2)
    ]
    for t in h2o_threads:
        t.start()
    for t in h2o_threads:
        t.join()
    assert len(atoms) == 6 and sorted(atoms[:3]) == ["H", "H", "O"]

    mock_web = {
        "http://news.yahoo.com/a": ["http://news.yahoo.com/b", "http://google.com/x"],
        "http://news.yahoo.com/b": ["http://news.yahoo.com/a", "http://news.yahoo.com/c"],
    }
    assert q28_multithreaded_crawler("http://news.yahoo.com/a", mock_web) == [
        "http://news.yahoo.com/a",
        "http://news.yahoo.com/b",
        "http://news.yahoo.com/c",
    ]

    with custom_switch_interval(0.002):
        assert abs(sys.getswitchinterval() - 0.002) < 1e-6

    assert q30_subinterpreter_or_thread_pool([1, 2, 3]) == [1, 2, 3]
    logger.info("All 15 Advanced Solutions passed assertions successfully!")