"""Utilities for the :class:`GPImageGenerator` and agents utilizing it. The module requires extras to be installed.
"""
import copy
import math
import operator
import random

import deap.base
import deap.tools
import deap.gp

import creamas.domains.image.gp.primitives as prim

#: Maximum depth for GP trees created by functions in this module.
GP_TREE_MAX_DEPTH = 8


class Rand(deap.gp.Ephemeral):
    """A helper class to make ephemeral float constants in the range [-1, 1].
    """
    ret = float

    @staticmethod
    def func():
        return random.random() * 2 - 1


# Set the attribute to DEAP's gp-module to circumvent some problems with ephemeral constants.
setattr(deap.gp, 'Rand', Rand)


PRIMITIVES = {
    'min': (min, [float, float], float),
    'max': (max, [float, float], float),
    'safe_log2': (prim.safe_log2, [float], float),
    'safe_log10': (prim.safe_log10, [float], float),
    'sin': (math.sin, [float], float),
    'cos': (math.cos, [float], float),
    'safe_sinh': (prim.safe_sinh, [float], float),
    'safe_cosh': (prim.safe_cosh, [float], float),
    'tanh': (math.tanh, [float], float),
    'atan': (math.atan, [float], float),
    'hypot': (math.hypot, [float, float], float),
    'abs': (abs, [float], float),
    'abs_sqrt': (prim.abs_sqrt, [float], float),
    'parab': (prim.parab, [float], float),
    'avg_sum': (prim.avg_sum, [float, float], float),
    'sign': (prim.sign, [float], float),
    'mdist': (prim.mdist, [float, float], float),
    'simplex2': (prim.simplex2, [float, float], float),
    'perlin2': (prim.perlin2, [float, float], float),
    'perlin1': (prim.perlin1, [float], float),
    'plasma': (prim.plasma, [float, float, float, float], float),
}


def create_super_pset(bw=True):
    """Create super pset which contains all the primitives for DEAP.

    :param bool bw:
        If ``True`` the returned primitive set is primed to create grayscale images, otherwise it
        will create RGB images.
    :return:
        Created primitive set
    """
    if bw:
        pset = deap.gp.PrimitiveSetTyped("main", [float, float], float)
    else:
        pset = deap.gp.PrimitiveSetTyped("main", [float, float], list)
        pset.addPrimitive(prim.combine, [float, float, float], list)

    # Basic math
    pset.addPrimitive(operator.mul, [float, float], float)
    pset.addPrimitive(prim.safe_div, [float, float], float)
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(prim.safe_mod, [float, float], float)

    # Relational
    pset.addPrimitive(min, [float, float], float)
    pset.addPrimitive(max, [float, float], float)

    # Other math
    pset.addPrimitive(prim.safe_log2, [float], float)
    pset.addPrimitive(prim.safe_log10, [float], float)
    pset.addPrimitive(math.sin, [float], float)
    pset.addPrimitive(math.cos, [float], float)
    pset.addPrimitive(prim.safe_sinh, [float], float)
    pset.addPrimitive(prim.safe_cosh, [float], float)
    pset.addPrimitive(math.tanh, [float], float)
    pset.addPrimitive(math.atan, [float], float)
    pset.addPrimitive(math.hypot, [float, float], float)
    pset.addPrimitive(abs, [float], float)
    pset.addPrimitive(prim.abs_sqrt, [float], float)
    pset.addPrimitive(prim.parab, [float], float)
    pset.addPrimitive(prim.avg_sum, [float, float], float)
    pset.addPrimitive(prim.sign, [float], float)
    pset.addPrimitive(prim.mdist, [float, float], float)

    # Noise
    pset.addPrimitive(prim.simplex2, [float, float], float)
    pset.addPrimitive(prim.perlin2, [float, float], float)
    pset.addPrimitive(prim.perlin1, [float], float)

    # Plasma
    pset.addPrimitive(prim.plasma, [float, float, float, float], float)

    # Constants
    pset.addTerminal(1.6180, float)  # Golden ratio
    pset.addTerminal(math.pi, float)
    pset.addEphemeralConstant('Rand', Rand.func, float)

    pset.renameArguments(ARG0="x")
    pset.renameArguments(ARG1="y")
    return pset


