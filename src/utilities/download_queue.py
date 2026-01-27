#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import requests
import threading
import queue
import uuid
from pathlib import Path
from time import sleep
from enum import auto, IntEnum
from typing import NotRequired, TypedDict, Protocol, Unpack
# from collections.abc import Callable

class TaskStatus(IntEnum):
    QUEUED = auto()     # "queued", added to queue but not started
    STARTED = auto()    # "started", download initiated
    SUCCEEDED = auto()  # "succeeded", download completed successfully
    FAILED = auto()     # "failed", download failed

# class DownloadCallbackKwargs(TypedDict, total=False):
class DownloadCallbackKwargs(TypedDict):
    """TypedDict defining the exact keyword arguments passed to download task callbacks.
    
    Attributes:
        task_id: Unique identifier for the download task
        status: Task status (queued/started/succeeded/failed)
        url: Download URL of the file
        save_path: Local path to save the file
        extra_msg: Extra message (only present for "failed" status)
    """
    # task_id: str
    status: TaskStatus
    # url: str
    save_path: str
    extra_msg: NotRequired[str]

# Define the precise callback type
# DownloadCallback = Callable[[Unpack[DownloadCallbackKwargs]], None]
class DownloadCallback(Protocol):
    def __call__(self, **kwargs: Unpack[DownloadCallbackKwargs]) -> None:
        """Protocol for download task callbacks (strict keyword args)"""
        ...

