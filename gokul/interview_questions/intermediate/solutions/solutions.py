"""
intermediate/solutions/solutions.py
Executable reference implementations for Intermediate Questions (Q1 - Q15).
Run directly via: python intermediate/solutions/solutions.py
"""

from __future__ import annotations

import concurrent.futures
import dis
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

# Import shared utilities from common_start.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common_start import benchmark_threads, logger


# ============================================================================
# Q1 & Q2: I/O-Bound Concurrency vs. Sequential Execution under the GIL
# ============================================================================
@benchmark_threads
def q1_q2_io_concurrency_demo(num_tasks: int = 8, io_delay: float = 0.05) -> list[int]:
    """Demonstrates how threads release the GIL during blocking I/O calls."""
    def simulated_io_call(task_id: int) -> int:
        time.sleep(io_delay)  # Releases the GIL during OS sleep/I/O wait
        return task_id * 10

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_tasks) as pool:
        results = list(pool.map(simulated_io_call, range(num_tasks)))
    return results


# ============================================================================
# Q3: Thread Lifecycle — start() vs run() and join(timeout)
# ============================================================================
def q3_lifecycle_and_join_timeout() -> tuple[str, str, bool]:
    """Shows thread identity difference between run() and start(), plus join timeout."""
    recorded_threads: list[str] = []

    def worker(delay: float) -> None:
        recorded_threads.append(threading.current_thread().name)
        time.sleep(delay)

    t1 = threading.Thread(target=worker, args=(0.0,), name="SpawnedWorker")
    t1.run()    # Executes synchronously on MainThread!
    t1.start()  # Executes asynchronously on SpawnedWorker
    t1.join()

    slow_thread = threading.Thread(target=worker, args=(0.2,), name="SlowWorker")
    slow_thread.start()
    slow_thread.join(timeout=0.02)
    timed_out = slow_thread.is_alive()
    slow_thread.join()
    return recorded_threads[0], recorded_threads[1], timed_out


# ============================================================================
# Q4: Daemon Thread with Graceful Shutdown Hook
# ============================================================================
def q4_daemon_with_graceful_stop() -> int:
    """Uses a daemon thread for background telemetry with an explicit stop Event."""
    stop_event = threading.Event()
    heartbeats = 0

    def telemetry_daemon() -> None:
        nonlocal heartbeats
        while not stop_event.wait(timeout=0.01):
            heartbeats += 1

    daemon_t = threading.Thread(target=telemetry_daemon, name="TelemetryDaemon", daemon=True)
    daemon_t.start()
    time.sleep(0.05)
    stop_event.set()
    daemon_t.join(timeout=0.5)
    return heartbeats


