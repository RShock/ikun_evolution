import io


class Logger:
    _log = io.StringIO()
    _debug = False

    def log(self, string):
        if self._debug:
            print(string)
        else:
            self._log.write(string)
            self._log.write('\n')

    def print_log(self):
        print(self._log.getvalue())

    def clean(self):
        self._log = io.StringIO()
        pass

    def get_log(self):
        # print(self._log)
        return self._log.getvalue()

    def debug_log(self, string):
        print(string)
