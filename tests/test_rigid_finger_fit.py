"""Synthetic objective checks, no commercial hand or geometry fixtures."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fit_rigid_finger_curls import refine


class IndividualFingerFitTests(unittest.TestCase):
    def test_never_trades_crossings_for_proximity(self):
        seed=[0,0,0]
        values,cost=refine(seed,lambda v:(int(any(v)),0 if any(v) else 1))
        self.assertEqual(values,seed);self.assertEqual(cost,(0,1,0));self.assertEqual(seed,[0,0,0])

    def test_moves_only_within_domain_and_keeps_equal_cost_seed(self):
        values,cost=refine([0,0,0],lambda v:(0,sum((a-b)**2 for a,b in zip(v,[15,-7.5,3.75]))))
        self.assertEqual(values,[15,-7.5,3.75]);self.assertEqual(cost[:2],(0,0))
        values,_=refine([110,-110,0],lambda v:(0,1))
        self.assertEqual(values,[110,-110,0])

    def test_invalid_measurements_or_angles_refused(self):
        for result in ((True,0),(-1,0),(0,float('nan')),(0,-1),(0,True),[0,0],(0,0,0)):
            with self.assertRaises(ValueError):refine([0,0,0],lambda v:result)
        with self.assertRaises(ValueError):refine([111,0,0],lambda v:(0,0))


if __name__=='__main__':unittest.main()
