# Python Multithreading — Advanced Interview Questions (16–30)

## 16. What are the 4 Coffman Conditions for Deadlock, and how do you guarantee deadlock-free lock acquisition across multiple resources?
* **Citations / Asked In:** Google, Amazon, Devinterview.io
* **Concept:** Deadlocks require four simultaneous conditions: (1) Mutual Exclusion, (2) Hold and Wait, (3) No Preemption, and (4) Circular Wait. The standard production fix breaks **Circular Wait** by enforcing a strict global **Lock Acquisition Ordering** (e.g., sorting locks by `id(lock)` or account ID via a `@contextlib.contextmanager`) or breaks **Hold and Wait** using `lock.acquire(timeout=...)`.

## 17. Distinguish between Deadlock, Livelock, and Thread Starvation. How do you fix Livelock?
* **Citations / Asked In:** Microsoft, Goldman Sachs, Devinterview.io
* **Concept:**
  * **Deadlock:** Threads are permanently blocked waiting for each other's locks (0% CPU usage, zero progress).
  * **Livelock:** Threads actively release and retry acquiring locks in lockstep to avoid deadlock, burning CPU cycles without making progress. Fixed by introducing **randomized exponential backoff (jitter)** before retrying.
  * **Starvation:** Low-priority or slow threads are perpetually bypassed by greedy threads. Fixed via fair queuing or writer-preference locks.

## 18. How does Free-Threaded CPython (PEP 703 / Python 3.13 & 3.14 `Py_GIL_DISABLED`) change multithreading in Python?
* **Citations / Asked In:** Meta, Google, CoPrep AI 2026 Guide
* **Concept:** Starting with Python 3.13 (experimental `python3.13t`) and maturing in Python 3.14 (with first-class `asyncio` support), CPython can be built with the GIL disabled (`sys._is_gil_enabled() == False`). It uses **biased reference counting**, **immortal objects** (for `None`, `True`, small ints), and **per-object fine-grained locks** on built-in collections (`dict`, `list`). Crucially, removing the GIL allows true multi-core CPU parallelism with `threading`, but makes **application-level thread synchronization mandatory** because operations truly overlap across CPU cores.

