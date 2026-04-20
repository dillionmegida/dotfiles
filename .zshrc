[ -f ~/zshrc_default ] && source ~/zshrc_default

export ZSH="$HOME/.oh-my-zsh"

#theme
ZSH_THEME="robbyrussell"

source $ZSH/oh-my-zsh.sh

# git aliases
alias g="git"
alias ga="git add"
alias gc="git checkout"
alias gcom="git commit -m"
alias gs="git status"
alias gb="git branch"
alias gps="git push"
alias greb="git rebase"
alias gc="git checkout"
alias gcb="git checkout -b"
alias gst="git stash -u"
alias gstp="git stash pop"
alias gnoedit="git commit --amend --no-edit"

alias nr="npm run"
alias ni="npm install"
alias nid="npm install -D" 
alias nu="npm uninstall"
alias nt="npm test"

alias c="pbcopy"
alias arg="xargs"

alias delete="rm -rf"
alias copy="cp -R"

# custom functions
# git log
function gl {
  if [[ $# -eq 0 ]]; then
    git --no-pager log -1
  else
    git log "$@"
  fi
}

# find files
function ff {
  local search_dir="${1:-.}"
  local filename="${2:-*}"
  local depth="${3}"

  if [[ -z "$depth" ]]; then
    find "$search_dir" -type f -name "${filename}*"
  else
    find "$search_dir" -type f -maxdepth "$depth" -name "${filename}*"
  fi
}

# get a particular line from output
function line {
  local lineno=$1
  sed -n "${lineno}p"
}

# grep with default options
unalias gr
function gr {
  if [[ $# -eq 0 ]]; then
    echo "Usage: gr <pattern> [file...]"
    echo "       ... | gr <pattern>"
    return 1
  elif [[ -t 0 ]]; then
    # No stdin input, use recursive grep
    grep -r -n -i --color=auto "$@"
  else
    # Has stdin input, use regular grep
    grep -n -i --color=auto "$@"
  fi
}


function co {
  # Use the provided argument, or default to the current directory
  local target=$(realpath "${1:-$(pwd)}")

  echo "Opening VSCodium for: $target"
  open "vscodium://file/$target?window=new"
}

# Added by Windsurf
export PATH="$HOME/.codeium/windsurf/bin:$PATH"

function su {
  if (( $+commands[surf] )); then
    surf "$@"
  elif (( $+commands[windsurf] )); then
    windsurf "$@"
  else
    echo "Neither surf nor windsurf found" >&2
    return 1
  fi
}

alias shr="ssh-keygen -R" # remove host from known_hosts
alias sh="ssh"
. "$HOME/.local/bin/env"


# Ghostty shell integration
if [ -n "$GHOSTTY_RESOURCES_DIR" ]; then
  source "$GHOSTTY_RESOURCES_DIR/shell-integration/zsh/ghostty-integration"
fi