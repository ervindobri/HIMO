import time
import threading


class BaseThread(threading.Thread):
    def __init__(self, callback=None, callback_args=None, arglist=None, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, args=arglist, **kwargs)
        self.callback = callback
        self.method = target
        self.callback_args = callback_args

    def target_with_callback(self):
        self.method()
        if self.callback is not None:
            self.callback(*self.callback_args)


def my_thread_job():
    # do any things here
    print("thread start successfully and sleep for 5 seconds")
    time.sleep(5)
    print( "thread ended successfully!")


def cb(param1, param2):
    # this is run after your thread end
    print("callback function called")
    print("{} {}".format(param1, param2))


# example using BaseThread with callback
thread = BaseThread(
    name='test',
    target=my_thread_job,
    callback=cb,
    callback_args=("hello", "world")
)

thread.start()