import argparse
from os import path
import sys
import requests

RUNDIRECTORY = path.dirname(__file__)
sys.path.append(RUNDIRECTORY)

from setup import log

class JobExecutor:


    def __init__(self, *args):
        result = {}
        parser = argparse.ArgumentParser(description='simple parser')
        parser.add_argument('--file', dest="file", help='path to file with urls', required=True)
        parser.add_argument('--out', dest="output", help='path to output', required=True)
        parsed = parser.parse_args(*args)
        self.urlfile = parsed.file
        self.output = parsed.output

    def run(self):
        urls = self.__get_url_list()
        for url in urls:
            self.do(url)

    def do(self, url):
        filename = url.split('/')[-1]
        r = requests.get(url, allow_redirects=True)
        filepath = path.join(self.output, filename)
        print(filepath)
        # open('google.ico', 'wb').write(r.content)
        log.info(f'downloading {url}')

    def __get_url_list(self):
        if not all([path.exists(self.urlfile), path.isfile(self.urlfile)]):
            raise FileNotFoundError(f'{self.urlfile} Not Exists!')
        else:
            with open(self.urlfile) as urlfile:
                urlist = [l.rstrip() for l in urlfile.readlines()]
                return urlist



if __name__ == '__main__':
    log.info(f'Starting in {RUNDIRECTORY}')
    argv = sys.argv[sys.argv.index('--') + 1:]
    executor = JobExecutor(argv)
    executor.run()