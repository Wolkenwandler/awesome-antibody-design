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


class BackfillTests(unittest.TestCase):
    def test_calendar_windows_are_contiguous(self):
        from datetime import date, timedelta
        from backfill_papers import windows
        result = list(windows(date(2025, 12, 26), date(2026, 3, 2)))
        self.assertEqual(result[0], (date(2025, 12, 26), date(2025, 12, 31)))
        self.assertEqual(result[-1], (date(2026, 3, 1), date(2026, 3, 2)))
        for left, right in zip(result, result[1:]):
            self.assertEqual(left[1] + timedelta(days=1), right[0])

class IndexedHistoryTests(unittest.TestCase):
    @patch('update_papers.request')
    def test_biorxiv_index_uses_publication_date_and_explicit_platform(self, request):
        from urllib.parse import urlparse, parse_qs
        from update_papers import biorxiv_indexed
        request.return_value = {'resultList': {'result': [{'title': 'Protein design', 'source': 'PPR', 'id': 'PPR1', 'doi': '10.1101/example'}]}}
        rows = list(biorxiv_indexed('2025-01-01', '2025-01-31', 1))
        query = parse_qs(urlparse(request.call_args[0][0]).query)['query'][0]
        self.assertIn('FIRST_PDATE:[2025-01-01 TO 2025-01-31]', query)
        self.assertIn('PUBLISHER:"bioRxiv"', query)
        self.assertEqual(rows[0]['source'], 'bioRxiv (Europe PMC index)')


class ArxivEndpointTests(unittest.TestCase):
    @patch('update_papers.time.sleep')
    @patch('update_papers.request')
    def test_406_retries_identical_query_on_official_alternate_host(self, request, sleep):
        from update_papers import SourceHTTPError
        request.side_effect = [SourceHTTPError(406, ''), ET.fromstring('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>0</o:totalResults></feed>')]
        self.assertEqual(list(arxiv('2025-01-01', '2025-01-31', 1)), [])
        original, alternate = [c.args[0] for c in request.call_args_list]
        self.assertEqual(original.replace('export.arxiv.org', 'arxiv.org'), alternate)

    @patch('update_papers.time.sleep')
    @patch('update_papers.request')
    def test_other_http_errors_remain_failures(self, request, sleep):
        from update_papers import SourceHTTPError
        request.side_effect = SourceHTTPError(400, 'invalid query')
        with self.assertRaises(SourceHTTPError):
            list(arxiv('2025-01-01', '2025-01-31', 1))
        self.assertEqual(request.call_count, 1)