class DownloadQueue:
    """A thread-safe download queue manager with per-task callbacks and proxy support.

    This class manages sequential file downloads in an independent thread, supports
    HTTP/HTTPS proxies, allows adding tasks at any time, and triggers individual
    callback functions for each task's lifecycle events (queued/started/succeeded/failed).

    Attributes:
        _task_queue: Thread-safe queue storing download tasks
        _proxies: HTTP/HTTPS proxy configuration
        _is_running: Flag to control the download worker thread
        _download_thread: The background thread executing download tasks
    """
    def __init__(self, proxies: dict[str, str] | None = None) -> None:
        """Initialize the DownloadQueue instance.

        Args:
            proxies: Optional proxy configuration dictionary. Format:
                {"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}
        """
        # Protected attributes (single leading underscore)
        self._task_queue: queue.Queue[tuple[str, str, str, DownloadCallback | None]] = queue.Queue()
        self._proxies: dict[str, str] | None = proxies
        self._is_running: bool = False
        self._download_thread: threading.Thread | None = None

    def _download_file(self, task_id: str, url: str, save_path: str,
            task_callback: DownloadCallback | None) -> bool:
        """Handle single file download with proxy support.

        Args:
            task_id: Unique identifier for the download task
            url: URL of the file to download
            save_path: Local path to save the downloaded file
            task_callback: Callback function for this specific task

        Returns:
            bool: True if download succeeds, False otherwise

        Raises:
            requests.exceptions.RequestException: For HTTP request errors
            OSError: For file system operations errors
        """
        is_success = False
        try:
            # Trigger "started" callback for this task
            self._trigger_task_callback(
                task_id,
                task_callback=task_callback,
                status=TaskStatus.STARTED,
                # url=url,
                save_path=save_path
            )

            # Send HTTP request with proxy support and stream download
            response = requests.get(
                url=url,
                stream=True,
                timeout=30,
                proxies=self._proxies  # Access proxy attribute
            )
            response.raise_for_status()  # Raise exception for HTTP errors (4xx/5xx)

            # Create parent directory if it doesn't exist
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)

            # Write file in chunks to avoid high memory usage
            with open(save_path, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive new chunks
                        _ = file_handle.write(chunk)

            sleep(0.1)

            is_success = True

        except requests.RequestException as e:
            extra_msg = f"Fail to download：{str(e)}"
            print(f"task {task_id[:8]} download exception：{extra_msg}")
            self._trigger_task_callback(
                task_id,
                task_callback=task_callback,
                status=TaskStatus.FAILED,
                # url=url,
                save_path=save_path,
                extra_msg=extra_msg
            )
        except OSError as e:
            extra_msg = f"fail to operate file: {str(e)}"
            print(f"task {task_id[:8]} file exception: {extra_msg}")
            self._trigger_task_callback(
                task_id,
                task_callback=task_callback,
                status=TaskStatus.FAILED,
                # url=url,
                save_path=save_path,
                extra_msg=extra_msg
            )
        except Exception as e:
            extra_msg = f"Unkown exception{str(e)}"
            print(f"task {task_id[:8]} Unkown exception：{extra_msg}")
            self._trigger_task_callback(
                task_id,
                task_callback=task_callback,
                status=TaskStatus.FAILED,
                # url=url,
                save_path=save_path,
                extra_msg=extra_msg
            )

        if is_success:
            self._trigger_task_callback(
                task_id,
                task_callback=task_callback,
                status=TaskStatus.SUCCEEDED,
                # url=url,
                save_path=save_path
            )

        return is_success

    def _download_worker(self) -> None:
        """Background worker thread to process tasks sequentially.

        This method runs in a separate thread and continuously fetches tasks from
        the task queue until _is_running is set to False.
        """
        while self._is_running:  # Access protected running flag
            try:
                # Get task from queue
                task = self._task_queue.get(block=True, timeout=1)
                task_id, url, save_path, task_callback = task

                # Execute download for this task
                _ = self._download_file(task_id, url, save_path, task_callback)

                # Mark task as completed in the queue
                self._task_queue.task_done()

            except queue.Empty:
                # Continue looping to wait for new tasks (don't exit)
                continue
            except Exception as e:
                # Catch unexpected exceptions to prevent thread crash
                print(f"Unexpected error in download worker: {str(e)}")
                continue

    def _trigger_task_callback(self, task_id: str, *,
            task_callback: DownloadCallback | None,
            **kwargs: Unpack[DownloadCallbackKwargs]):
        """Internal protected method to trigger task-specific callback (if provided).

        Args:
            task_callback: Callback function for the task (None if not provided)
            **kwargs: Arbitrary keyword arguments to pass to the callback
        """
        if task_callback is not None:
            try:
                task_callback(**kwargs)
            except Exception as e:
                # Catch callback execution errors to avoid affecting download process
                print(f"Error executing callback for task {task_id}: {str(e)}")

    def add_task(self, url: str, save_path: str,
            task_callback: DownloadCallback | None = None) -> str:
        """Add a new download task to the queue (supports adding midway).

        This is the public interface for adding tasks - external code should never
        modify _task_queue directly.

        Args:
            url: URL of the file to download
            save_path: Local path to save the downloaded file
            task_callback: Optional callback function for this specific task.
                The callback should accept these keyword arguments:
                - task_id (str): Unique task identifier
                - status (str): Task status (queued/started/succeeded/failed)
                - url (str): Download URL
                - save_path (str): Local save path
                - extra_msg (str): Error message (only for failed status)

        Returns:
            str: Unique UUID identifier for the added task
        """
        # Generate unique task ID using UUID4
        task_id = str(uuid.uuid4())

        # Add task to PROTECTED queue
        self._task_queue.put((task_id, url, save_path, task_callback))

        # Trigger "queued" callback for this task
        self._trigger_task_callback(
            task_id,
            task_callback=task_callback,
            status=TaskStatus.QUEUED,
            # url=url,
            save_path=save_path
        )

        # Automatically start the download thread if not running
        if not self._is_running:
            self.start()

        return task_id

    def start(self) -> None:
        """Public interface to start the background download worker thread.

        This method is thread-safe and controls the protected _is_running flag -
        external code should never modify _is_running directly.
        """
        if self._is_running:
            print("Download queue is already running")
            return

        self._is_running = True  # Modify protected flag via public method
        # Create and start daemon thread
        self._download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self._download_thread.start()
        print("Download queue started successfully")

    def stop(self) -> None:
        """Stop the background download worker thread gracefully.

        This method controls the protected _is_running flag and _download_thread -
        external code should never modify these attributes directly.
        """
        if not self._is_running:
            print("Download queue is not running")
            return

        self._is_running = False  # Modify protected flag
        # Wait for thread to finish with timeout
        if self._download_thread and self._download_thread.is_alive():
            self._download_thread.join(timeout=5)
        print("Download queue stopped successfully")

    def get_queue_size(self) -> int:
        """Get the number of pending tasks (safe access to queue size).

        Returns:
            int: Number of tasks waiting to be processed
        """
        return self._task_queue.qsize()  # Safe read-only access to protected queue

    def get_proxies(self) -> dict[str, str] | None:
        """Get proxy configuration (read-only access).

        Returns:
            dict[str, str] | None: Proxy configuration dictionary (None if no proxy)
        """
        return self._proxies  # Read-only access to protected proxy attribute

    def set_proxies(self, proxies: dict[str, str]):
        """ Set proxy configuration (read-only access).

        Args:
            proxies: proxy configuration dictionary. Format:
                {"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}
        """
        self._proxies = proxies

    def is_running(self) -> bool:
        """Check if the download queue is running.

        Returns:
            bool: True if the queue is running, False otherwise
        """
        return self._is_running  # Read-only access to protected running flag

    def wait_for_completion(self) -> None:
        """Block until all tasks are completed.

        External code should use this instead of accessing _task_queue.join() directly.
        """
        self._task_queue.join()  # Safe access to protected queue


# ------------------------------ TEST EXAMPLE ------------------------------
if __name__ == "__main__":
    # Example 1: Callback function for PDF files
    def pdf_task_callback(**kwargs: Unpack[DownloadCallbackKwargs]):
        """Callback function specifically for PDF download tasks."""
        status_emoji: dict[int, str] = {
            TaskStatus.QUEUED: "📋",
            TaskStatus.STARTED: "🚀",
            TaskStatus.SUCCEEDED: "✅",
            TaskStatus.FAILED: "❌"
        }
        emoji = status_emoji.get(kwargs["status"], "ℹ️")
        
        # print(f"\n{emoji} PDF Task [{kwargs['task_id']}]: {kwargs['status']}")
        print(f"\n{emoji} PDF Task {kwargs['status'].name.upper()}")
        # print(f"   URL: {kwargs['url']}")
        # print(f"   Save Path: {kwargs['save_path']}")
        if "extra_msg" in kwargs and kwargs["extra_msg"]:
            print(f"   Error: {kwargs["extra_msg"]}")

    # Example 2: Callback function for image files
    def image_task_callback(**kwargs: Unpack[DownloadCallbackKwargs]):
        """Callback function specifically for image download tasks."""
        # print(f"\n\tImage Task Update: [{kwargs['task_id']}] {kwargs['status']}")
        print(f"\n\tImage Task Update - {kwargs['status']}")
        # print(f"   Target: {kwargs['save_path']}")

    # Initialize download queue with proxy (set to None if no proxy needed)
    proxy_config: dict[str, str] | None = None
    download_manager = DownloadQueue(proxies=proxy_config)

    # Add initial tasks (via PUBLIC add_task() method - correct usage)
    print("=== Adding initial tasks ===")
    task1_id = download_manager.add_task(
        url="https://example.com/sample1.pdf",
        save_path="./downloads/sample1.pdf",
        task_callback=pdf_task_callback
    )
    task2_id = download_manager.add_task(
        url="https://example.com/sample2.jpg",
        save_path="./downloads/sample2.jpg",
        task_callback=image_task_callback
    )

    # Access queue status via PUBLIC getter methods (correct usage)
    print(f"\nCurrent pending tasks: {download_manager.get_queue_size()}")
    print(f"Is queue running? {download_manager.is_running()}")
    print(f"Proxy configuration: {download_manager.get_proxies()}")

    # Demonstrate adding tasks midway (while downloads are in progress)
    print("\n=== Adding midway task after 2 seconds ===")
    sleep(2)  # Simulate delay before adding new task
    task3_id = download_manager.add_task(
        # Intentionally invalid URL
        url="https://example.com/invalid_file.zip",
        save_path="./downloads/invalid.zip",
        # task_callback=lambda **kwargs:print((f"\n\tError Task [{kwargs['task_id']}]"
        task_callback=lambda **kwargs: print((f"\n\tError Task "
            f"{kwargs['status'].name}: {kwargs.get('extra_msg', 'No error')}"))
    )

    task4_id = download_manager.add_task(
        url="https://dictionary.so8848.com/ajax_search/?q=good",
        save_path="good.json",
        task_callback=lambda **kwargs: print((f"\n️  Task "
            f"{kwargs['status'].name}: {kwargs.get('extra_msg', 'No error')}"))
    )

    # Wait for all tasks to complete (via PUBLIC method)
    try:
        print("\n=== Waiting for all tasks to complete ===")
        download_manager.wait_for_completion()
        print((f"\n📊 All tasks processed! Pending tasks remaining: "
            f"{download_manager.get_queue_size()}"))
    except KeyboardInterrupt:
        # Stop queue via PUBLIC stop() method
        download_manager.stop()
        print("\n🛑 Download queue stopped by user interrupt")