# ============================================================================
# Q5: Proving Race Conditions Despite the GIL & Fixing with Lock
# ============================================================================
def q5_race_condition_vs_lock() -> tuple[int, int]:
    """Shows bytecode non-atomicity and repairs a shared counter using threading.Lock."""
    counter = 0
    lock = threading.Lock()
    barrier = threading.Barrier(4)

    def unsafe_increment(iterations: int) -> None:
        nonlocal counter
        barrier.wait()
        for _ in range(iterations):
            temp = counter
            time.sleep(0)  # Force context switch opportunity between LOAD and STORE
            counter = temp + 1

    threads = [threading.Thread(target=unsafe_increment, args=(50,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    unsafe_result = counter

    # Thread-safe version
    counter = 0

    def safe_increment(iterations: int) -> None:
        nonlocal counter
        for _ in range(iterations):
            with lock:
                counter += 1

    threads = [threading.Thread(target=safe_increment, args=(50,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return unsafe_result, counter


# ============================================================================
# Q6: RLock (Reentrant Lock) in Composable Class Methods
# ============================================================================
class ThreadSafeBankAccount:
    """Demonstrates why RLock is required when synchronized methods call each other."""

    def __init__(self, balance: int = 0) -> None:
        self.balance = balance
        self._rlock = threading.RLock()

    def deposit(self, amount: int) -> None:
        with self._rlock:
            self.balance += amount

    def apply_bonus_and_deposit(self, amount: int, bonus: int) -> int:
        with self._rlock:
            # Re-acquires self._rlock inside deposit() without self-deadlocking
            self.deposit(amount + bonus)
            return self.balance


# ============================================================================
# Q7: Thread-Safe Producer-Consumer with queue.Queue & Sentinel Shutdown
# ============================================================================
def q7_producer_consumer_pipeline(items: list[int], num_consumers: int = 3) -> list[int]:
    """Processes items via bounded queue with poison-pill sentinel termination."""
    work_queue: queue.Queue[int | None] = queue.Queue(maxsize=5)
    results: list[int] = []
    results_lock = threading.Lock()

    def producer() -> None:
        for item in items:
            work_queue.put(item)
        for _ in range(num_consumers):
            work_queue.put(None)  # Poison pill sentinel per consumer

    def consumer() -> None:
        while True:
            item = work_queue.get()
            try:
                if item is None:
                    return
                processed = item * item
                with results_lock:
                    results.append(processed)
            finally:
                work_queue.task_done()

    prod_thread = threading.Thread(target=producer, name="Producer")
    cons_threads = [
        threading.Thread(target=consumer, name=f"Consumer-{i}")
        for i in range(num_consumers)
    ]

    prod_thread.start()
    for ct in cons_threads:
        ct.start()

    prod_thread.join()
    work_queue.join()
    for ct in cons_threads:
        ct.join()

    return sorted(results)


# ============================================================================
# Q8: BoundedSemaphore Connection Pool Guard
# ============================================================================
class ConnectionPoolGuard:
    """Limits concurrent active connections and prevents accidental over-release."""

    def __init__(self, max_connections: int = 3) -> None:
        self._sem = threading.BoundedSemaphore(max_connections)
        self._lock = threading.Lock()
        self.active_count = 0
        self.peak_concurrency = 0

    def execute_query(self, query: str) -> str:
        with self._sem:
            with self._lock:
                self.active_count += 1
                self.peak_concurrency = max(self.peak_concurrency, self.active_count)
            time.sleep(0.02)
            with self._lock:
                self.active_count -= 1
            return f"Result({query})"


# ============================================================================
# Q9: Start-Gate Synchronization Using threading.Event
# ============================================================================
def q9_event_start_gate(num_workers: int = 4) -> list[str]:
    """Holds all worker threads at a start gate until main thread signals readiness."""
    start_gate = threading.Event()
    log_order: list[str] = []
    lock = threading.Lock()

    def worker(worker_id: int) -> None:
        start_gate.wait()  # Blocks efficiently until start_gate.set()
        with lock:
            log_order.append(f"Worker-{worker_id}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_workers)]
    for t in threads:
        t.start()

    start_gate.set()  # Release all waiting workers simultaneously
    for t in threads:
        t.join()
    return log_order


# ============================================================================
# Q10: threading.Condition with While-Loop Predicate
# ============================================================================
def q10_condition_variable_demo() -> list[int]:
    """Demonstrates producer-consumer signaling with threading.Condition."""
    cond = threading.Condition()
    shared_buffer: list[int] = []
    consumed: list[int] = []

    def consumer() -> None:
        with cond:
            while len(shared_buffer) < 3:  # Always use 'while' to guard spurious wakeups
                cond.wait()
            consumed.extend(shared_buffer)
            shared_buffer.clear()

    def producer() -> None:
        for val in (10, 20, 30):
            time.sleep(0.01)
            with cond:
                shared_buffer.append(val)
                if len(shared_buffer) >= 3:
                    cond.notify_all()

    c_thread = threading.Thread(target=consumer)
    p_thread = threading.Thread(target=producer)
    c_thread.start()
    p_thread.start()
    c_thread.join()
    p_thread.join()
    return consumed


# ============================================================================
# Q11: Multi-Stage Synchronization Using threading.Barrier
# ============================================================================
def q11_barrier_matrix_stages(num_workers: int = 3) -> list[str]:
    """Coordinates workers so nobody begins Stage 2 before all finish Stage 1."""
    events: list[str] = []
    lock = threading.Lock()

    def on_stage_one_complete() -> None:
        with lock:
            events.append("STAGE_1_CHECKPOINT")

    barrier = threading.Barrier(parties=num_workers, action=on_stage_one_complete)

    def worker(worker_id: int) -> None:
        with lock:
            events.append(f"W{worker_id}-S1")
        barrier.wait()
        with lock:
            events.append(f"W{worker_id}-S2")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return events


# ============================================================================
# Q12: Thread-Local Request Context Isolation (threading.local)
# ============================================================================
_request_ctx = threading.local()


def q12_thread_local_context() -> dict[str, str]:
    """Verifies each thread holds an isolated request_id without leaking state."""
    observed: dict[str, str] = {}
    lock = threading.Lock()

    def handle_request(user: str, req_id: str) -> None:
        _request_ctx.request_id = req_id
        time.sleep(0.01)  # Overlap execution with other threads
        with lock:
            observed[user] = _request_ctx.request_id

    threads = [
        threading.Thread(target=handle_request, args=(f"user_{i}", f"req_{i * 100}"))
        for i in range(1, 5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return observed


# ============================================================================
# Q13: ThreadPoolExecutor submit() + as_completed() vs map()
# ============================================================================
def q13_as_completed_vs_map() -> tuple[list[int], list[int]]:
    """Shows completion-order harvesting (as_completed) vs input-order (map)."""
    delays = [(1, 0.06), (2, 0.01), (3, 0.03)]

    def task(item: tuple[int, float]) -> int:
        task_id, delay = item
        time.sleep(delay)
        return task_id

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        map_order = list(executor.map(task, delays))

        futures = [executor.submit(task, item) for item in delays]
        completion_order = [
            fut.result() for fut in concurrent.futures.as_completed(futures)
        ]

    return map_order, completion_order


# ============================================================================
# Q14: Exception-Propagating Thread Wrapper
# ============================================================================
class PropagatingThread(threading.Thread):
    """Custom Thread subclass that captures worker exceptions and re-raises on join()."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.exception: BaseException | None = None
        self.return_value: Any = None

    def run(self) -> None:
        try:
            if self._target is not None:  # type: ignore[attr-defined]
                self.return_value = self._target(*self._args, **self._kwargs)  # type: ignore[attr-defined]
        except BaseException as exc:
            self.exception = exc

    def join(self, timeout: float | None = None) -> Any:
        super().join(timeout=timeout)
        if self.exception is not None:
            raise self.exception
        return self.return_value


# ============================================================================
# Q15: Alternating Odd-Even Printer (LeetCode #1114 / #1115 Pattern)
# ============================================================================
def q15_alternating_odd_even(limit: int = 10) -> list[int]:
    """Deterministically prints 1..limit alternating between OddThread and EvenThread."""
    output: list[int] = []
    odd_turn = threading.Semaphore(1)   # Odd starts unlocked
    even_turn = threading.Semaphore(0)  # Even starts locked

    def print_odd() -> None:
        for num in range(1, limit + 1, 2):
            odd_turn.acquire()
            output.append(num)
            even_turn.release()

    def print_even() -> None:
        for num in range(2, limit + 1, 2):
            even_turn.acquire()
            output.append(num)
            odd_turn.release()

    t_odd = threading.Thread(target=print_odd, name="OddThread")
    t_even = threading.Thread(target=print_even, name="EvenThread")
    t_odd.start()
    t_even.start()
    t_odd.join()
    t_even.join()
    return output


if __name__ == "__main__":
    logger.info("Running Intermediate Multithreading Solutions Verification...")
    assert len(q1_q2_io_concurrency_demo(4, 0.01)) == 4
    r_main, r_spawned, timed_out = q3_lifecycle_and_join_timeout()
    assert r_main == "MainThread" and r_spawned == "SpawnedWorker" and timed_out is True
    assert q4_daemon_with_graceful_stop() >= 1
    unsafe_cnt, safe_cnt = q5_race_condition_vs_lock()
    assert safe_cnt == 200 and unsafe_cnt < 200
    acct = ThreadSafeBankAccount(100)
    assert acct.apply_bonus_and_deposit(50, 10) == 160
    assert q7_producer_consumer_pipeline([1, 2, 3, 4, 5]) == [1, 4, 9, 16, 25]
    pool = ConnectionPoolGuard(max_connections=2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(pool.execute_query, ["q1", "q2", "q3", "q4", "q5"]))
    assert pool.peak_concurrency <= 2
    assert len(q9_event_start_gate(4)) == 4
    assert q10_condition_variable_demo() == [10, 20, 30]
    stage_events = q11_barrier_matrix_stages(3)
    assert stage_events[3] == "STAGE_1_CHECKPOINT"
    assert len(q12_thread_local_context()) == 4
    m_order, c_order = q13_as_completed_vs_map()
    assert m_order == [1, 2, 3] and c_order[0] == 2
    assert q15_alternating_odd_even(10) == list(range(1, 11))
    logger.info("All 15 Intermediate Solutions passed assertions successfully!")