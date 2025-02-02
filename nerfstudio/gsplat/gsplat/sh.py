"""Python bindings for SH"""

from jaxtyping import Float
from torch import Tensor
from torch.autograd import Function

import nerfstudio.gsplat.gsplat.cuda as _C


def num_sh_bases(degree: int):
    if degree == 0:
        return 1
    if degree == 1:
        return 4
    if degree == 2:
        return 9
    if degree == 3:
        return 16
    return 25


def deg_from_sh(num_bases: int):
    if num_bases == 1:
        return 0
    if num_bases == 4:
        return 1
    if num_bases == 9:
        return 2
    if num_bases == 16:
        return 3
    if num_bases == 25:
        return 4
    assert False, "Invalid number of SH bases"


class SphericalHarmonics(Function):
    """Compute spherical harmonics

    Args:
        degrees_to_use (int): degree of SHs to use (<= total number available).
        viewdirs (Tensor): viewing directions.
        coeffs (Tensor): harmonic coefficients.
    """

    @staticmethod
    def forward(
        ctx,
        degrees_to_use: int,
        viewdirs: Float[Tensor, "*batch 3"],
        coeffs: Float[Tensor, "*batch D C"],
    ):
        num_points = coeffs.shape[0]
        assert coeffs.shape[-2] >= num_sh_bases(degrees_to_use)
        ctx.degrees_to_use = degrees_to_use
        degree = deg_from_sh(coeffs.shape[-2])
        ctx.degree = degree
        ctx.save_for_backward(viewdirs)
        return _C.compute_sh_forward(
            num_points, degree, degrees_to_use, viewdirs, coeffs
        )

    @staticmethod
    def backward(ctx, v_colors: Float[Tensor, "*batch 3"]):
        degrees_to_use = ctx.degrees_to_use
        degree = ctx.degree
        viewdirs = ctx.saved_tensors[0]
        num_points = v_colors.shape[0]
        return (
            None,
            None,
            _C.compute_sh_backward(
                num_points, degree, degrees_to_use, viewdirs, v_colors
            ),
        )
