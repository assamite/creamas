"""
.. :py:module:: test_image
    :platform: Unix

Tests for image domain.
"""
import asyncio
import os
import unittest

from testfixtures import TempDirectory

import numpy as np

from creamas.core.artifact import Artifact
from creamas.core.environment import Environment

from creamas.domains.image import features
from creamas.domains.image.gp import tools
from creamas.domains.image import gp


class ImageTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()
        self.d = TempDirectory()
        self.td = self.d.path

    def tearDown(self):
        self.env.close()

    def test_features(self):
        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageComplexityFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageBenfordsLawFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageEntropyFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageSymmetryFeature(features.ImageSymmetryFeature.ALL_AXES)
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageRednessFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageBluenessFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageGreennessFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

        for _ in range(10):
            image = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
            artifact = Artifact('creator_name', image, domain='image')

            feat = features.ImageIntensityFeature()
            value = feat(artifact)
            self.assertEqual(type(value), float)

        artifact = Artifact('creator_name', image, domain='not image')
        value = feat(artifact)
        self.assertIs(value, None)

    def test_gp(self):

        pset = tools.create_super_pset()
        toolbox = tools.create_toolbox(pset)

        feat = features.ImageSymmetryFeature(features.ImageSymmetryFeature.ALL_AXES)

        def evaluate_func(artifact):
            if gp.GPImageArtifact.png_compression_ratio(artifact) <= 0.08:
                return 0.0, None
            return feat(artifact), None

        image_shape = (32, 32)
        gpgen = gp.GPImageGenerator('name', toolbox, pset, 10, 5, evaluate_func, image_shape)
        arts = gpgen.generate()
        art = arts[0][0]
        img = art.obj
        self.assertEqual(img.shape, image_shape)
        image_path = os.path.join(self.td, 'test_image.png')
        string_path = os.path.join(self.td, 'test_image.txt')
        gp.GPImageArtifact.save(art, image_path, pset, shape=(400, 400), string_file=string_path)

