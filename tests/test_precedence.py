import unittest
from unittest.mock import patch
from app.rag.precedence import resolve_precedence

class TestPrecedence(unittest.TestCase):
    @patch('app.rag.precedence.get_doc_metadata')
    def test_precedence_resolution(self, mock_get_doc_metadata):
        # Mocking the DB metadata
        mock_docs = {
            'reg1': {
                'doc_id': 'reg1',
                'authority_level': 1,
                'effective_from': '2024-07-01',
                'supersedes': None
            },
            'circ1': {
                'doc_id': 'circ1',
                'authority_level': 2,
                'effective_from': '2026-08-01',
                'supersedes': 'reg1'
            },
            'faq1': {
                'doc_id': 'faq1',
                'authority_level': 4,
                'effective_from': '2024-01-01',
                'supersedes': None
            }
        }
        
        mock_get_doc_metadata.side_effect = lambda doc_id: mock_docs.get(doc_id, {})
        
        chunks = [
            {"text": "Attendance required is 75%", "metadata": {"doc_id": "reg1"}},
            {"text": "Attendance required is 80%", "metadata": {"doc_id": "circ1"}},
            {"text": "Attendance required is 65%", "metadata": {"doc_id": "faq1"}}
        ]
        
        # Scenario: Circular L2 supersedes Regulation L1. FAQ L4 is ignored.
        # Actually, if Circular L2 supersedes Reg L1, Reg L1 is excluded.
        # Then between Circ1 and FAQ1, Circ1 has authority 2 and FAQ1 has authority 4.
        # Circ1 wins.
        
        result = resolve_precedence(chunks, as_of_date='2026-09-01')
        
        self.assertEqual(result['answer_type'], 'standard')
        self.assertEqual(len(result['chunks']), 1)
        self.assertEqual(result['chunks'][0]['metadata']['doc_id'], 'circ1')
        self.assertEqual(result['chunks'][0]['text'], 'Attendance required is 80%')

if __name__ == '__main__':
    unittest.main()
