# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.0] - 2025-01-XX

### Initial Release

- Initial version of tskr CLI tool
- Basic task management functionality
- Cross-platform binary releases
- GitHub Actions release automation

## [2.0.0] - 2025-01-XX

### Added

- Complete rewrite with modern Python architecture
- Rich CLI interface with beautiful formatting
- Task claiming and collaboration features
- Event logging for coordination
- Natural language date parsing
- Smart tagging system with auto-tags
- Task dependencies and relationships
- Code references and acceptance criteria
- Discussion/comments on tasks
- Project dashboard and statistics
- Urgency calculation algorithm
- Multiple output formats and filtering
- Git integration for author detection
- Comprehensive test suite
- Type safety with Pydantic models

### Changed

- **BREAKING**: Complete API redesign
- **BREAKING**: New storage format (JSONL-based)
- **BREAKING**: New CLI command structure
- Improved performance and reliability
- Better error handling and user feedback

### Removed

- **BREAKING**: Legacy task format compatibility
- **BREAKING**: Old CLI commands and flags

## [1.x.x] - Previous Versions

### Note

Version 1.x.x history is not documented here as this represents a complete rewrite.
The project has been redesigned from the ground up for better usability,
maintainability, and collaboration features.

---

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Release Types

- **🚀 Major Release** (x.0.0): Breaking changes, major new features
- **✨ Minor Release** (x.y.0): New features, backwards compatible
- **🐛 Patch Release** (x.y.z): Bug fixes, backwards compatible
- **🔥 Hotfix** (x.y.z): Critical bug fixes

### Changelog Categories

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

### Breaking Changes

Breaking changes are marked with **BREAKING** and include:

- Migration instructions
- Compatibility notes
- Timeline for removal (for deprecated features)

---

## Migration Guides

### From 1.x to 2.0

Version 2.0 is a complete rewrite. If you're upgrading from 1.x:

1. **Backup your data**: Export your existing tasks
2. **Reinstall**: `pip install --upgrade tskr`
3. **Initialize**: Run `tskr init .` in your project
4. **Import**: Manually recreate important tasks

**Note**: There is no automatic migration path due to the complete architectural change.

---

## Contributing to Changelog

When contributing:

1. **Add entries** to the `[Unreleased]` section
2. **Use proper categories** (Added, Changed, Fixed, etc.)
3. **Write clear descriptions** of changes
4. **Link to issues/PRs** when relevant: `(#123)`
5. **Mark breaking changes** with **BREAKING**

Example entry:

```markdown
### Added
- New `tskr export` command for data backup (#123)

### Fixed
- **BREAKING**: Fixed task ID generation to be more unique (#456)
```
