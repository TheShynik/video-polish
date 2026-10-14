# Video Polish: preserve approved local-native-v1

- `main` and tag `local-native-v1` are the user-approved stable snapshot. Never rewrite/move that tag or commit experiments on `main`.
- Before experimental edits, verify the current Git branch. Use `experiments/after-local-native-v1` or create a dedicated branch from `local-native-v1`.
- Never overwrite/delete `local_native_v1_assets`, the approved `reference_detail_test/local_native_60fps.mp4`, or their exact inputs. Experiments and reproductions use fresh output directories and isolated environments.
- Models, video/image assets, environments and upstream checkouts remain outside Git. Review staged filenames and sizes before committing. Extend the explicit `.gitignore` allow-list for new experimental source only on the experiment branch.
- Stable reproduction instructions and hash manifest are in `stable_local_native/README.md` and `stable_local_native/manifest.json`.
- A change on an experimental branch does not change the stable Git snapshot, but Git does not isolate ignored assets. Preserve the external stable assets explicitly.
