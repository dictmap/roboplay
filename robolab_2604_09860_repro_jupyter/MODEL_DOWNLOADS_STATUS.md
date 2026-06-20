# Model Download Status

| Model | Path | Size | Status |
|---|---|---:|---|
| Cosmos Reason1 7B | /data/light/roboplay_models/cosmos/cosmos_reason1_7b_full | 16G | complete/full |
| Cosmos Policy LIBERO Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_libero_predict2_2b_full | 3.7G | complete/full |
| Cosmos Predict2.5 2B | /data/light/roboplay_models/cosmos/cosmos_predict2_5_2b_metadata | 56K | metadata only |
| Cosmos Reason2 2B | /data/light/roboplay_models/cosmos/cosmos_reason2_2b_full | 64K | blocked: HF gated access required |
| Cosmos Reason2 8B | /data/light/roboplay_models/cosmos/cosmos_reason2_8b_full | 64K | blocked: HF gated access required |
| Cosmos Policy ALOHA Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_aloha_predict2_2b_full | 1.6G | prefetch running via hf-mirror |
| Cosmos Policy ALOHA Planning Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_aloha_planning_predict2_2b_full | missing | pending |
| Cosmos Policy RoboCasa Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_robocasa_predict2_2b_full | missing | pending |
| GR00T N1.5 3B | /data/light/roboplay_models/open_model_baselines/groot_n1_5_3b_full | 5.1G | complete/full |
| Qwen2.5-VL 3B Instruct | /data/light/roboplay_models/open_model_baselines/qwen2_5_vl_3b_instruct_full | 7.1G | complete/full |
| Qwen2.5-VL 7B Instruct | /data/light/roboplay_models/open_model_baselines/qwen2_5_vl_7b_instruct_metadata | 12M | metadata only |
| PaliGemma2 3B PT 224 | /data/light/roboplay_models/open_model_baselines/paligemma2_3b_pt_224_full | 56K | incomplete: README only |

Cosmos policy prefetch uses `HF_ENDPOINT=https://hf-mirror.com`; Reason2 repos currently return HF gated-access errors and need account authorization before full download.
