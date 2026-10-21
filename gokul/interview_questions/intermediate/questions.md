# Python Multithreading — Intermediate Interview Questions (1–15)

## 1. What is the difference between Concurrency and Parallelism, and when should you use `threading` in Python?
* **Citations / Asked In:** Amazon, Microsoft, CoPrep AI Concurrency Guide, Devinterview.io
* **Concept:** Concurrency means multiple tasks make progress during overlapping time periods (interleaving execution), while parallelism means multiple tasks execute at the exact same instant across multiple CPU cores. In standard CPython, `threading` achieves concurrency for **I/O-bound workloads** (network calls, disk reads, database queries) because threads release the GIL while waiting for OS-level I/O.

## 2. What is the Global Interpreter Lock (GIL), why does CPython have it, and when is it released?
* **Citations / Asked In:** Google, Bloomberg, Dropbox, CoPrep AI
* **Concept:** The GIL is a mutex protecting access to Python objects, preventing multiple native threads from executing Python bytecodes simultaneously inside a single standard CPython process. It exists primarily to keep CPython's reference-counting memory management (`ob_refcnt`) thread-safe and fast without fine-grained locks on every object. The GIL is released during blocking I/O calls (`read`, `write`, `recv`, `time.sleep`) and inside C extensions (like NumPy, PyTorch, or `hashlib`) that explicitly wrap C computation in `Py_BEGIN_ALLOW_THREADS`.

## 3. What is the difference between `thread.start()` and `thread.run()`, and how does `thread.join(timeout)` work?
* **Citations / Asked In:** Amazon, TCS, Infosys, Wipro
* **Concept:** Calling `start()` spawns a new OS-level thread that invokes `run()` asynchronously. Calling `run()` directly executes the target function synchronously inside the **calling thread** without creating any new thread. `join(timeout=N)` blocks the calling thread until the target thread terminates or `N` seconds elapse; you must check `thread.is_alive()` afterward to know if `join()` timed out.

## 4. How do Daemon Threads (`daemon=True`) differ from Non-Daemon Threads during interpreter shutdown?
* **Citations / Asked In:** Cisco, Oracle, PayPal
* **Concept:** The Python process stays alive as long as at least one **non-daemon** thread is running. Daemon threads run in the background (e.g., heartbeat monitors, telemetry flushers, cache eviction loops) and are abruptly terminated when all non-daemon threads exit—meaning `finally` blocks and open file flushes in daemon threads are not guaranteed to run unless coordinated with a shutdown signal.

## 5. Why can race conditions still occur in Python despite the GIL? Prove it with `x += 1`.
* **Citations / Asked In:** Meta, Dropbox, CoPrep AI
* **Concept:** The GIL protects CPython's internal interpreter state, **not** application-level business logic. An operation like `x += 1` compiles into multiple bytecode instructions (`LOAD_GLOBAL`, `LOAD_CONST`, `BINARY_OP` / `INPLACE_ADD`, `store`). A thread switch can occur between `LOAD` and `STORE`, causing lost updates.

## 6. What is the difference between `threading.Lock` and `threading.RLock` (Reentrant Lock)?
* **Citations / Asked In:** Bloomberg, Goldman Sachs, Morgan Stanley
* **Concept:** A standard `Lock` cannot be acquired twice by the same thread without releasing it first—doing so causes an immediate self-deadlock. An `RLock` tracks the **owning thread ID** and a **recursion counter**, allowing the same thread to acquire the lock multiple times (e.g., in recursive functions or when one synchronized class method calls another synchronized method on `self`). It must be released the exact same number of times before another thread can acquire it.

## 7. How do you solve the Producer-Consumer problem safely in Python using `queue.Queue`?
* **Citations / Asked In:** Amazon, Uber, Walmart Labs, Devinterview.io
* **Concept:** `queue.Queue` encapsulates internal locks and condition variables (`not_empty`, `not_full`, `all_tasks_done`). Producers call `q.put(item)` (blocking if bounded and full), and consumers call `q.get()` followed by `q.task_done()`. Using a **sentinel value (`None`)** or `q.join()` ensures clean pipeline completion without busy-waiting.

