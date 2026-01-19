# Dotfiles Setup

## On a New Machine

```bash
# Clone this repository to your home directory
git clone <your-repo-url> ~/dotfiles

# Create symbolic links for all managed files
ln -s ~/dotfiles/.zshrc ~/.zshrc

# Reload your shell configuration
source ~/.zshrc
```

**Optional**: Create a `~/zshrc_default` file with your default zsh configuration.

## Adding New Dotfiles

```bash
# Move the dotfile to this repository
mv ~/.config_file ~/dotfiles/.config_file

# Create the symbolic link
ln -s ~/dotfiles/.config_file ~/.config_file

# Commit the changes
cd ~/dotfiles
git add .config_file
git commit -m "Add .config_file"
git push
```
