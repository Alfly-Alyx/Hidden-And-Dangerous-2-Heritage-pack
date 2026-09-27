"""Synthetic objective checks, no commercial hand or geometry fixtures."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fit_rigid_finger_curls import refine,index_seeds
from fit_rigid_weapon_grips import stock_wrist_allowed


class IndividualFingerFitTests(unittest.TestCase):
    def test_modern_stock_posture_rejects_high_or_forward_wrist(self):
        self.assertTrue(stock_wrist_allowed([.12,-.18,.01],[.07,-.13,.16]))
        self.assertFalse(stock_wrist_allowed([.14,-.07,.02],[.07,-.13,.16]))
        self.assertFalse(stock_wrist_allowed([.12,-.18,.08],[.07,-.13,.16]))
        with self.assertRaises(ValueError):stock_wrist_allowed([True,0,0],[0,0,0])

    def test_never_trades_crossings_for_proximity(self):
        seed=[0,0,0]
        values,cost=refine(seed,lambda v:(int(any(v)),0 if any(v) else 1))
        self.assertEqual(values,seed);self.assertEqual(cost,(0,1,0));self.assertEqual(seed,[0,0,0])

    def test_moves_only_within_domain_and_keeps_equal_cost_seed(self):
        values,cost=refine([0,0,0],lambda v:(0,sum((a-b)**2 for a,b in zip(v,[15,-7.5,3.75]))))
        self.assertEqual(values,[15,-7.5,3.75]);self.assertEqual(cost[:2],(0,0))
        values,_=refine([110,-110,0],lambda v:(0,1))
        self.assertEqual(values,[110,-110,0])

    def test_optional_splay_search_is_bounded_separately(self):
        values,cost=refine([0,0,0,0],lambda v:(0,sum((a-b)**2 for a,b in zip(v,[15,-7.5,3.75,40]))))
        self.assertEqual(values,[15,-7.5,3.75,30]);self.assertEqual(cost[:2],(0,100))
        for seed in ([0,0,0,31],[0,0,0,True],[0,0],None):
            with self.assertRaises(ValueError):refine(seed,lambda v:(0,0))

    def test_index_grid_keeps_seed_and_has_no_duplicates_or_unbounded_angles(self):
        seed=[-10,-20,-30,5];rows=index_seeds(seed)
        self.assertEqual(rows[0],seed);self.assertEqual(len(rows),82)
        self.assertEqual(len({tuple(row) for row in rows}),82)
        self.assertTrue(all(all(-110<=v<=110 for v in row[:3]) and -30<=row[3]<=30 for row in rows))
        self.assertEqual(len(index_seeds([-90,-90,-90,-30])),81)
        rows[0][0]=0;self.assertEqual(seed,[-10,-20,-30,5])
        with self.assertRaises(ValueError):index_seeds([0,0,0])

    def test_invalid_measurements_or_angles_refused(self):
        for result in ((True,0),(-1,0),(0,float('nan')),(0,-1),(0,True),[0,0],(0,0,0)):
            with self.assertRaises(ValueError):refine([0,0,0],lambda v:result)
        with self.assertRaises(ValueError):refine([111,0,0],lambda v:(0,0))


if __name__=='__main__':unittest.main()
