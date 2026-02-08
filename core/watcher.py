import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from state_manager import state

class ExperimentHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        self.queue = event_queue
        self.timers = {}  # Store active timers: {path: Timer}
        self.debounce_interval = 2.0  # Wait 2 seconds after LAST write
        self.marker_file = ".restore_in_progress"

    def on_created(self, event):
        """Added to catch files immediately when they are dropped/pasted."""
        if not event.is_directory:
            self.on_modified(event)

    def on_modified(self, event):
        if event.is_directory or not (event.src_path.endswith('.csv') or event.src_path.endswith('.xlsx')):
            return
        # 1. Check for the "Restore" marker in the parent directory
        # This prevents the app from auto-committing when YOU restore an old version
        marker_path = os.path.join(os.path.dirname(event.src_path), self.marker_file)
        if os.path.exists(marker_path):
            return 
        # 2. Advanced Debouncing (Reset timer on every event)
        # If a timer already exists for this file, cancel it (user is still writing)
        if event.src_path in self.timers:
            self.timers[event.src_path].cancel()
        # Start a new timer
        timer = threading.Timer(self.debounce_interval, self._trigger_event, args=[event.src_path])
        self.timers[event.src_path] = timer
        timer.start()

    def _trigger_event(self, path):
        """Called only when the file has been silent for `debounce_interval`."""
        # Clean up timer reference
        if path in self.timers:
            del self.timers[path]
        
        # Verify file still exists (it might have been deleted during the delay)
        if os.path.exists(path):
            self.queue.put({"type": "NEW_FILE", "path": path})

def start_watcher(path_to_watch, event_queue):
    if not os.path.exists(path_to_watch):
        os.makedirs(path_to_watch)
        
    event_handler = ExperimentHandler(event_queue)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=False)
    observer.start()
    return observer