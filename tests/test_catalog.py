import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from catalog import record, merge, identifiers, ROOT, read_json, relevant
from migrate_readme import migrate
from restore_pending import restore
from render_papers import render, entry


class CatalogTests(unittest.TestCase):
    def test_migration_preserves_entries_and_links(self):
        import re
        text = (ROOT / 'README.md').read_text()
        papers = migrate(text)
        self.assertEqual(len(papers), len(re.findall(r'^\*\*', text, re.M)))
        expected = re.findall(r'\[\[([^\]]+)\]\(([^\n]+?)\)\]', text)
        actual = [(k, v) for p in papers for k, v in p['links'].items()]
        self.assertCountEqual(expected, actual)
        self.assertTrue(all(p['authors'] for p in papers))

    def test_version_and_publication_dedup(self):
        first = record('Antibody design', 'A', 'https://doi.org/10.1101/example', 'bioRxiv', version='1')
        first['related_dois'] = ['10.1000/published']
        papers = []
        merge(papers, [first], [], '2026-09-20')
        journal = record('Changed journal title', 'A', 'https://doi.org/10.1000/published', 'Europe PMC')
        self.assertTrue(merge(papers, [journal], [], '2026-09-21'))
        self.assertEqual(len(papers), 1)
        self.assertFalse(merge(papers, [journal], [], '2026-09-22'))
        self.assertEqual(papers[0]['first_seen'], '2026-09-20')

    def test_excluded_stays_excluded(self):
        p = record('Protein design', 'A', 'https://arxiv.org/abs/2601.12345v2', 'arXiv')
        self.assertEqual(identifiers(p['links']['Paper']), {'arxiv': '2601.12345'})
        papers = []
        merge(papers, [p], [{'id': p['id']}], '2026-09-20')
        self.assertEqual(papers, [])
        self.assertEqual(restore([], [p], [{'id': p['id']}]), [])

    def test_restore_keeps_review(self):
        p = record('Protein design', 'A', 'https://doi.org/10.1000/x', 'source')
        reviewed = dict(p, status='curated')
        self.assertEqual(restore([reviewed], [p], [])[0]['status'], 'curated')

    def test_scope(self):
        self.assertTrue(relevant('Antibody design', ''))
        self.assertTrue(relevant('Protein language models', ''))
        self.assertFalse(relevant('Clinical antibody trial', 'patient outcomes'))

    def test_render_is_deterministic(self):
        render()
        before = {p: p.read_bytes() for p in (ROOT / 'papers').rglob('*.md')}
        render()
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_unsafe_link_not_rendered(self):
        p = record('<script>Title</script>', 'A', 'javascript:alert(1)', 'source')
        self.assertNotIn('javascript:', entry(p))


if __name__ == '__main__':
    unittest.main()
