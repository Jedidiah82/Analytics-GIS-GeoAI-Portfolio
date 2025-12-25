```mermaid

flowchart LR

&nbsp;   Dev\[Developer Laptop<br/>(VS Code + .NET SDK)]

&nbsp;   GitHub\[GitHub Repository<br/>(Source Code)]

&nbsp;   Actions\[GitHub Actions<br/>CI/CD Pipeline]

&nbsp;   Azure\[Azure Static Web Apps<br/>(HTTPS + CDN)]

&nbsp;   Users\[End Users<br/>(Web Browser)]



&nbsp;   Dev -->|git push| GitHub

&nbsp;   GitHub -->|trigger workflow| Actions

&nbsp;   Actions -->|build \& deploy| Azure

&nbsp;   Users -->|HTTPS access| Azure

```

