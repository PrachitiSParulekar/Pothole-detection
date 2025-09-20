# Contributing to CivicSightAI

1. Fork & clone
2. Create branch: `git checkout -b feature/xyz`
3. Make changes
4. Test
5. Submit PR

Follow PEP 8 & include tests. Questions? Open an issue!

### Code Style

We follow PEP 8 with basic formatting:

- **Line Length**: 88 characters (Black formatter default)
- **Formatting**: Use `black` for code formatting (optional)
- **Linting**: Use `flake8` for linting (optional)

#### Basic Code Formatting Commands (Optional)

```bash
# Format code (if black is installed)
black .

# Lint code (if flake8 is installed)
flake8 .
```

### How to Contribute

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Follow our code style (PEP 8)
4. Write meaningful commit messages
5. Push and create a Pull Request

For detailed guidelines, see our [Wiki](https://github.com/PrachitiSParulekar/Pothole-detection/wiki)
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add nearby complaints endpoint
fix(database): resolve PostGIS connection issue
docs(readme): update installation instructions
test(api): add tests for complaint submission
```

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

#### Writing Tests

- Place test files in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names
- Follow AAA pattern (Arrange, Act, Assert)

Example test:
```python
def test_submit_complaint_success():
    """Test successful complaint submission."""
    # Arrange
    client = app.test_client()
    data = {
        'description': 'Large pothole on Main St',
        'category': 'pothole',
        'location': 'Main Street, City'
    }
    
    # Act
    response = client.post('/submit_complaint', data=data)
    
    # Assert
    assert response.status_code == 200
    assert 'success' in response.get_json()
```

### Database Migrations

When making database schema changes:

1. Create migration scripts in `setup/migrations/`
2. Update `setup_database.py` if needed
3. Test migrations thoroughly
4. Document breaking changes

### AI Model Changes

When modifying AI/ML components:

1. Document model changes in `docs/model_changes.md`
2. Include performance benchmarks
3. Test with various image types
4. Update model file references if needed

## 🔄 Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
   ```bash
   pytest
   ```

2. **Code Quality**: Run basic checks (if tools are installed)
   ```bash
   # Optional formatting and linting
   black . || echo "Black not installed, skipping"
   flake8 . || echo "Flake8 not installed, skipping"
   ```

3. **Documentation**: Update docs if needed

4. **Changelog**: Add entry to `CHANGELOG.md` if applicable

### Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: Manual testing for significant changes
4. **Documentation**: Ensure docs are updated

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Try latest version
3. Check documentation

### Bug Report Template

```markdown
**Describe the Bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Windows 10]
- Python Version: [e.g., 3.11]
- Browser: [e.g., Chrome 91]

**Additional Context**
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature

**Problem Solved**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Mockups, examples, etc.
```

## 📋 Project Areas

### Frontend Development
- **Skills**: HTML, CSS, JavaScript, Mapbox GL JS
- **Files**: `templates/`, `static/`
- **Focus**: UI/UX, responsive design, accessibility

### Backend Development
- **Skills**: Python, Flask, PostgreSQL, PostGIS
- **Files**: `app.py`, `src/`, database modules
- **Focus**: API development, database optimization

### AI/ML Development
- **Skills**: Computer Vision, YOLO, OpenCV, PyTorch
- **Files**: AI processing modules
- **Focus**: Model improvement, accuracy optimization

### DevOps/Infrastructure
- **Skills**: Docker, GitHub Actions, Cloud platforms
- **Files**: `Dockerfile`, `.github/workflows/`
- **Focus**: Deployment, CI/CD, monitoring

### Documentation
- **Skills**: Technical writing, Markdown
- **Files**: `README.md`, `docs/`
- **Focus**: User guides, API documentation

## 🏷️ Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `priority: high`: High priority
- `priority: low`: Low priority
- `area: frontend`: Frontend changes
- `area: backend`: Backend changes
- `area: ai`: AI/ML related
- `area: devops`: Infrastructure/deployment

## 📞 Getting Help

- **Documentation**: Check the [Wiki](https://github.com/yourusername/civicsight-ai/wiki)
- **Issues**: Search existing issues or create new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: For private matters: maintainers@civicsightai.com

## 🎉 Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Given credit in documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Happy Contributing! 🚀**

Thank you for helping make CivicSightAI better for everyone!