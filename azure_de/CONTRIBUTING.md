# Contributing Guide

## Development Workflow

### Branching Strategy
- `dev`: Development branch for ongoing work
- `qa`: QA branch for testing
- `main`: Production branch (protected)

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Make Changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/new-feature-name
   # Create PR to dev branch
   ```

5. **Code Review**
   - Address review comments
   - Ensure CI/CD passes

6. **Merge**
   - Merge to dev after approval
   - Deploy to QA for testing
   - Merge to main for production

## Coding Standards

### Python (Airflow, Databricks)
- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions/classes
- Maximum line length: 100 characters

### SQL (Synapse)
- Use consistent naming conventions
- Add comments for complex logic
- Format SQL consistently
- Use parameterized queries

### Terraform
- Use consistent naming
- Add descriptions to variables/outputs
- Format with `terraform fmt`
- Validate with `terraform validate`

## Testing

### Unit Tests
- Write tests for all new functions
- Aim for >80% code coverage
- Run tests before committing

### Integration Tests
- Test end-to-end data flows
- Verify data quality
- Test error handling

## Documentation

### Code Documentation
- Add docstrings to functions
- Comment complex logic
- Update README for major changes

### Architecture Documentation
- Update architecture.md for design changes
- Update runbook.md for operational changes
- Update onboarding-guide.md for new sources

## Pull Request Process

1. **Create PR**
   - Clear title and description
   - Link to related issues
   - Add reviewers

2. **CI/CD Checks**
   - All tests must pass
   - Code must be formatted
   - No linter errors

3. **Code Review**
   - Address all comments
   - Get approval from at least one reviewer

4. **Merge**
   - Squash and merge (preferred)
   - Delete feature branch after merge

## Questions?

Contact the data engineering team:
- Email: data-engineering@company.com
- Slack: #data-engineering

