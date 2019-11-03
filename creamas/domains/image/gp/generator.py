"""Generator creating evolutionary art using genetic programming.

The generated artifacts are instances of :class:`GPImageArtifact`.
"""
import random

import deap
import deap.base
import deap.creator
import deap.gp
import deap.tools

import numpy as np

from creamas.util import sanitize_agent_name
from creamas.domains.image.gp.artifact import GPImageArtifact


class GPImageGenerator:
    """A generator class producing instances of :class:`GPImageArtifact` using genetic programming.

    The generator uses `DEAP <https://deap.readthedocs.io/en/master/>`_ in its internal operation.

    Generator class can be used in two different manners:

        * calling only the static functions of the class, or
        * creating a new instance of the class associated with a specific agent and calling
          :meth:`GPImageGenerator.generate`.
    """
    def __init__(self, creator_name, toolbox, pset, generations, pop_size, evaluate_func, shape=(32, 32),
                 super_pset=None):
        """
        Most of the initialization arguments are used as defaults in the calls for
        :meth:`~creamas.domains.image.gp.GPImageGenerator.generate`, and can be overridden when using it.

        :param str creator_name:
            Name of the creator agent used by :meth:`generate` as a default.
        :param toolbox:
            DEAP's toolbox used by :meth:`generate` as a default.
        :param pset:
            DEAP's primitive set which is used to create the images.
        :param generations:
            Number of generations to evolve
        :param pop_size:
            Population size.
        :param shape:
            Shape of the produced images during the evolution. The resolution can be (indefinitely)
            up-scaled for the accepted artifacts.
        :param callable evaluate_func:
            A function used to evaluate each image, e.g. :meth:`~creamas.core.agent.CreativeAgent.evaluate`
            Function should accept one argument, a :class:`GPImageArtifact` and return an evaluation
            of an artifact. Evaluation is supposed to be maximized.
        :param super_pset:
            In a case an agent may create artifacts in conjunction with other agents, ``super_pset`` should contain all
            the primitives all the agents may use. If ``None``, this is set to ``pset``.
        """
        self.creator_name = creator_name
        self.pset = pset
        self.generations = generations
        self.pop_size = pop_size
        self.shape = shape
        self.evaluate_artifact = evaluate_func
        self.super_pset = super_pset if super_pset is not None else pset
        self.toolbox = toolbox
        self.class_suffix = "_" + sanitize_agent_name(self.creator_name)
        self.fitness_class, self.individual_class = GPImageGenerator.init_deap_creator(self.class_suffix, self.pset)

    @staticmethod
    def individual_to_artifact(creator_name, individual, shape, pset=None, bw=True):
        """Convert DEAP´s ``individual`` to :class:`GPImageArtifact`.

        This will create the inherent image object, if it is not already present in the
        ``individual``. If individual has already an image associated with it, that image is used
        and ``shape`` and ``bw`` parameters are omitted.

        Fails silently if the image creation does not succeed, i.e. ``deap.gp.compile`` fails for the given individual
        and pset, and returns ``None``.

        :param str creator_name:
            Name of the creator of the image.
        :param individual:
            Function (DEAP´s individual) of the image.
        :param shape:
            Shape of the returned image.
        :param pset:
            DEAP's primitive set used to compile the individual.
        :param bw:
            If ``True``, the individual is assumed to represent grayscale image, otherwise it is assumed to
            be an RGB image.
        :returns:
            :class:`GPImageArtifact` or ``None``
        """
        if individual.image is None:
            try:
                func = deap.gp.compile(individual, pset)
            except MemoryError:
                import traceback
                print(traceback.format_exc())
                return None
            image = GPImageArtifact.image_from_function(func, shape, bw=bw)
            individual.image = image

        artifact = GPImageArtifact(creator_name, individual.image, individual, str(individual))
        return artifact

    def evaluate_individual(self, individual, shape):
        """Evaluates a DEAP individual.

        This method inherently changes the individual to :class:`GPImageArtifact` for
        the evaluation.

        :param individual:
            The individual to be evaluated.
        :param shape:
            Shape of the image.
        :returns:
            The evaluation.
        """
        pset = self.super_pset
        artifact = GPImageGenerator.individual_to_artifact(self.creator_name, individual, shape, pset)

        if artifact is None:
            return -1,

        return self.evaluate_artifact(artifact)

    @staticmethod
    def init_deap_creator(class_suffix, pset):
        """Initializes the DEAP :class:`deap.creator` by creating classes which use the wanted primitive set to
        maximize fitness.

        The created classes are found from :py:mod:`deap.creator` with names ``FitnessMax-[class_suffix]`` and
        ``Individual-[class_suffix]`` using, e.g. ``getattr(deap.creat or, "FitnessMax-{}".format(class_suffix))``.
        The method should be called only once per ``class_suffix`` as subsequent calls will erase previously created
        classes.

        :param str class_suffix: Suffix for the created fitness and individual classes.
        :param pset: Primitive set used by the individual creator.
        :returns: Created classes
        """
        fitness_class_name = "FitnessMax{}".format(class_suffix)
        individual_class_name = "Individual{}".format(class_suffix)
        deap.creator.create(fitness_class_name, deap.base.Fitness, weights=(1.0,))
        fitness_class = getattr(deap.creator, fitness_class_name)
        deap.creator.create(individual_class_name, deap.gp.PrimitiveTree, fitness=fitness_class, pset=pset, image=None)
        individual_class = getattr(deap.creator, individual_class_name)

        return fitness_class, individual_class

    @staticmethod
    def create_population(size, pset, generation_method, individual_creator=None, toolbox=None):
        """Creates a population of randomly generated individuals.

        :param size:
            The size of the generated population.
        :param pset:
            The primitive set used in individual generation.
        :param generation_method:
            Generation method to create individuals, e.g.
            :meth:`deap.gp.genHalfAndHalf`.
        :param individual_creator:
            If ``None`` calls :func:`~creamas.domains.image.gp.generator.GPImageGenerator.init_deap_creator` with class
            suffix "".
        :param toolbox:
            DEAP toolbox. If ``None`` a new toolbox is created.
        :return:
            DEAP toolbox and a list containing the generated population as DEAP individuals.
        """
        if individual_creator is None:
            _, individual_creator = GPImageGenerator.init_deap_creator("", pset)
        if toolbox is None:
            toolbox = deap.base.Toolbox()
        if not hasattr(toolbox, 'expr'):
            toolbox.register("expr", generation_method, pset=pset, min_=2, max_=6)
        if not hasattr(toolbox, 'individual'):
            toolbox.register("individual", deap.tools.initIterate, individual_creator, toolbox.expr)
        if not hasattr(toolbox, 'population'):
            toolbox.register("population", deap.tools.initRepeat, list, toolbox.individual)
        return toolbox, toolbox.population(size)

    @staticmethod
    def initial_population(toolbox, pset, pop_size, individual_creator=None, old_artifacts=[], mutate_old=True):
        """Create initial population for new evolution.

        Population is formed by first creating individuals from *old_artifacts* and then the rest of the population
        is generated using :func:`deap.gp.genHalfAndHalf` with given *pset*.

        :param toolbox:
            DEAP toolbox.
        :param pset:
            Primitive set for the population's new individuals.
        :param pop_size:
            Size of the population.
        :param individual_creator:
            Class used to create new individuals, if ``None`` tries to use ``deap.creator.Individual``.
        :param list old_artifacts:
            A list of existing :class:`~creamas.domains.image.gp.artifact.GPImageArtifact` objects, which should be
            part of the initial population. Each artifact in the list should have the function tree for the individual
            stored in ``artifact.framings['function_tree']``.
        :param bool mutate_old:
            If ``True``, forces mutation on the existing individuals from.
        :return: Created population
        """
        if individual_creator is None:
            individual_creator = deap.creator.Individual

        population = []
        for artifact in old_artifacts[:pop_size]:
            # Super individual has all primitives, so no need to call
            # agent specific individual creator (with agent specific
            # pset).
            individual = individual_creator(artifact.framings['function_tree'])
            # Force mutate artifacts from the memory
            if mutate_old:
                toolbox.mutate(individual, pset)
                del individual.fitness.values
                if individual.image is not None:
                    del individual.image
            population.append(individual)

        if len(population) < pop_size:
            toolbox, pop = GPImageGenerator.create_population(pop_size - len(population), pset, deap.gp.genHalfAndHalf,
                                                              individual_creator, toolbox)
            population += pop
        return population

    @staticmethod
    def _crossover_and_mutate(offspring, toolbox, pset, cxpb, mutpb):
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if np.random.random() < cxpb:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
                if child1.image is not None:
                    del child1.image
                if child2.image is not None:
                    del child2.image

        for mutant in offspring:
            if np.random.random() < mutpb:
                toolbox.mutate(mutant, pset)
                del mutant.fitness.values
                if mutant.image is not None:
                    del mutant.image

    @staticmethod
    def evolve_population(population, generations, toolbox, pset, hall_of_fame,
                          cxpb=0.75, mutpb=0.25, injected_individuals=[],
                          use_selection_on_first=True):
        """Evolves a population of individuals. Applies elitist selection strategy (k=1) in addition
        to toolbox's selection strategy to the individuals.

        :param population: A list containing the individuals of the population.
        :param generations: Number of generations to be evolved.
        :param toolbox: DEAP toolbox with the necessary functions.
        :param pset: DEAP primitive set used during the evolution.
        :param hall_of_fame: DEAP's hall-of-fame
        :param float cxpb: Crossover probability
        :param float mutpb: Mutation probability
        :param list injected_individuals: A list of individuals which are injected into the starting population
        :param bool use_selection_on_first:
            If ``True``, uses selection on the first generation before producing offspring, otherwise produces offspring
            from the
        """
        pop_len = len(population)
        population += injected_individuals
        fitnesses = map(toolbox.evaluate, population)
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        hall_of_fame.update(population)

        for g in range(generations):
            if not use_selection_on_first and g == 0:
                offspring = list(map(toolbox.clone, population))
            else:
                # Select the next generation individuals with elitist (k=1) and
                # toolboxes selection method
                offspring = deap.tools.selBest(population, 1)
                offspring += toolbox.select(population, pop_len - 1)
                # Clone the selected individuals
                offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            GPImageGenerator._crossover_and_mutate(offspring, toolbox, pset, cxpb, mutpb)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            population[:] = offspring
            random.shuffle(population)
            # Update hall of fame with new population.
            hall_of_fame.update(population)

    def generate(self, artifacts=1, generations=None, pset=None, pop_size=None, shape=None,
                 old_artifacts=[], mutate_old=True):
        """
        Generate new artifacts using instance's own toolbox and given arguments.

        :param int artifacts:
            The number of the most fit artifacts to be returned.
        :param int generations:
            Number of generations to be evolved. If ``None`` uses initialization parameters.
        :param pset:
            DEAP's primitive set used to create the individuals.
        :param int pop_size:
            DEAP population size
        :param tuple shape:
            Shape of the created images. This heavily affects the execution time.
        :param list old_artifacts:
            A list of existing :class:`~creamas.domains.image.gp.artifact.GPImageArtifact` objects, which should be
            part of the initial population. Each artifact in the list should have the function tree for the individual
            stored in ``artifact.framings['function_tree']``.
        :param bool mutate_old:
            If ``True``, forces mutation on the existing individuals from.
        :return:
            A list of generated :class:`GPImageArtifact` objects. The artifacts returned do not
            have their framing information (evaluation, etc.) filled.
        """
        # Initialize parameters
        generations = generations if generations is not None else self.generations
        pset = pset if pset is not None else self.pset
        pop_size = pop_size if pop_size is not None else self.pop_size
        shape = shape if shape is not None else self.shape
        hall_of_fame = deap.tools.HallOfFame(artifacts)

        # Create initial population
        population = GPImageGenerator.initial_population(self.toolbox,
                                                         pset,
                                                         pop_size,
                                                         self.individual_class,
                                                         old_artifacts,
                                                         mutate_old)
        self.toolbox.register("evaluate", self.evaluate_individual, shape=shape)
        # Evolve population for the number of generations.
        GPImageGenerator.evolve_population(population, generations, self.toolbox, pset, hall_of_fame)
        arts = []
        for ft in hall_of_fame:
            print(type(ft))
            artifact = GPImageArtifact(self.creator_name, ft.image, ft, str(ft))
            arts.append((artifact, None))
        return arts