def create_sample_pset(bw=True, sample_size=8):
    """Create a sampled pset from all primitives.
    """
    if bw:
        pset = deap.gp.PrimitiveSetTyped("main", [float, float], float)
    else:
        pset = deap.gp.PrimitiveSetTyped("main", [float, float], list)
        pset.addPrimitive(prim.combine, [float, float, float], list)

    # All psets will have basic math and constants

    # Basic math
    pset.addPrimitive(operator.mul, [float, float], float)
    pset.addPrimitive(prim.safe_div, [float, float], float)
    pset.addPrimitive(operator.add, [float, float], float)
    pset.addPrimitive(operator.sub, [float, float], float)
    pset.addPrimitive(prim.safe_mod, [float, float], float)

    # Constants
    pset.addTerminal(1.6180, float)  # Golden ratio
    pset.addTerminal(math.pi, float)
    pset.addEphemeralConstant('Rand', Rand.func, float)

    # Other primitives are sampled from the defined primitive set.
    keys = list(PRIMITIVES.keys())
    random.shuffle(keys)
    sample_keys = keys[:sample_size]
    for k in sample_keys:
        p = PRIMITIVES[k]
        pset.addPrimitive(p[0], p[1], p[2])

    pset.renameArguments(ARG0="x")
    pset.renameArguments(ARG1="y")
    return pset, sample_keys


def _valid_ind(ind, max_val):
    return ind.height <= max_val


def subtree_mutate(individual, pset, expr):
    """Choose a random node and generate a subtree to that node using *pset* and *expr*.
    """
    mut_ind = copy.deepcopy(individual)
    while True:
        mutated, = deap.gp.mutUniform(mut_ind, expr, pset)
        if _valid_ind(mutated, GP_TREE_MAX_DEPTH):
            return mutated

        mut_ind = copy.deepcopy(individual)


def mate_limit(ind1, ind2):
    keep_indices = [copy.deepcopy(ind) for ind in [ind1, ind2]]
    new_indices = list(deap.gp.cxOnePoint(ind1, ind2))
    for i, ind in enumerate(new_indices):
        if not _valid_ind(ind, GP_TREE_MAX_DEPTH):
            new_indices[i] = random.choice(keep_indices)
    return new_indices


def create_toolbox(pset):
    """Creates a DEAP toolbox with some reasonable defaults:

    * ``toolbox.expr`` creates new individuals with :func:`deap.gp.genHalfAndHalf` with depth in [2, 6].
    * ``toolbox.mate`` Uses :func:`deap.gp.cxOnePoint` enforcing :attr:`GP_TREE_MAX_DEPTH`
    * ``toolbox.mutate`` Uses :func:`deap.gp.mutUniform` enforcing :attr:`GP_TREE_MAX_DEPTH`
    * ``toolbox.select`` Uses :func:`deap.tools.selDoubleTournament` with
      ``fitness_size=3, parsimony_size=1.4, fitness_first=True``

    :param pset: Primitive set
    :returns: :class:`deap.base.Toolbox`
    """
    toolbox = deap.base.Toolbox()
    toolbox.register("expr", deap.gp.genHalfAndHalf, pset=pset, min_=2, max_=6)
    toolbox.register("expr_mut", deap.gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
    toolbox.register("mate", mate_limit)
    toolbox.register("mutate", subtree_mutate, expr=toolbox.expr_mut)
    toolbox.register("select", deap.tools.selDoubleTournament, fitness_size=3,
                     parsimony_size=1.4, fitness_first=True)
    return toolbox
