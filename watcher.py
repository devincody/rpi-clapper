import time  
import sys
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler



class MyHandler(PatternMatchingEventHandler):
    ignore_directories = True
    def __init__(self, patterns = ["*/data.txt"]):
        super().__init__(patterns = patterns)
        self.data = 0
        self.valid_time = 0
        print("data = {}".format(self.data))

    def process(self, event):
        """
        event.event_type 
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print(event.src_path, event.event_type)  # print now only for degug
        if not event.is_directory:
            try:
                f = open(event.src_path)
                self.data = float(f.readline())
                self.valid_time = self.data * 60 + time.time()
                print("data = {}".format(self.data))
            except:
                pass
            
    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def check_paused(self):
        return self.valid_time > time.time()


if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
    observer.schedule(MyHandler(), '/home/pi/')
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
