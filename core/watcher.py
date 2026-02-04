import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue

class ExperimentHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        self.queue = event_queue

    def on_created(self, event):
        # Ignore directories and non-csv files
        if event.is_directory:
            return
        
        filename = event.src_path
        if filename.endswith('.csv') or filename.endswith('.xlsx'):
            # Allow file write to finish
            time.sleep(0.5) 
            self.queue.put({"type": "NEW_FILE", "path": filename})

def start_watcher(path_to_watch, event_queue):
    # Ensure directory exists
    if not os.path.exists(path_to_watch):
        os.makedirs(path_to_watch)
        
    event_handler = ExperimentHandler(event_queue)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=False)
    observer.start()
    return observer