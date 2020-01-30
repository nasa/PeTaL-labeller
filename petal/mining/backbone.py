from pprint import pprint
from subprocess import call
from time import time

import requests, zipfile, os

from neo import add_json

from neo4j import GraphDatabase, basic_auth
neoDriver = GraphDatabase.driver("bolt://139.88.179.199:7687", auth=basic_auth("neo4j", "testing"))

# TODO: setup auto downloads from here?

col_date = '2019-05-01' # Make sure this is a valid COL release

def create_dir():
    if not os.path.isfile('col_data/taxa.txt'):
        try:
            data = requests.get('http://www.catalogueoflife.org/DCA_Export/zip-fixed/{}-archive-complete.zip'.format(col_date))
            with open('col.zip', 'wb') as outfile:
                outfile.write(data.content)
            with zipfile.ZipFile('col.zip', 'r') as zip_handle:
                zip_handle.extractall('col_data')
        except:
            if os.path.isfile('col.zip'):
                os.remove('col.zip')
            shutil.rmtree('col_data')


def read():
    start = time()
    i = 0
    with open('col_data/taxa.txt', 'r', encoding='utf-8') as infile:
        headers = None
        json    = dict()
        for line in infile:
            if i == 0:
                headers = line.split('\t')
                headers = ('id',) + tuple(headers[1:])
            else:
                for k, v in zip(headers, line.split('\t')):
                    json[k] = v
                try:
                    json.pop('isExtinct\n')
                except KeyError:
                    pass
                if json['taxonRank'] == 'species':
                    with neoDriver.session() as session:
                        session.read_transaction(add_json, label='Species', properties=json) 
                json = dict()
            try:
                total = i
                duration = time() - start
                species_per_sec = total / duration
                total_seconds  = 1.9e6 / species_per_sec
                eta_seconds = total_seconds - duration
                eta = eta_seconds / 3600
                percent = duration / total_seconds
                print('Species: {}, Rate: {} species per second, ETA: {}h, Percent: {}\r'.format(total, round(species_per_sec, 1), round(eta, 1), round(percent, 5)), flush=True, end='')
            except ZeroDivisionError:
                pass

            i += 1

if __name__ == '__main__':
    create_dir()
    read()
