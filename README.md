# Dotfiles Setup

## On a New Machine

```bash
# Clone this repository
git clone <your-repo-url> <path-to-dotfiles>

# Create symbolic links for all managed files
ln -s <path-to-dotfiles>/.zshrc ~/.zshrc

# Reload your shell configuration
source ~/.zshrc
```

**Optional**: Create a `~/zshrc_default` file with your default zsh configuration.

## Adding New Dotfiles

```bash
# Move the dotfile to this repository
mv ~/.config_file <path-to-dotfiles>/.config_file

# Create the symbolic link
ln -s <path-to-dotfiles>/.config_file ~/.config_file

# Commit the changes
cd <path-to-dotfiles>
git add .config_file
git commit -m "Add .config_file"
git push
```
