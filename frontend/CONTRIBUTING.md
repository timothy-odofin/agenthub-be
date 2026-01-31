# Contributing to AgentHub Frontend

Thank you for your interest in contributing to AgentHub! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment (OS, Node.js version, browser)

### Suggesting Features

We welcome feature suggestions! Please create an issue with:
- A clear description of the feature
- The problem it solves
- Possible implementation approach
- Any relevant examples or mockups

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow the existing code style
   - Write clear, descriptive commit messages
   - Add tests if applicable
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   npm install
   npm run lint
   npm run build
   npm run dev
   ```

4. **Submit a pull request** with:
   - A clear title and description
   - Reference to any related issues
   - Screenshots/videos for UI changes

## Development Setup

### Prerequisites
- Node.js 20.19+ or 22.12+
- npm or yarn

### Getting Started
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agenthub-fe.git
cd agenthub-fe

# Install dependencies
npm install

# Start development server
npm run dev
```

### Project Structure
```
src/
├── api/              # API calls and axios configuration
├── components/       # Reusable React components
│   ├── chat/        # Chat-specific components
│   ├── common/      # Common utilities
│   ├── modals/      # Modal components
│   └── ui/          # UI primitives
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── routes/          # Route configuration
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Code Style

### TypeScript
- Use TypeScript for all new code
- Define proper types/interfaces
- Avoid `any` types when possible

### React
- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks

### Styling
- Use Tailwind CSS utility classes
- Follow existing naming conventions
- Ensure responsive design (mobile-first)

### Naming Conventions
- Components: PascalCase (`ChatInput.tsx`)
- Files: camelCase or kebab-case
- Functions: camelCase (`handleSubmit`)
- Constants: UPPER_SNAKE_CASE (`API_BASE_URL`)

## Testing
- Test your changes manually in the browser
- Verify on different screen sizes
- Check console for errors or warnings
- Ensure existing functionality still works

## Documentation
- Update README.md if needed
- Add JSDoc comments for complex functions
- Document new features or breaking changes

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive experience for everyone.

### Our Standards
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior
- Harassment, trolling, or discriminatory comments
- Personal or political attacks
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

## Questions?

Feel free to ask questions by creating an issue or reaching out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