## 19. Design a Thread-Safe Bounded Blocking Queue from Scratch (Without `queue.Queue`).
* **Citations / Asked In:** LinkedIn, Uber, Meta (LeetCode #1188 Design Bounded Blocking Queue)
* **Concept:** Use a `collections.deque` protected by a single `threading.Lock` and two `threading.Condition` variables sharing that lock: `not_full` and `not_empty`. `enqueue()` waits in a `while len(buf) == capacity` loop on `not_full`, appends the item, and notifies `not_empty`. `dequeue()` waits in a `while len(buf) == 0` loop on `not_empty`, pops from the left, and notifies `not_full`.

## 20. Implement a Writer-Preference Read-Write Lock (`RWLock`) in Python.
* **Citations / Asked In:** Bloomberg, Citadel, Two Sigma
* **Concept:** A naive Read-Write lock allows unlimited concurrent readers, which starves waiting writers if readers continuously overlap. A **Writer-Preference RWLock** tracks `active_readers`, `active_writers`, and `waiting_writers`. New readers must wait if `active_writers > 0 OR waiting_writers > 0`, ensuring pending writes flush promptly.

## 21. Design a Thread-Safe LRU Cache with TTL and Fine-Grained / Striped Locking.
* **Citations / Asked In:** Google, Robinhood, Databricks
* **Concept:** Wrapping an entire LRU cache in a single global lock creates a throughput bottleneck under high concurrency. By partitioning keys across $K$ independent shards (`hash(key) % K`), where each shard has its own `Lock` and `OrderedDict`, threads accessing different shards run concurrently without contention.

## 22. Solve the Dining Philosophers Problem Without Deadlock or Starvation.
* **Citations / Asked In:** Apple, Palantir, Amazon (LeetCode #1226 The Dining Philosophers)
* **Concept:** If all 5 philosophers pick up their left fork simultaneously, circular wait causes a deadlock. Classic solutions either: (1) use a `Semaphore(4)` waiter limiting at most $N-1$ philosophers at the table simultaneously, or (2) enforce **asymmetric resource hierarchy** where the last philosopher picks up the higher-indexed fork first.

## 23. How do you implement a Thread-Safe Singleton in Python using Double-Checked Locking?
* **Citations / Asked In:** Adobe, Salesforce, IBM
* **Concept:** Acquiring a lock on every `__new__` call adds unnecessary lock overhead after initialization. Double-checked locking checks `if cls._instance is None:` outside the lock first; only if `None` does it acquire `cls._lock`, check `if cls._instance is None:` a second time (in case another thread initialized it while waiting for the lock), and construct the instance.

## 24. Implement a Custom `ThreadPoolExecutor` from Scratch (Worker Pool, Task Queue, `Future`, and `shutdown()`).
* **Citations / Asked In:** Uber, Rubrik, Confluent
* **Concept:** A thread pool maintains a fixed list of worker threads pulling `(fn, args, kwargs, future)` tuples from a shared `queue.Queue`. Each worker executes `fn(*args, **kwargs)` and calls `future.set_result(res)` or `future.set_exception(exc)`. Calling `shutdown(wait=True)` sets an atomic closed flag, pushes poison-pill sentinels for each worker, and joins all worker threads.

## 25. Implement a Thread-Safe Token Bucket Rate Limiter.
* **Citations / Asked In:** Stripe, Cloudflare, DoorDash
* **Concept:** Rather than spawning a background thread to add tokens on a timer (which wastes resources and suffers from timer drift), compute token refills **lazily** inside a lock using `time.monotonic()`: `tokens = min(capacity, tokens + (now - last_refill) * refill_rate)`.

## 26. How do you safely bridge `asyncio` Event Loops and Multithreading (`run_coroutine_threadsafe` vs. `asyncio.to_thread`)?
* **Citations / Asked In:** Netflix, Discord, OpenAI, CoPrep AI
* **Concept:** `asyncio` objects (`Task`, `Future`, `asyncio.Queue`) are **not thread-safe**.
  * To run blocking synchronous I/O from inside an async coroutine without freezing the event loop: await `asyncio.to_thread(blocking_fn, *args)`.
  * To schedule a coroutine onto a running event loop from a separate OS worker thread: call `asyncio.run_coroutine_threadsafe(coro, loop)`, which returns a thread-safe `concurrent.futures.Future`.

## 27. Solve the H2O Molecule Barrier Problem (2 Hydrogen Threads + 1 Oxygen Thread).
* **Citations / Asked In:** LinkedIn, Amazon (LeetCode #1117 Building H2O)
* **Concept:** Threads arrive randomly as `H` or `O` and must bond in strict groups of two `H` and one `O`. Combine `threading.Semaphore(2)` for Hydrogen, `threading.Semaphore(1)` for Oxygen, and a `threading.Barrier(3)` so that exactly two H threads and one O thread cross the bonding barrier together before releasing the semaphores for the next molecule.

## 28. Design a Multithreaded Web Crawler with Thread-Safe URL Deduplication.
* **Citations / Asked In:** Dropbox, Meta (LeetCode #1242 Web Crawler Multithreaded)
* **Concept:** A multithreaded crawler must avoid crawling the same URL twice. Checking `if url not in visited:` and adding `visited.add(url)` must happen **atomically inside the same lock acquisition** before submitting the task to the `ThreadPoolExecutor`, otherwise multiple threads will enqueue duplicate HTTP requests simultaneously.

## 29. How does CPython's `sys.getswitchinterval()` work, and what is the GIL Convoy Effect?
* **Citations / Asked In:** Jane Street, Hudson River Trading, Dropbox
* **Concept:** Since Python 3.2, CPython uses a time-based switch interval (default `0.005` seconds = 5ms, configurable via `sys.setswitchinterval()`). When a thread holds the GIL for 5ms, CPython sets an atomic eval-breaker flag requesting the holder to release the GIL and signal waiting threads. The **convoy effect** occurs when CPU-bound threads repeatedly preempt I/O-bound threads that wake up from OS system calls and must wait up to the switch interval to re-acquire the GIL.

## 30. What are Subinterpreters and `InterpreterPoolExecutor` (PEP 734 / Python 3.13–3.14), and how do they compare to `ThreadPoolExecutor` and `ProcessPoolExecutor`?
* **Citations / Asked In:** Snowflake, Canonical, CoPrep AI 2026 Guide
* **Concept:** PEP 734 (`concurrent.futures.InterpreterPoolExecutor` and `interpreters` module in Python 3.13/3.14) runs isolated Python interpreters inside the **same OS process**, each with its own independent GIL (per-interpreter GIL, PEP 684). This gives multi-core CPU parallelism like `ProcessPoolExecutor` with the much lower memory and startup overhead of `ThreadPoolExecutor`, without shared-memory data races.