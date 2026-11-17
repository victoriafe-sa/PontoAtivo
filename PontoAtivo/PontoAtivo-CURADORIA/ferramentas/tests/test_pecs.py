import unittest
from ferramentas.curadoria import assess_pec_candidate

class PecTest(unittest.TestCase):
    def test_reform_near_existing_is_not_published(self):
        published=[{"id":"a","name":"PEC QNF 24","address":"QNF 24","latitude":-15.82,"longitude":-48.08}]
        candidate={"id":"b","name":"PEC revitalizada QNF 24","address":"QNF 24","latitude":-15.8197,"longitude":-48.08}
        result=assess_pec_candidate(candidate,published)
        self.assertFalse(result["publish"]); self.assertEqual(result["status"],"possible_duplicate")
    def test_candidate_without_precise_address_is_review_only(self):
        result=assess_pec_candidate({"name":"Nova PEC no Sudoeste"},[])
        self.assertFalse(result["publish"]); self.assertEqual(result["reason"],"address_unconfirmed")

if __name__ == "__main__": unittest.main()
