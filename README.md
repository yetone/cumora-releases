# cumora-releases

Public release archive for [Cumora](https://cumora.ai). This repo holds
the GitHub Releases (DMGs, ZIPs, installers, AppImages, auto-update
feeds) — no source code, no issue discussion.

- **Product site / downloads**: https://cumora.ai
- **Issues & discussion**: please file at the main repo
  ([yetone/cumora](https://github.com/yetone/cumora))

The `Release` workflow here is invoked by the main repo via
`repository_dispatch` whenever a `v*` tag is pushed. It builds the
Electron app for macOS (arm64 + Intel), Windows, and Linux, signs +
notarises the macOS binaries, uploads everything to the
`cumora-updates` R2 bucket (for the in-app auto-updater) and creates a
GitHub Release here.