## 8. How do `threading.Semaphore` and `threading.BoundedSemaphore` work for rate-limiting or connection pooling?
* **Citations / Asked In:** Stripe, Uber, Cloudflare, Devinterview.io
* **Concept:** A Semaphore maintains an internal counter decremented by `acquire()` and incremented by `release()`, allowing up to $N$ threads into a critical section simultaneously. However, a standard `Semaphore` allows calling `release()` more times than `acquire()`, accidentally raising the pool capacity above $N$. `BoundedSemaphore` raises a `ValueError` if `release()` increments the counter beyond its initial value, catching bugs where a thread releases a permit it never acquired.

## 9. How do you coordinate thread startup or cancellation using `threading.Event`?
* **Citations / Asked In:** Apple, Qualcomm, NVIDIA
* **Concept:** `threading.Event` wraps a thread-safe boolean flag. Threads calling `event.wait(timeout)` block efficiently (without burning CPU cycles in a `while` loop) until another thread calls `event.set()`. Calling `event.clear()` resets the flag to `False`. It is ideal for start-gates, pause/resume toggles, and graceful cancellation tokens.

## 10. How does `threading.Condition` work, and why must `wait()` always be checked inside a `while` loop rather than an `if` statement?
* **Citations / Asked In:** LinkedIn, Microsoft, Adobe
* **Concept:** A `Condition` combines a lock with a wait-queue so threads can sleep until a specific state predicate becomes true (`wait()`) and wake waiting threads (`notify()` / `notify_all()`). You must always check the condition in a `while not predicate(): cond.wait()` loop because of **spurious wakeups** at the OS pthread level and because another awakened thread may consume the state change before the current thread re-acquires the lock.

## 11. When and how do you use `threading.Barrier`?
* **Citations / Asked In:** Citadel, JPMorgan Chase
* **Concept:** `threading.Barrier(parties, action=...)` blocks a fixed number of threads (`parties`) until **all** of them reach the barrier call (`barrier.wait()`). Once the last thread arrives, the optional `action` callback runs once, and all threads are released simultaneously. If a thread times out or calls `abort()`, the barrier enters a broken state and raises `BrokenBarrierError` in all waiting threads to prevent permanent hangs.

## 12. How does `threading.local()` work and where is it used in production frameworks?
* **Citations / Asked In:** Meta (Instagram), Spotify, Django / Flask Core Interviews
* **Concept:** `threading.local()` creates an object whose attributes are isolated per thread—each thread reads and writes its own independent dictionary under the hood. Web frameworks (like Werkzeug/Flask contexts and Django's database connection handlers) and observability libraries use thread-local storage to store request IDs, user sessions, and DB connections without passing them through every function signature.

## 13. Compare `ThreadPoolExecutor.submit()` vs. `ThreadPoolExecutor.map()` and `as_completed()`.
* **Citations / Asked In:** Netflix, Airbnb, Amazon, CoPrep AI
* **Concept:**
  * `executor.map(fn, iterables)` yields results **in the exact order of the input iterable**, blocking on slow earlier items even if later items finished first.
  * `executor.submit(fn, *args)` returns a `Future` object immediately, allowing heterogeneous tasks and consumption via `concurrent.futures.as_completed(futures)`, which yields futures **in the exact order they finish**.

## 14. Why do unhandled exceptions inside `threading.Thread` disappear silently from the main thread, and how do you capture them?
* **Citations / Asked In:** Datadog, Snowflake, Atlassian
* **Concept:** Exceptions raised inside a child `threading.Thread` are caught by the thread's bootstrap wrapper and printed to `sys.stderr` (or passed to `threading.excepthook`), **not** raised in the parent thread that called `join()`. To propagate exceptions to the caller, either use `ThreadPoolExecutor` (where `future.result()` re-raises the worker exception in the caller) or subclass `Thread` to store `self.exc` and re-raise it inside `join()`.

## 15. Classic Coding Question: Print "FooBar" or Odd-Even Numbers Alternately Across Two Threads.
* **Citations / Asked In:** Meta, Yahoo, Amazon (LeetCode #1114 Print in Order / LeetCode #1115 Print FooBar Alternately)
* **Concept:** Given two threads (one printing odd numbers, one printing even numbers up to $N$), using `time.sleep()` is an anti-pattern that fails under load. The deterministic interview solution uses either two cross-signaling `Lock`/`Semaphore` objects or a shared `Condition` variable checking `current % 2`.