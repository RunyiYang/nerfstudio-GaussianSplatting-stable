import pytest
import torch


device = torch.device("cuda:0")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="No CUDA device")
def test_map_gaussians():
    from gsplat import _torch_impl
    from gsplat.map_gaussian_to_intersects import MapGaussiansToIntersects

    torch.manual_seed(42)

    num_points = 100

    means3d = torch.randn((num_points, 3), device=device, requires_grad=True)
    scales = torch.randn((num_points, 3), device=device)
    glob_scale = 0.3
    quats = torch.randn((num_points, 4), device=device)
    quats /= torch.linalg.norm(quats, dim=-1, keepdim=True)
    viewmat = torch.eye(4, device=device)
    projmat = torch.eye(4, device=device)
    fx, fy = 3.0, 3.0
    H, W = 512, 512
    clip_thresh = 0.01

    BLOCK_X, BLOCK_Y = 16, 16
    tile_bounds = (W + BLOCK_X - 1) // BLOCK_X, (H + BLOCK_Y - 1) // BLOCK_Y, 1

    (
        _cov3d,
        _xys,
        _depths,
        _radii,
        _conics,
        _num_tiles_hit,
        _masks,
    ) = _torch_impl.project_gaussians_forward(
        means3d,
        scales,
        glob_scale,
        quats,
        viewmat,
        projmat,
        fx,
        fy,
        (H, W),
        tile_bounds,
        clip_thresh,
    )
    _xys = _xys[_masks]
    _depths = _depths[_masks]
    _radii = _radii[_masks]
    _conics = _conics[_masks]
    _num_tiles_hit = _num_tiles_hit[_masks]

    num_points = num_points - torch.count_nonzero(~_masks).item()

    _cum_tiles_hit = torch.cumsum(_num_tiles_hit, dim=0, dtype=torch.int32)
    _num_intersects = _cum_tiles_hit[-1].item()
    _depths = _depths.contiguous()

    _isect_ids, _gaussian_ids = _torch_impl.map_gaussian_to_intersects(
        num_points, _xys, _depths, _radii, _cum_tiles_hit, tile_bounds
    )

    isect_ids, gaussian_ids = MapGaussiansToIntersects.apply(
        num_points, _num_intersects, _xys, _depths, _radii, _cum_tiles_hit, tile_bounds
    )

    torch.testing.assert_close(gaussian_ids, _gaussian_ids)
    torch.testing.assert_close(isect_ids, _isect_ids)


if __name__ == "__main__":
    test_map_gaussians()
