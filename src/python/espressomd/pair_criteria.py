from .script_interface import ScriptInterfaceHelper, script_interface_register
from .particle_data import ParticleHandle


@script_interface_register
class PairCriterion(ScriptInterfaceHelper):
    """Base class for a criterion which makes a decision based on two particles"""
    _so_name = "PairCriteria::PairCriterion"

    def decide(self, p1, p2):
        """Makes a decision based on the two particles specified.
           p2,p2 : Instances of ParticleHandle or integers containing the particle id.
        """
        id1 = None
        id2 = None
        if isinstance(p1, ParticleHandle) and isinstance(p2, ParticleHandle):
            id1 = p1.id
            id2 = p2.id
        elif isinstance(p1, int) and isinstance(p2, int):
            id1 = p1
            id2 = p2
        else:
            raise ValueError(
                "arguments must be instances of int or ParticleHandle")
        return self.call_method("decide", id1=id1, id2=id2)


@script_interface_register
class DistanceCriterion(PairCriterion):
    """Pair criterion returning true, if particles are closer than a cut off.
       Periodic boundaries are treated via minimum image convention.

       The following parameters can be passed to the constructor, changed via set_params() 
       and retrieved via get_params()

       cut_off : float, distance cut off for the criterion
    """
    _so_name = "PairCriteria::DistanceCriterion"


@script_interface_register
class EnergyCriterion(PairCriterion):
    """Pair criterion returning true, if the short range energy between the particles is >= the cutoff"

       The following parameters can be passed to the constructor, changed via set_params() 
       and retrieved via get_params()

       cut_off : float, energy cut off for the criterion
    """
    _so_name = "PairCriteria::EnergyCriterion"


@script_interface_register
class BondCriterion(PairCriterion):
    """Pair criterion returning true, if a bond of given type exists between them

       The following parameters can be passed to the constructor, changed via set_params() 
       and retrieved via get_params()

       bond_type : int, numeric type of the bond 
    """
    _so_name = "PairCriteria::BondCriterion"
