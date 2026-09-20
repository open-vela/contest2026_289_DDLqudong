# VelaMotion Coach 最终演示截图链路

生成时间：2026-09-20T04:00:51.617Z
有效画面哈希数：4

## 截图顺序

1. core_01_home.png — 首页 · 小芽运动伙伴与腕上初筛
2. core_02_coach.png — 腕上教练 · 前三候选与提醒
3. core_03_timeline.png — 动作时间线 · 自动分段与本地复盘
4. core_04_sync_review.png — 同步复盘 · 同步/历史/更多

实际模拟器截图串联，每页 10 秒；不是连续操作录屏。

## 视频产物

- velamotion_core_demo.mp4

```bash
# 在快应用工程根目录执行
ffmpeg -y -f concat -safe 0 -i artifacts/final_demo/auto_carousel/core_demo.ffconcat -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,format=yuv420p" -r 30 artifacts/final_demo/auto_carousel/velamotion_core_demo.mp4
```
