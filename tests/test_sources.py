import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_papers import biorxiv, europepmc, arxiv
import xml.etree.ElementTree as ET


class SourceTests(unittest.TestCase):
    @patch('update_papers.time.sleep')
    @patch('update_papers.request')
    def test_biorxiv_paginates_and_links_journal(self, request, sleep):
        request.side_effect = [
            {'messages': [{'status': 'ok', 'total': 2}], 'collection': [{'title': 'Antibody design', 'doi': '10.1101/a', 'published': '10.1000/b'}]},
            {'messages': [{'status': 'ok', 'total': 2}], 'collection': [{'title': 'Protein design', 'doi': '10.1101/c'}]}]
        rows = list(biorxiv('2026-09-01', '2026-09-02', 2))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['related_dois'], ['10.1000/b'])
        self.assertTrue(request.call_args[0][0].endswith('/1'))

    @patch('update_papers.time.sleep')
    @patch('update_papers.request')
    def test_budget_is_failure_not_silent_truncation(self, request, sleep):
        request.return_value = {'messages': [{'status': 'ok', 'total': 2}], 'collection': [{'title': 'Protein design', 'doi': '10.1101/a'}]}
        with self.assertRaises(RuntimeError):
            list(biorxiv('2026-09-01', '2026-09-02', 1))

    @patch('update_papers.request')
    def test_europepmc_preserves_pmid(self, request):
        request.return_value = {'resultList': {'result': [{'title': 'Protein design', 'source': 'MED', 'id': '123', 'doi': '10.1000/a'}]}}
        self.assertEqual(list(europepmc('2026-09-01', '2026-09-02', 1))[0]['identifiers']['pmid'], '123')

    @patch('update_papers.time.sleep')
    @patch('update_papers.request')
    def test_arxiv_empty_and_malformed(self, request, sleep):
        request.return_value = ET.fromstring('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>0</o:totalResults></feed>')
        self.assertEqual(list(arxiv('2026-09-01', '2026-09-02', 1)), [])
        request.return_value = ET.fromstring('<feed/>')
        with self.assertRaises(RuntimeError):
            list(arxiv('2026-09-01', '2026-09-02', 1))
