# RoboLab Sample Videos

> [!NOTE]
> This folder intentionally contains only a few small MP4 samples for GitHub browsing. Full videos, HDF5 files, and raw episode logs stay on the RTX 4090 output disk.

| Video | Task | Size | Link | Note |
|---|---|---:|---|---|
| RoboLab-120 Pi05 full run sample: AnimalsInBinTask viewport | `AnimalsInBinTask` | 6.91 MB | [mp4](sample_videos/robolab120_animals_in_bin_viewport.mp4) | Viewport sample from the clean Pi05 full-120 run. Small enough for GitHub preview. |
| RoboLab-120 Pi05 full run sample: FruitsOnPlate3Task viewport | `FruitsOnPlate3Task` | 7.32 MB | [mp4](sample_videos/robolab120_fruits_on_plate3_viewport.mp4) | Viewport sample from the clean Pi05 full-120 run for a multi-object counting task. |
| Pi05 complex sample: Stack3RubiksCubeTask | `Stack3RubiksCubeTask` | 7.61 MB | [mp4](sample_videos/pi05_complex_stack3_rubiks_cube.mp4) | Complex stacking sample from the earlier Pi05 complex-task probe. |

## Evidence Boundary

- These videos are visual samples from the reproduction workflow, not the final RoboLab-120 score table.
- The final full-120 report should be based on `episode_results.jsonl`, artifact checks, HDF5 logs, and regenerated analysis tables after the manifest reaches 120/120.
- Keep only a small number of videos in Git. Complete video archives should use release artifacts or object storage.
