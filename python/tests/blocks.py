import copy

import numpy as np
import pytest
from numpy.testing import assert_equal

import equistore
import equistore.status
from equistore import Labels, TensorBlock


@pytest.fixture
def block():
    return TensorBlock(
        values=np.full((3, 2), -1.0),
        samples=Labels(["s"], np.array([[0], [2], [4]])),
        components=[],
        properties=Labels(["p"], np.array([[5], [3]])),
    )


def test_gradient_no_sample_error(block):
    msg = (
        "invalid parameter: gradients samples must have at least "
        "one dimension named 'sample', we got none"
    )
    with pytest.raises(equistore.status.EquistoreError, match=msg):
        block.add_gradient(
            "g",
            data=np.zeros((0, 2)),
            samples=Labels([], np.empty((0, 2))),
            components=[],
        )


def test_repr(block):
    expected = """TensorBlock
    samples (3): ['s']
    components (): []
    properties (2): ['p']
    gradients: no"""
    assert block.__repr__() == expected


def test_repr_zero_samples():
    block = TensorBlock(
        values=np.zeros((0, 2)),
        samples=Labels([], np.empty((0, 2))),
        components=[],
        properties=Labels(["p"], np.array([[5], [3]])),
    )
    expected = """TensorBlock
    samples (0): []
    components (): []
    properties (2): ['p']
    gradients: no"""
    assert block.__repr__() == expected


def test_repr_zero_samples_gradient(block):
    block.add_gradient(
        "g",
        data=np.zeros((0, 2)),
        samples=Labels(["sample"], np.empty((0, 2))),
        components=[],
    )

    expected_block = """TensorBlock
    samples (3): ['s']
    components (): []
    properties (2): ['p']
    gradients: ['g']"""

    assert block.__repr__() == expected_block

    expected_grad = """Gradient TensorBlock
parameter: 'g'
samples (0): ['sample']
components (): []
properties (2): ['p']"""

    gradient = block.gradient("g")
    assert gradient.__repr__() == expected_grad


def test_block_no_components(block):
    assert_equal(block.values, np.full((3, 2), -1.0))

    assert block.samples.names == ("s",)
    assert len(block.samples) == 3
    assert tuple(block.samples[0]) == (0,)
    assert tuple(block.samples[1]) == (2,)
    assert tuple(block.samples[2]) == (4,)

    assert len(block.components) == 0

    assert block.properties.names == ("p",)
    assert len(block.properties) == 2
    assert tuple(block.properties[0]) == (5,)
    assert tuple(block.properties[1]) == (3,)


@pytest.fixture
def block_components():
    return TensorBlock(
        values=np.full((3, 3, 2, 2), -1.0),
        samples=Labels(["s"], np.array([[0], [2], [4]])),
        components=[
            Labels(["c_1"], np.array([[-1], [0], [1]])),
            Labels(["c_2"], np.array([[-4], [1]])),
        ],
        properties=Labels(["p"], np.array([[5], [3]])),
    )


def test_block_with_components(block_components):
    expected = """TensorBlock
    samples (3): ['s']
    components (3, 2): ['c_1', 'c_2']
    properties (2): ['p']
    gradients: no"""
    assert block_components.__repr__() == expected

    assert_equal(block_components.values, np.full((3, 3, 2, 2), -1.0))

    assert block_components.samples.names == ("s",)
    assert len(block_components.samples) == 3
    assert tuple(block_components.samples[0]) == (0,)
    assert tuple(block_components.samples[1]) == (2,)
    assert tuple(block_components.samples[2]) == (4,)

    assert len(block_components.components) == 2
    component_1 = block_components.components[0]
    assert component_1.names == ("c_1",)
    assert len(component_1) == 3
    assert tuple(component_1[0]) == (-1,)
    assert tuple(component_1[1]) == (0,)
    assert tuple(component_1[2]) == (1,)

    component_2 = block_components.components[1]
    assert component_2.names == ("c_2",)
    assert len(component_2) == 2
    assert tuple(component_2[0]) == (-4,)
    assert tuple(component_2[1]) == (1,)

    assert block_components.properties.names, ("p",)
    assert len(block_components.properties) == 2
    assert tuple(block_components.properties[0]) == (5,)
    assert tuple(block_components.properties[1]) == (3,)


def test_gradients(block_components):
    block_components.add_gradient(
        "g",
        data=np.full((2, 3, 2, 2), 11.0),
        samples=Labels(["sample", "g"], np.array([[0, -2], [2, 3]])),
        components=[
            Labels(["c_1"], np.array([[-1], [0], [1]])),
            Labels(["c_2"], np.array([[-4], [1]])),
        ],
    )

    expected = """TensorBlock
    samples (3): ['s']
    components (3, 2): ['c_1', 'c_2']
    properties (2): ['p']
    gradients: ['g']"""
    assert block_components.__repr__() == expected

    assert block_components.has_gradient("g")
    assert not block_components.has_gradient("something_else")
    assert not block_components.has_gradient("something else")

    assert block_components.gradients_list() == ["g"]

    gradient = block_components.gradient("g")

    expected_grad = """Gradient TensorBlock
parameter: 'g'
samples (2): ['sample', 'g']
components (3, 2): ['c_1', 'c_2']
properties (2): ['p']"""
    assert gradient.__repr__() == expected_grad

    assert gradient.samples.names == ("sample", "g")
    assert len(gradient.samples) == 2
    assert tuple(gradient.samples[0]) == (0, -2)
    assert tuple(gradient.samples[1]) == (2, 3)

    assert_equal(gradient.data, np.full((2, 3, 2, 2), 11.0))


def test_copy():
    block = TensorBlock(
        values=np.full((3, 3, 2), 2.0),
        samples=Labels(["s"], np.array([[0], [2], [4]])),
        components=[
            Labels(["c_1"], np.array([[-1], [0], [1]])),
        ],
        properties=Labels(["p"], np.array([[5], [3]])),
    )

    # using TensorBlock.copy
    clone = block.copy()
    block_values_id = id(block.values)

    del block

    assert id(clone.values) != block_values_id

    assert_equal(clone.values, np.full((3, 3, 2), 2.0))
    assert clone.samples.names == ("s",)
    assert len(clone.samples) == 3
    assert tuple(clone.samples[0]) == (0,)
    assert tuple(clone.samples[1]) == (2,)
    assert tuple(clone.samples[2]) == (4,)

    # using copy.deepcopy
    other_clone = clone.copy()
    block_values_id = id(clone.values)

    del clone

    assert id(other_clone.values) != block_values_id
    assert_equal(other_clone.values, np.full((3, 3, 2), 2.0))


def test_shallow_copy_error(block):
    msg = "shallow copies of TensorBlock are not possible, use a deepcopy instead"
    with pytest.raises(ValueError, match=msg):
        copy.copy(block)


def test_eq(block):
    assert equistore.equal_block(block, block) == (block == block)


def test_neq(block, block_components):
    assert equistore.equal_block(block, block_components) == (block == block_components)
