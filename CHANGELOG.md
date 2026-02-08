# CHANGELOG

<!-- version list -->

## v0.1.1 (2026-02-08)

### Bug Fixes

- **cd**: Run uv build on host runner instead of inside PSR Docker container
  ([`8e2b24e`](https://github.com/igrybkov/omnifocus-mcp/commit/8e2b24ecde1641817075c82d18b82f964d2ee47a))

- **search**: Add due_before/due_after filters and comprehensive input validation
  ([`ac23adc`](https://github.com/igrybkov/omnifocus-mcp/commit/ac23adc28b519055beae003d16b95286940b5bc8))


## v0.1.0 (2026-02-08)

### Bug Fixes

- **omnijs**: Populate project folder metadata in browse and search
  ([`7a847be`](https://github.com/igrybkov/omnifocus-mcp/commit/7a847be2d22cf9b0fd12be080e0f2b18941f361b))

- **search**: Repair broken filters and add completed_after/completed_before
  ([`955fd7f`](https://github.com/igrybkov/omnifocus-mcp/commit/955fd7f0cdb20b4ef720cc5ea9984c57ccf819f2))

- **tasks**: Use OmniJS for task status changes to support inbox tasks
  ([`6648383`](https://github.com/igrybkov/omnifocus-mcp/commit/6648383f82c5756c35c3ed50acd315f4f07a0100))

### Chores

- Add Claude Code project settings
  ([`c543459`](https://github.com/igrybkov/omnifocus-mcp/commit/c543459d06d824705c27a607b66a8135cb1f967f))

- Add ruff and pre-commit dev dependencies with config
  ([`c088e3d`](https://github.com/igrybkov/omnifocus-mcp/commit/c088e3df4fb52115cbe07b05d8ce87099092c4c6))

### Code Style

- Apply ruff formatting across codebase
  ([`b49de31`](https://github.com/igrybkov/omnifocus-mcp/commit/b49de314ff5cd48edd17ba9b39cb3eb23cd9c4e1))

### Continuous Integration

- Add GitHub Actions workflow and pre-commit hooks
  ([`0e95131`](https://github.com/igrybkov/omnifocus-mcp/commit/0e951312fdcf31ff236612c158d25d35bc0dd39f))

- Add Renovate configuration for automated dependency updates
  ([`a72d669`](https://github.com/igrybkov/omnifocus-mcp/commit/a72d6697fcbd6582930287ecb7d2c8eba52c67e5))

- **release**: Integrate python-semantic-release for automated releases
  ([`a622f73`](https://github.com/igrybkov/omnifocus-mcp/commit/a622f732a071abba9ba24e29f7be240f81614a71))

### Documentation

- Add AI authorship disclaimer to README
  ([`98a7bfc`](https://github.com/igrybkov/omnifocus-mcp/commit/98a7bfcfe15bc30612fdf7ebd11a0085029ea2c8))

- Add CLAUDE.md for Claude Code guidance
  ([`d269a49`](https://github.com/igrybkov/omnifocus-mcp/commit/d269a4956aad83237e10c4955bd5b454130d1cfc))

- Add CLI usage documentation to CLAUDE.md
  ([`18fc9af`](https://github.com/igrybkov/omnifocus-mcp/commit/18fc9afc589c577ec412da91aae85f635ca47bf8))

- Document shared utility patterns in CLAUDE.md
  ([`790a584`](https://github.com/igrybkov/omnifocus-mcp/commit/790a584c76d44f83f1d3802d361ddcd7062bdb20))

- Remove FastMCP references from documentation
  ([`39c2c5f`](https://github.com/igrybkov/omnifocus-mcp/commit/39c2c5ff3f7a1dc0bcc1e37e32610cc900cb546f))

- Update CLAUDE.md for renamed search and browse tools
  ([`d963f79`](https://github.com/igrybkov/omnifocus-mcp/commit/d963f79da93a0b9178a976b2b962eaaac4d343ea))

- **readme**: Rewrite with improved structure and examples
  ([`455c361`](https://github.com/igrybkov/omnifocus-mcp/commit/455c3612b9e7ac22ded2bb68089aac3e1f097dcb))

- **search**: Document aggregation patterns and use cases
  ([`b101d99`](https://github.com/igrybkov/omnifocus-mcp/commit/b101d99efb88265a1c5c91a2fe9bed6442e2611d))

### Features

- Add batch operations for bulk task/project management
  ([`d6a9472`](https://github.com/igrybkov/omnifocus-mcp/commit/d6a94724f6ec27ca1c0f6cbc1386d170a4f63df8))

- Add infrastructure utilities for dates, tags, and OmniJS
  ([`229c557`](https://github.com/igrybkov/omnifocus-mcp/commit/229c5577febfdc41288992c634befbd933236eca))

- Add perspective tools for OmniFocus views
  ([`60f5bd7`](https://github.com/igrybkov/omnifocus-mcp/commit/60f5bd772f62f3fbfbc2a10e64210ff3431d7aef))

- Add query_omnifocus tool for efficient database queries
  ([`cf781e3`](https://github.com/igrybkov/omnifocus-mcp/commit/cf781e36facb5e50b80a1891e92432eb1c504b48))

- Enhance existing tools with full OmniFocus properties
  ([`294a22b`](https://github.com/igrybkov/omnifocus-mcp/commit/294a22b1b8ff4cb59fcc17268f52931f4b536a70))

- Register new tools in server (9 standard, 10 expanded)
  ([`21141b5`](https://github.com/igrybkov/omnifocus-mcp/commit/21141b573bccf960713947c54cf4993dc2f7d949))

- **cli**: Add add-server command for easy MCP config setup
  ([`b6a699d`](https://github.com/igrybkov/omnifocus-mcp/commit/b6a699d525364767a42daf20d0b6577027b5a3c2))

- **cli**: Add command-line interface for MCP tools
  ([`af23429`](https://github.com/igrybkov/omnifocus-mcp/commit/af2342970e162a5973bbe11e0586823c4f7f7419))

- **core**: Add shared AppleScript builder and response utilities
  ([`63c4e9e`](https://github.com/igrybkov/omnifocus-mcp/commit/63c4e9e010fb715ef2216c0d7665c237ce145dfd))

- **edit**: Add new_parent_id parameter to change task parent
  ([`a951263`](https://github.com/igrybkov/omnifocus-mcp/commit/a951263d88ebe2086f2957c9e88a51dc8212ca01))

- **omnijs**: Add includes parameter for script composition
  ([`dbfa83c`](https://github.com/igrybkov/omnifocus-mcp/commit/dbfa83cfdd38d0fa43363ca14085360334c6e390))

- **perspectives**: Add get_perspective_rules tool
  ([`2898d82`](https://github.com/igrybkov/omnifocus-mcp/commit/2898d825c01f9accd796993a55797a92a5ec0dd6))

- **perspectives**: Implement custom perspective content access
  ([`bf341b6`](https://github.com/igrybkov/omnifocus-mcp/commit/bf341b6bcdfe099b5132fe7e13e2b6f57262cddc))

- **perspectives**: Include note in default fields for get_perspective_view
  ([`2b8b239`](https://github.com/igrybkov/omnifocus-mcp/commit/2b8b239922bb7285bf378058be43a7523dafb211))

- **projects**: Add get_tree tool for hierarchical folder/project/task views
  ([`801c95d`](https://github.com/igrybkov/omnifocus-mcp/commit/801c95d6992d34ba12d9ade0dc11ebe50f7c1808))

- **remove**: Drop items instead of deleting them
  ([`2df0c49`](https://github.com/igrybkov/omnifocus-mcp/commit/2df0c49189cc744c1260f87ee4c558b56977320e))

- **reorder**: Add task reordering and positioning support
  ([`c5218f8`](https://github.com/igrybkov/omnifocus-mcp/commit/c5218f8d41e1188aa6bd2f9f9e3e16b4c0d97eff))

- **scripts**: Add shared JS modules for search and browse
  ([`cb3893d`](https://github.com/igrybkov/omnifocus-mcp/commit/cb3893de3571d55a2b07b73fbebca7e211f61775))

- **search**: Add aggregation and grouping support
  ([`b2da6a2`](https://github.com/igrybkov/omnifocus-mcp/commit/b2da6a26026ab7caba47a23df1fe52445dd6a509))

- **search**: Add item_ids filter for fetching items by ID
  ([`58c71fa`](https://github.com/igrybkov/omnifocus-mcp/commit/58c71fa6ce83ed3a6a6b38a2a10b8b6bd62f49ef))

- **tasks**: Accept item_id as alias for id in edit_item and remove_item
  ([`9b03b8a`](https://github.com/igrybkov/omnifocus-mcp/commit/9b03b8ae15e0ebc90b8a0a7459fb4f65a7ae47c1))

### Refactoring

- Extract inline OmniJS to external script files
  ([`e1fbebe`](https://github.com/igrybkov/omnifocus-mcp/commit/e1fbebeaea431958cb742ec254bec4d4172835ef))

- Rewrite dump_database with OmniJS for better output
  ([`6db75e1`](https://github.com/igrybkov/omnifocus-mcp/commit/6db75e19984b7128c062a13433053b69b42f7379))

- **cli**: Auto-generate commands from registered server tools
  ([`9d7a3e0`](https://github.com/igrybkov/omnifocus-mcp/commit/9d7a3e0bf609d2eaedbb2b9dd695e7ffb44c2ec7))

- **scripts**: Extend shared JS modules for status maps and filters
  ([`969f3a0`](https://github.com/igrybkov/omnifocus-mcp/commit/969f3a03725aa311b6ae7aae13e4e99210ca4635))

- **server**: Replace --expanded flag with env-based tool config
  ([`24ce4e6`](https://github.com/igrybkov/omnifocus-mcp/commit/24ce4e66d3991509be80e3af68cc0dca181991ef))

- **tools**: Rename query_omnifocus to search and get_tree to browse
  ([`9ef61c6`](https://github.com/igrybkov/omnifocus-mcp/commit/9ef61c66191ebe5c2ca131a1b621b101663509f7))

- **tools**: Use shared utilities in all tool implementations
  ([`fc6d431`](https://github.com/igrybkov/omnifocus-mcp/commit/fc6d431991a591abefcfaa83dc3cc3f57d638ab4))

### Testing

- Update tests and documentation for new tools
  ([`6083908`](https://github.com/igrybkov/omnifocus-mcp/commit/6083908c38fb23fff41148b994e9002ce1c2edb4))

- Update tests for renamed search and browse tools
  ([`44d6bc8`](https://github.com/igrybkov/omnifocus-mcp/commit/44d6bc8dd3e7803e570d7e5cc269f1b5ca50ee8b))

- **search**: Add comprehensive aggregation test suite
  ([`bd026f3`](https://github.com/igrybkov/omnifocus-mcp/commit/bd026f3304dcf9f54e6ac67b0935f99cf64cd7c4))
