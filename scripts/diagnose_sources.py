"""Read-only, bounded arXiv diagnostics on the actual GitHub runner."""
import json
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET


def main():
    query = 'all:protein AND submittedDate:[202501010000 TO 202501312359]'
    params = dict(search_query=query, max_results=1)
    variants = [
        ('minimal', 'https://export.arxiv.org/api/query?search_query=all:protein&max_results=1', {}),
        ('encoded', 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params), {}),
        ('syntax-preserved', 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params, safe=':[]'), {}),
        ('alternate-host', 'https://arxiv.org/api/query?' + urllib.parse.urlencode(params), {}),
        ('custom-agent', 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params),
         {'User-Agent': 'awesome-protein-literature/1.0'})]
    for name, url, headers in variants:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
                data = response.read()
                root = ET.fromstring(data)
                print(json.dumps(dict(case=name, status=response.status,
                    total=root.findtext('{http://a9.com/-/spec/opensearch/1.1/}totalResults'))), flush=True)
        except urllib.error.HTTPError as error:
            print(json.dumps(dict(case=name, status=error.code, body=error.read(300).decode(errors='replace'))), flush=True)
        except Exception as error:
            print(json.dumps(dict(case=name, error=str(error))), flush=True)


if __name__ == '__main__':
    main()
