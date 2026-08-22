# Release Checklist for the SPDX Online Tools

- [ ] Update the `spdx_online_tools_version` in the file src/config/version.py
- [ ] Update the `[VERSION]` in `image: 410487266669.dkr.ecr.us-west-2.amazonaws.com/spdx/online-tools:[VERSION]`
- [ ] Run unit tests locally
- [ ] Run the development docker image and verify that the Validate command, Conformance command, License check and License submit functions work properly
- [ ] Update production per the [README-PRODUCTION.md](README-PRODUCTION.md) file
- [ ] Tag the release
- [ ] Create a Git release
- [ ] Email community that a new release is available