if __name__ == "__main__":
    from creamas.domains.image.features import ImageSymmetryFeature, ImageEntropyFeature, ImageBenfordsLawFeature
    from creamas.domains.image.gp import tools
    from creamas.domains.image import gp
    pset = tools.create_super_pset()
    toolbox = tools.create_toolbox(pset)

    feat = ImageSymmetryFeature(ImageSymmetryFeature.ALL_AXES)
    feat2 = ImageEntropyFeature(normalize=True)
    feat3 = ImageBenfordsLawFeature()

    def evaluate_func(artifact):
        if gp.GPImageArtifact.png_compression_ratio(artifact) <= 0.08:
            return 0.0, None
        return feat(artifact) * 2 + feat2(artifact), None

    gpgen = gp.GPImageGenerator('name', toolbox, pset, 4, 3, evaluate_func, (32, 32))
    arts = gpgen.generate()
    art = arts[0][0]
    img = art.obj
    print(art.framings)
    #gp.GPImageArtifact.save(art, 'test_image.png', pset, shape=(100, 100), string_file='test_image.txt')

    #art2 = gp.GPImageArtifact.artifact_from_file('creator_name', 'test_image.txt', pset, (32, 32), bw=True)
    #print(art2.framings['string_repr'])
    #img2 = art2.obj
    #print(art2.framings)
    #print(art2.framings['string_repr'] == art.framings['string_repr'])
