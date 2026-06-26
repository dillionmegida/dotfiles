# Absolute directory of this .zshrc (portable across machines)
DOTFILES_DIR="${${(%):-%N}:A:h:h}"

export ZSH="$HOME/.oh-my-zsh"

#theme
ZSH_THEME="robbyrussell"

source $ZSH/oh-my-zsh.sh

# git aliases
alias g="git"
alias ga='python3 "$DOTFILES_DIR/dotfiles/scripts/git/git_add.py"'
alias gr='python3 "$DOTFILES_DIR/dotfiles/scripts/git/git_remove.py"'
alias gs="git status"

alias gb="git branch"
alias gbm="git branch -m"
alias gnb="git --no-pager branch"
alias gbunset="git branch --unset-upstream"

alias gpl="git pull"
alias gps="git push"

alias greb="git rebase"
alias greba="git rebase --abort"
alias grebc="git rebase --continue"

alias gc='python3 "$DOTFILES_DIR/dotfiles/scripts/git/git_checkout.py"'
alias gcb="git checkout -b"
alias gst="git stash -u"
alias gstp="git stash pop"

alias gcom="git commit -m"
alias gamend="git commit --amend"
alias gnoedit="git commit --amend --no-edit"
alias glastcom="git reset --soft HEAD~1"

alias de="decodelogs"

alias nr="npm run"
alias ni="npm install"
alias nid="npm install -D" 
alias nu="npm uninstall"
alias nt="npm test"

alias c="pbcopy"
alias arg="xargs"

alias delete="rm -rf"
alias copy="cp -R"

# Added by Devin
export PATH="/Users/dillion/.codeium/windsurf/bin:$PATH"

alias sshr="ssh-keygen -R" # remove host from known_hosts

# Ghostty shell integration
if [ -n "$GHOSTTY_RESOURCES_DIR" ]; then
  source "$GHOSTTY_RESOURCES_DIR/shell-integration/zsh/ghostty-integration"
fi

# Override oh-my-zsh's SHARE_HISTORY
unsetopt SHARE_HISTORY
setopt APPEND_HISTORY

alias reload="source ~/.zshrc && box 'zshrc reloaded 🔄'"

alias remove-from-history='$DOTFILES_DIR/dotfiles/scripts/remove_from_history.py'

source "$DOTFILES_DIR/dotfiles/functions.zsh"

[[ -z "$DOT_AUTORUN" ]] && export DOT_AUTORUN=1 && dot -q

# ---
# ---
# ---
# ---
# ---
# ---

[ -f ~/.zshrc_default ] && source ~/.zshrc_default
# Added by Devin
export PATH="/Users/dillion/.codeium/windsurf/bin:$PATH"
