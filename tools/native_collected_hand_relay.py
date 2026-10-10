"""Native model frame-vector collection feeds the compiled hand relay directly."""
from native_bound_hand_relay import BoundHandRelayOracle
from native_hand_model_collect import HandModelCollectionOracle


class CollectedHandRelayOracle(BoundHandRelayOracle):
    BINDING=HandModelCollectionOracle

    def build_binding(self,records):
        # The caller supplies known readable extents, not a pointer obtained by
        # chasing untrusted memory. C verifies that the native model agrees.
        return self.binding.collect(self.STATE+0x100,0x170,self.SOURCE+0x400,len(records)*4,records)

    def run(self,**kwargs):
        result=super().run(**kwargs)
        return {**result,'native_model_frame_vector_used':True,'node_collection_order_from_native_model':True,
                'live_client_ownership_and_equipment_profile_qualified':False}
