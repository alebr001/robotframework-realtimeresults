## Release Process

This repository uses a release-branch–driven workflow with automated version management
and GitHub Releases.

### Branch roles
- **develop**  
  Active development branch.
- **main**  
  Represents the latest released state.
- **feature/\***  
  Short-lived branches for feature development.
- **release/\*** and **hotfix/\***  
  Used to prepare a release and define the version.

---

### Step-by-step release flow

1. Create a feature branch from `develop`
2. Implement the feature and test locally
3. Open a Pull Request to merge the feature branch into `develop`
4. Create a release or hotfix branch from `develop`  
   (`release/x.y.z` or `hotfix/x.y.z`)
5. A GitHub Action automatically updates the version in `pyproject.toml`
   based on the branch name and commits this change
6. Merge the release/hotfix branch into `main`
7. Merge the release/hotfix branch back into `develop`
8. Create a **GitHub Release**, and during this step create a tag
   (`vX.Y.Z`) pointing to `main`
9. The tag triggers the CI pipeline, which builds and publishes the
   package to PyPI


![Gitflow workflow diagram](https://miro.medium.com/v2/resize:fit:550/format:webp/1*9yJY7fyscWFUVRqnx0BM6A.png)

*Source:*  
*Gitflow Workflow – Continuous Integration & Continuous Delivery*  
Originally published on Medium:  
https://medium.com/devsondevs/gitflow-workflow-continuous-integration-continuous-delivery-7f4643abb64f  

*Image hosted by Medium (miro.medium.com). Used for illustrative purposes only.*


---

### Important notes

- Version numbers are derived from the release/hotfix branch name
- GitHub Releases are created from **tags**, not from branches
- The tag always points to a commit on `main`
- `main` always reflects the latest published release
