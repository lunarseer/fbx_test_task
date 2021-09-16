import argparse
from os import path, makedirs, listdir, remove, getenv
import sys
import requests
from zipfile import ZipFile

RUNDIRECTORY = path.dirname(__file__)
TEMPDIRECTORY = path.join(RUNDIRECTORY, 'temp_downloads')

print(TEMPDIRECTORY)

sys.path.append(RUNDIRECTORY)

from setup import log


class Job:
    pass


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
        archive = self.__download(url)
        result = self.__extract_zip(archive)
        result


    def __download(self, url):
        filename = url.split('/')[-1]
        filepath = path.join(TEMPDIRECTORY, filename)

        if not path.exists(TEMPDIRECTORY):
            makedirs(TEMPDIRECTORY)
        if path.exists(filepath):
            remove(filepath)
            log.debug(f'{filepath} overwrited!')
        r = requests.get(url, allow_redirects=True)
        open(filepath, 'wb').write(r.content)
        log.info(f'{url} downloaded')
        return filepath

    def __extract_zip(self, archive):
        with ZipFile(archive, 'r') as file:
            file.extractall(TEMPDIRECTORY)
            log.info(f'{archive} extracted')
            return True

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