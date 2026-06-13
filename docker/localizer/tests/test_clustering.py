import numpy as np
from numpy.testing import assert_allclose

from src.localize import cluster_retrieved_images


class TestClusterRetrievedImages:
    def test_single_coherent_group_is_one_cluster(self):
        centers = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
        span, num_clusters, labels = cluster_retrieved_images(centers, 5.0)
        assert num_clusters == 1
        assert len(set(labels.tolist())) == 1
        assert_allclose(span, 2.0)

    def test_two_far_groups_split(self):
        centers = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [30.0, 0.0, 0.0], [31.0, 0.0, 0.0]])
        span, num_clusters, labels = cluster_retrieved_images(centers, 5.0)
        assert num_clusters == 2
        assert labels[0] == labels[1]
        assert labels[2] == labels[3]
        assert labels[0] != labels[2]
        assert_allclose(span, 31.0)

    def test_single_linkage_chains_through_intermediate(self):
        # First and last centers are 8m apart (beyond the 5m gap) but linked via the middle one.
        centers = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [8.0, 0.0, 0.0]])
        _, num_clusters, labels = cluster_retrieved_images(centers, 5.0)
        assert num_clusters == 1
        assert len(set(labels.tolist())) == 1

    def test_isolated_center_is_its_own_cluster(self):
        centers = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [50.0, 0.0, 0.0]])
        _, num_clusters, labels = cluster_retrieved_images(centers, 5.0)
        assert num_clusters == 2
        assert labels[0] == labels[1]
        assert labels[2] != labels[0]
